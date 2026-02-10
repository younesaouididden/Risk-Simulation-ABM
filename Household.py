from mesa import Agent


class Household(Agent):
    def __init__(self, unique_id, model, market_value, initial_wealth, savings_rate):
        super().__init__(unique_id, model)
        self.market_value = market_value # Ma "compétence" (salaire potentiel)
        self.income = 0                  # Mon salaire actuel (0 si chômage)
        self.wealth = initial_wealth
        self.savings_rate = savings_rate
        self.employer = None
        self.is_owner = False
        self.mortgage_payment = 0
        # Paramètres psychologiques
        self.perceived_audit_prob = 0.05
        self.utility_house = 100
        self.penalty_caught = 500

    def step(self):
        # Épargne simple (si revenu > 0)
        if self.income > 0:
            self.wealth += self.income * self.savings_rate

    def get_job(self, firm):
        self.employer = firm
        # Je suis payé à ma juste valeur
        self.income = self.market_value

    def lose_job(self):
        self.employer = None
        self.income = 0

    def can_pay_mortgage(self, monthly_payment):
        # RÈGLE IMPITOYABLE : Pas de salaire = Défaut immédiat
        # On ne tape pas dans l'épargne pour payer la banque
        if self.income < monthly_payment:
            return False
        return True

    def decide_application_strategy(self, property_price):
        """ Retourne (Revenu_Déclaré, Est_Fraudeur) """
        interest_rate = self.model.interest_rate
        duration = self.model.loan_duration
        max_dti = self.model.bank_max_dti

        loan_needed = property_price - self.wealth
        if loan_needed <= 0: return self.income, False

        # Calcul PMT interne
        r = interest_rate / 12
        n = duration * 12
        pmt = loan_needed * (r / (1 - (1 + r) ** (-n)))

        required_income = pmt / max_dti

        if self.income >= required_income:
            return self.income, False
        else:
            # Calcul Utilité Espérée de la Fraude
            p = self.perceived_audit_prob
            eu_fraud = (1 - p) * self.utility_house - p * self.penalty_caught

            if eu_fraud > 0:
                return required_income + 1, True  # FRAUDE
            else:
                return self.income, False