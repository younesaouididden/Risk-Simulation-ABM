from mesa import Agent
import math


class Firm(Agent):
    def __init__(self, unique_id, model, wage=0, debt=0, margin=1.5, initial_employees=None):
        super().__init__(unique_id, model)
        # self.wage n'est plus utilisé comme fixe, mais comme indicateur ou 0
        self.employees = [] if initial_employees is None else initial_employees
        self.cash_on_hand = 100000
        self.revenue = 0
        self.debt = debt
        self.margin_target = margin

    def step(self):
        # 1. Calcul de la Masse Salariale Réelle
        wage_bill = sum([e.market_value for e in self.employees])

        # 2. Calcul du Chiffre d'Affaires (Productivité)
        # Hypothèse : L'entreprise facture 'margin_target' fois le coût de ses employés
        # (Modèle société de conseil / services)
        self.revenue = wage_bill * self.margin_target

        # 3. Calcul du Profit
        interest_payment = self.debt * self.model.interest_rate
        profit = self.revenue - wage_bill - interest_payment
        self.cash_on_hand += profit

        # 4. Gestion Embauche/Licenciement
        if profit < 0:
            self.fire_staff(abs(profit))
        elif profit > 0 and self.model.random.random() < 0.1:
            self.hire_staff()

    def fire_staff(self, deficit):
        # On vire les gens pour couvrir le déficit.
        # Stratégie : On vire au hasard (ou les plus chers ?) -> Hasard pour l'instant
        if not self.employees: return

        # On estime un salaire moyen pour savoir combien de têtes couper
        avg_wage = sum([e.market_value for e in self.employees]) / len(self.employees)
        if avg_wage == 0: return

        nb_to_fire = math.ceil(deficit / avg_wage)
        nb_to_fire = min(nb_to_fire, len(self.employees))

        if nb_to_fire > 0:
            fired_employees = self.model.random.sample(self.employees, int(nb_to_fire))
            for household in fired_employees:
                household.lose_job()
                self.employees.remove(household)

    def hire_staff(self):
        potential_hires = [
            agent for agent in self.model.schedule.agents
            if type(agent).__name__ == 'Household' and agent.employer is None
        ]
        if potential_hires:
            # L'entreprise embauche un profil disponible
            new_employee = self.model.random.choice(potential_hires)
            new_employee.get_job(self)
            self.employees.append(new_employee)