import numpy as np
from mesa import Agent


class Bank(Agent):
    """
    Agent Banque.
    Rôle : Évaluer les demandes de crédit et gérer le risque.
    """

    def __init__(self, unique_id, model, min_down_payment=0.20, max_dti=0.33, interest_rate=0.045, loan_duration=20):
        super().__init__(unique_id, model)
        self.min_down_payment = min_down_payment  # Ex: 20% d'apport requis
        self.max_dti = max_dti  # Ex: Max 33% du revenu en mensualité
        self.interest_rate = interest_rate  # Taux annuel
        self.loan_duration = loan_duration  # En années

        # Statistiques internes
        self.loans_granted = 0
        self.total_loans_volume = 0

    def step(self):
        # La banque est passive dans ce modèle : elle réagit aux demandes.
        # Elle pourrait ajuster ses taux ici en fonction de la demande (optionnel pour l'instant).
        pass

    def evaluate_loan_application(self, applicant, property_price):
        """
        Évalue si un ménage (applicant) peut acheter un bien à 'property_price'.
        Retourne : True (Accordé) ou False (Refusé)
        """

        # 1. Vérification de l'Apport Personnel (Liquidité / LTV check)
        # Le ménage utilise toute son épargne pour réduire le prêt (Hypothèse simplificatrice)
        down_payment = applicant.wealth

        # Calcul du ratio d'apport réel
        down_payment_ratio = down_payment / property_price

        # Si l'apport est inférieur au minimum requis (ex: < 20%), REFUS IMMÉDIAT.
        if down_payment_ratio < self.min_down_payment:
            return False

        # 2. Vérification de la Solvabilité (Revenu / DTI check)
        loan_amount = property_price - down_payment

        # Si le ménage paie cash (loan_amount <= 0), pas besoin de crédit -> Accordé
        if loan_amount <= 0:
            return True

        # Calcul de la mensualité théorique du crédit
        monthly_payment = self.calculate_pmt(loan_amount)

        # Capacité maximale de remboursement du ménage
        max_allowed_payment = applicant.income * self.max_dti

        # Si la mensualité dépasse la capacité -> REFUS
        if monthly_payment > max_allowed_payment:
            return False

        # Si on arrive ici, tout est vert.
        self.loans_granted += 1
        self.total_loans_volume += loan_amount
        return True

    def calculate_pmt(self, principal):
        """
        Calcule la mensualité d'un prêt amortissable (formule standard).
        """
        r_monthly = self.interest_rate / 12
        n_months = self.loan_duration * 12

        if r_monthly == 0:
            return principal / n_months

        # PMT = P * (r / (1 - (1+r)^-n))
        payment = principal * (r_monthly / (1 - (1 + r_monthly) ** (-n_months)))
        return payment