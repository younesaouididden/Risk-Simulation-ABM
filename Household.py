import numpy as np
from mesa import Agent


class Household(Agent):
    """
    Agent Ménage.
    Attributs:
        unique_id: ID unique de l'agent
        model: Référence au modèle global
        income: Revenu mensuel (Y)
        wealth: Épargne accumulée (W) / Apport personnel
        savings_rate: Propension à épargner (ex: 0.20)
    """

    def __init__(self, unique_id, model, income, initial_wealth, savings_rate):
        super().__init__(unique_id, model)
        self.income = income
        self.wealth = initial_wealth
        self.savings_rate = savings_rate
        self.is_owner = False  # Statut : Locataire par défaut
        self.property_value = 0  # 0 si locataire

    def step(self):
        """
        Action à chaque pas de temps (supposé être 1 mois).
        1. Recevoir revenu
        2. Consommer et Épargner
        3. Si locataire, évaluer capacité d'achat
        """
        # 1. & 2. Gestion du budget (Flux -> Stock)
        monthly_savings = self.income * self.savings_rate
        self.wealth += monthly_savings  # Accumulation de l'apport

        # 3. Décision Immobilière (Si locataire)
        if not self.is_owner:
            max_budget = self.calculate_purchasing_power()
            # Logique future: Chercher une maison sur le marché < max_budget
            # Pour l'instant, on print juste la capacité pour vérifier
            # print(f"Agent {self.unique_id} peut acheter jusqu'à: {max_budget:.2f}")

    def calculate_purchasing_power(self):
        """
        Calcule le prix maximum que le ménage peut payer (P_max).
        P_max = Apport (Wealth) + Dette Max (L_max)
        """
        # Récupération des paramètres macro du modèle (Banque/Marché)
        # Note: self.model devra avoir ces attributs
        interest_rate_yearly = self.model.interest_rate
        max_dti = self.model.bank_max_dti  # Ex: 0.33
        loan_duration_years = self.model.loan_duration  # Ex: 20 ans

        # Conversion mensuelle
        r_monthly = interest_rate_yearly / 12
        n_months = loan_duration_years * 12

        # 1. Calcul de la mensualité maximale tolérée (Critère DTI)
        max_monthly_payment = self.income * max_dti

        # 2. Calcul du Capital Empruntable (Formule des annuités)
        # PV = PMT * [ (1 - (1+r)^-n) / r ]
        if r_monthly > 0:
            max_loan = max_monthly_payment * (1 - (1 + r_monthly) ** (-n_months)) / r_monthly
        else:
            max_loan = max_monthly_payment * n_months

        # 3. Budget Total
        # Le budget est l'apport + le crédit, MAIS...
        # Il y a une subtilité : la banque demande souvent un apport MINIMUM (ex: 20% du prix).
        # Prix = Apport + Crédit.
        # Si Apport doit être >= 20% du Prix, alors Prix_max = Apport / 0.20
        # Le vrai budget est le MINIMUM entre (Apport + Crédit Max) et (Apport / Min_Down_Payment_Ratio)

        purchasing_power_financial = self.wealth + max_loan

        # Ajout de la contrainte LTV (Loan-To-Value) inverse
        # Si la banque exige 20% d'apport : P_max_regulatory = Wealth / 0.20
        min_down_payment_ratio = self.model.bank_min_down_payment  # Ex: 0.20

        if min_down_payment_ratio > 0:
            purchasing_power_regulatory = self.wealth / min_down_payment_ratio
            final_budget = min(purchasing_power_financial, purchasing_power_regulatory)
        else:
            final_budget = purchasing_power_financial

        return final_budget

def lose_job(self):
    self.income = 0  # Choc brutal de revenu
    # Optionnel : self.income = self.model.unemployment_benefit