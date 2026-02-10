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

        # Paramètres Macro
        self.house_price = 100000
        self.interest_rate = config["base_rate"]
        self.housing_supply = config["init_supply"]
        self.deals_this_step = 0
        self.loan_duration = 20
        self.bank_max_dti = 0.33

        # Revenus
        is_sandbox = config.get("enable_inequality", False)
        if is_sandbox:
            incomes = self.generate_lognormal_income(
                n=self.num_agents,
                mean_income=config["mean_income"],
                gini=config["gini_index"],
                min_wage=config["min_wage"]
            )
        else:
            incomes = np.random.normal(loc=4000, scale=800, size=self.num_agents)
            incomes = np.maximum(incomes, 2500)

        # 1. Banque
        self.bank = Bank(9999, self)
        self.bank.audit_probability = config["audit_prob"]
        self.schedule.add(self.bank)

        # 2. Entreprises
        self.firms = []
        for i in range(5):
            unique_id = 500 + i
            f = Firm(unique_id, self, wage=0,
                     debt=config["firm_debt"],
                     margin=config["firm_margin"])
            self.schedule.add(f)
            self.firms.append(f)

        # 3. Ménages
        for i in range(self.num_agents):
            market_value = incomes[i]
            # Richesse fragile (4 à 8 mois) pour permettre le risque de faillite
            wealth = market_value * np.random.uniform(4, 8)
            a = Household(i, self, market_value, wealth, savings_rate=0.2)
            self.schedule.add(a)

        # 4. Emploi Initial (C'EST ICI QUE C'ÉTAIT CASSÉ)
        all_households = [a for a in self.schedule.agents if isinstance(a, Household)]
        self.random.shuffle(all_households)
        num_workers = int(self.num_agents * 0.90)

        for i in range(num_workers):
            worker = all_households[i]
            employer = self.random.choice(self.firms)

            # 1. Le travailleur sait qui est son patron
            worker.get_job(employer)

            # 2. IMPÉRATIF : Le patron doit inscrire le travailleur sur sa liste !
            # Sans ça, il ne peut pas le licencier en cas de faillite.
            employer.employees.append(worker)

        # 5. DataCollector
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
        self.deals_this_step = 0
        if self.schedule.steps == self.config["shock_step"]:
            self.interest_rate = self.config["shock_rate"]
            print(f"!!! CHOC : {self.config['base_rate']} -> {self.config['shock_rate']} !!!")

        # Turnover
        for agent in self.schedule.agents:
            if type(agent).__name__ == 'Household' and agent.is_owner:
                if self.random.random() < 0.01:
                    agent.is_owner = False
                    agent.mortgage_payment = 0
                    self.housing_supply += 1

        # Construction
        if self.housing_supply < 50:
            self.housing_supply += 5

        self.schedule.step()
        self.update_market_price()
        self.datacollector.collect(self)

    def update_market_price(self):
        potential_buyers = []
        for agent in self.schedule.agents:
            if type(agent).__name__ == 'Household' and not agent.is_owner:
                declared, _ = agent.decide_application_strategy(self.house_price)
                if self.bank.evaluate_loan_application(agent, self.house_price, declared):
                    potential_buyers.append(agent)

        demand = len(potential_buyers)
        supply = self.housing_supply
        if supply == 0: supply = 1

        excess_demand = (demand - supply) / self.num_agents
        self.house_price = self.house_price * (1 + 0.10 * excess_demand)
        if self.house_price < 50000: self.house_price = 50000

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