from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from Household import Household
from Bank import Bank
from Firm import Firm
import numpy as np
from scipy.special import erfinv


class HousingMarketModel(Model):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.num_agents = config["N_households"]
        self.schedule = RandomActivation(self)

        # --- PARAMÈTRES MACRO ---
        self.house_price = 100000
        self.interest_rate = config["base_rate"]
        self.bank_max_dti = 0.33
        self.loan_duration = 20
        self.alpha = 0.10  # On réduit un peu la volatilité
        self.housing_supply = config["init_supply"]
        self.deals_this_step = 0

        # --- REVENUS : DISTRIBUTION NORMALE (HÉTÉROGÈNE) ---
        is_sandbox = config.get("enable_inequality", False)
        if is_sandbox:
            incomes = self.generate_lognormal_income(
                n=self.num_agents,
                mean_income=config["mean_income"],
                gini=config["gini_index"],
                min_wage=config["min_wage"]
            )
        else:
            # On garde la distribution Normale qui marchait bien pour la diversité
            # Moyenne 4000, mais avec des riches et des pauvres
            incomes = np.random.normal(loc=4000, scale=800, size=self.num_agents)
            incomes = np.maximum(incomes, 2500)  # SMIG

        # Agents
        self.bank = Bank(9999, self)
        self.bank.audit_probability = config["audit_prob"]
        self.schedule.add(self.bank)

        self.firms = []
        for i in range(5):
            unique_id = 500 + i
            f = Firm(unique_id, self, wage=0,
                     debt=config["firm_debt"],
                     margin=config["firm_margin"])
            self.schedule.add(f)
            self.firms.append(f)

        for i in range(self.num_agents):
            market_value = incomes[i]
            # Richesse liée au salaire (plus réaliste)
            wealth = market_value * np.random.uniform(5, 15)

            a = Household(i, self,
                          market_value=market_value,
                          initial_wealth=wealth,
                          savings_rate=0.2)
            self.schedule.add(a)

        # Marché du Travail
        all_households = [a for a in self.schedule.agents if isinstance(a, Household)]
        self.random.shuffle(all_households)
        num_workers = int(self.num_agents * 0.90)
        for i in range(num_workers):
            worker = all_households[i]
            employer = self.random.choice(self.firms)
            worker.get_job(employer)
            employer.employees.append(worker)

        # DataCollector
        self.datacollector = DataCollector(
            model_reporters={
                "Price": "house_price",
                "Interest Rate": "interest_rate",
                "Unemployment": lambda m: sum([1 for a in m.schedule.agents if
                                               type(a).__name__ == 'Household' and a.employer is None]) / m.num_agents,
                "Housing Supply": "housing_supply",
                "Deals Count": "deals_this_step",
                "Foreclosures": lambda m: m.bank.foreclosures_count,
                "Mean Wealth": lambda m: np.mean(
                    [a.wealth for a in m.schedule.agents if type(a).__name__ == 'Household']),
                "Wealth Gini": self.compute_gini
            }
        )

    def step(self):
        previous_deals = self.deals_this_step
        self.deals_this_step = 0

        if self.schedule.steps == self.config["shock_step"]:
            self.interest_rate = self.config["shock_rate"]
            print(f"!!! CHOC : {self.config['base_rate']} -> {self.config['shock_rate']} !!!")

        # 1. TURNOVER (Classique)
        households = [a for a in self.schedule.agents if type(a).__name__ == 'Household']
        unemployed = [a for a in households if a.employer is None]
        unemployment_rate = len(unemployed) / len(households)

        # Plus de ventes si l'économie va bien (confiance), moins si crise (peur)
        turnover_prob = 0.015 if unemployment_rate < 0.10 else 0.005

        for agent in households:
            if agent.is_owner and self.random.random() < turnover_prob:
                agent.is_owner = False
                agent.mortgage_payment = 0
                self.housing_supply += 1

                # 2. CONSTRUCTION
        # Les constructeurs ne construisent que si le prix monte ou se maintient
        # et s'il y a un minimum de ventes.
        target_supply = int(self.num_agents * 0.10)
        market_is_active = (previous_deals > 0)

        if self.housing_supply < target_supply and market_is_active:
            new_houses = 5  # Production prudente et constante
            self.housing_supply += new_houses

        self.schedule.step()
        self.update_market_price()
        self.datacollector.collect(self)

    def update_market_price(self):
        potential_buyers = []

        # --- C'EST ICI QUE TOUT SE JOUE : LE FILTRE RATIONNEL ---
        for agent in self.schedule.agents:
            if type(agent).__name__ == 'Household' and not agent.is_owner:

                # 1. Check Banque (Capacité)
                declared, fraud = agent.decide_application_strategy(self.house_price)
                bank_says_yes = self.bank.evaluate_loan_application(agent, self.house_price, declared)

                # 2. Check Rationalité (Volonté)
                # Un ménage n'achète pas si le prix dépasse 6 années de son revenu (Ratio PTI)
                # C'est la limite "Bulle"
                if agent.income > 0:
                    max_rational_price = agent.income * 12 * 6
                else:
                    max_rational_price = 0

                buyer_is_rational = (self.house_price <= max_rational_price)

                if bank_says_yes and buyer_is_rational:
                    potential_buyers.append(agent)

        # Calcul Pression
        demand = len(potential_buyers)
        supply = self.housing_supply

        # Formule Z-Score pondérée
        excess_demand = (demand - supply) / self.num_agents

        # Asymétrie Panique
        if excess_demand > 0:
            adjustment = 0.10 * excess_demand  # Hausse douce
        else:
            adjustment = 0.40 * excess_demand  # Baisse violente (Krach)

        self.house_price = self.house_price * (1 + adjustment)
        if self.house_price < 0: self.house_price = 0

        # Transactions
        self.random.shuffle(potential_buyers)
        while self.housing_supply > 0 and len(potential_buyers) > 0:
            buyer = potential_buyers.pop()
            buyer.is_owner = True
            self.housing_supply -= 1
            loan = self.house_price * (1 - self.bank.min_down_payment)
            buyer.mortgage_payment = self.bank.calculate_pmt(loan)
            self.deals_this_step += 1

    @staticmethod
    def generate_lognormal_income(n, mean_income, gini, min_wage):
        if gini < 1e-9: gini = 1e-9
        sigma = 2 * erfinv(gini)
        mu = np.log(mean_income) - (sigma ** 2) / 2
        inc = np.random.lognormal(mean=mu, sigma=sigma, size=n)
        return np.maximum(inc, min_wage)

    @staticmethod
    def compute_gini(model):
        wealths = sorted([a.wealth for a in model.schedule.agents if type(a).__name__ == 'Household'])
        if not wealths or sum(wealths) == 0: return 0
        n = len(wealths)
        idx = np.arange(1, n + 1)
        return ((2 * idx - n - 1) * wealths).sum() / (n * sum(wealths))