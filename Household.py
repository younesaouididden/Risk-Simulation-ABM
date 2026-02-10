from mesa import Agent
import numpy as np

class Household(Agent):
    def __init__(self, unique_id, model, market_value, initial_wealth, savings_rate):
        super().__init__(unique_id, model)
        self.market_value = market_value
        self.income = 0
        self.wealth = initial_wealth
        self.savings_rate = savings_rate
        self.employer = None
        self.is_owner = False
        self.mortgage_payment = 0

    def step(self):
        # 1. Revenus
        if self.employer is not None:
            self.income = self.market_value
            savings = self.income * self.savings_rate
            self.wealth += savings
        else:
            self.income = 0
            # CORRECTION : Le coût de la vie dépend du standard de vie (50% du salaire de marché)
            # Avant c'était 1000 fixe (trop faible), maintenant c'est ~2000
            living_cost = self.market_value * 0.50
            self.wealth -= living_cost

        # 2. "Accidents de la Vie" (Nouveau !)
        # Même avec un emploi, on peut avoir une tuile (voiture, santé...)
        # 2% de chance par mois de perdre 5000 MAD
        if self.model.random.random() < 0.02:
            self.wealth -= 5000

        # Sécurité (pas de richesse négative, mais dette possible)
        if self.wealth < 0: self.wealth = 0

        # 3. Paiement Crédit
        if self.is_owner and self.mortgage_payment > 0:
            if self.can_pay_mortgage(self.mortgage_payment):
                self.wealth -= self.mortgage_payment
            else:
                # La banque détectera le défaut
                pass

    def get_job(self, firm):
        self.employer = firm
        self.income = self.market_value

    def lose_job(self):
        self.employer = None
        self.income = 0

    def can_pay_mortgage(self, amount):
        # On peut payer si : Salaire suffisant OU Épargne suffisante
        return (self.income >= amount) or (self.wealth >= amount)

    def decide_application_strategy(self, house_price):
        is_fraudster = False
        declared_income = self.income
        if self.model.random.random() < 0.10:
            is_fraudster = True
            declared_income = self.income * 1.20
        return declared_income, is_fraudster