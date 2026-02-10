from mesa import Agent
import numpy as np


class Bank(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.min_down_payment = 0.20
        self.max_dti = 0.33
        self.loans_granted = 0
        self.audit_probability = 0.10  # Sera écrasé par le modèle si config différente
        self.foreclosures_count = 0  # Compteur pour les stats

    def step(self):
        self.process_foreclosures()

    def calculate_pmt(self, principal):
        rate = self.model.interest_rate
        years = self.model.loan_duration
        r_monthly = rate / 12
        n_months = years * 12
        if r_monthly == 0: return principal / n_months
        return principal * (r_monthly / (1 - (1 + r_monthly) ** (-n_months)))

    def evaluate_loan_application(self, applicant, property_price, declared_income):
        # 1. Vérif Apport
        down_payment = applicant.wealth
        if (down_payment / property_price) < self.min_down_payment:
            return False

        # 2. Audit (Game Theory)
        is_audited = self.model.random.random() < self.audit_probability
        if is_audited:
            if abs(applicant.income - declared_income) > 1.0:
                return False  # Fraude détectée

        # 3. Solvabilité (DTI sur revenu déclaré)
        loan_amount = property_price - down_payment
        monthly_payment = self.calculate_pmt(loan_amount)
        if monthly_payment > (declared_income * self.max_dti):
            return False

        return True

    def process_foreclosures(self):
        for agent in self.model.schedule.agents:
            if type(agent).__name__ == 'Household' and agent.is_owner:

                # --- CORRECTIF ---
                # On utilise la VRAIE mensualité signée au moment de l'achat
                # (Plus de recalcule basé sur le prix actuel du marché)
                pmt = agent.mortgage_payment

                if not agent.can_pay_mortgage(pmt):
                    self.foreclose(agent)

    def foreclose(self, agent):
        # 1. Perte du titre
        agent.is_owner = False
        # 2. Ruine financière
        agent.wealth = 0
        # 3. Choc d'Offre
        self.model.housing_supply += 1
        # 4. Statistique
        self.foreclosures_count += 1

    def get_max_borrowing_capacity(self, monthly_income):
        """
        Calcule combien un ménage peut emprunter au maximum avec ce revenu.
        Inverse de la formule PMT.
        """
        max_monthly_payment = monthly_income * self.max_dti
        rate = self.model.interest_rate
        years = self.model.loan_duration
        r_monthly = rate / 12
        n_months = years * 12

        if r_monthly == 0: return max_monthly_payment * n_months

        # Formule inversée des annuités
        # PV = PMT * [(1 - (1+r)^-n) / r]
        max_principal = max_monthly_payment * ((1 - (1 + r_monthly) ** (-n_months)) / r_monthly)
        return max_principal