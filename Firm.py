from mesa import Agent


class Firm(Agent):
    def __init__(self, unique_id, model, wage=0, debt=0, margin=1.20):
        super().__init__(unique_id, model)
        self.wage = wage
        self.debt = debt
        self.margin = margin

        # AJUSTEMENT DE SÉCURITÉ
        self.cash_on_hand = 200000  # Assez pour survivre aux premiers mois
        self.employees = []

    def step(self):
        # 1. Calculs
        if len(self.employees) > 0:
            wage_bill = sum([e.market_value for e in self.employees])
        else:
            wage_bill = 0

        monthly_interest = (self.debt * self.model.interest_rate) / 12
        total_costs = wage_bill + monthly_interest
        revenue = wage_bill * self.margin
        profit = revenue - total_costs

        self.cash_on_hand += profit

        # 2. Gestion Faillite (Rigoriste)
        if self.cash_on_hand < 0:
            self.fire_everyone()
            # PUNITION : Pas de cadeau. La caisse reste à 0.
            # L'entreprise est morte cliniquement.
            self.cash_on_hand = 0

    def fire_everyone(self):
        for worker in self.employees:
            worker.lose_job()
        self.employees = []