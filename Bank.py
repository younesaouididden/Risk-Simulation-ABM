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
        self.audit_probability = 0.10  # La banque vérifie 1 dossier sur 10
        self.audit_cost = 100  # Coût de l'audit

        # Statistiques internes
        self.loans_granted = 0
        self.total_loans_volume = 0

    def step(self):
        self.process_foreclosures()

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

    def evaluate_loan_application(self, applicant, property_price, declared_income):
        """
        Évalue le dossier.
        NEW : Accepte 'declared_income' et peut auditer pour vérifier la fraude.
        """

        # 1. Vérification de l'Apport (LTV)
        # On suppose qu'on ne peut pas mentir sur le Cash (c'est sur le compte)
        down_payment = applicant.wealth
        if (down_payment / property_price) < self.min_down_payment:
            return False

        # 2. STRATÉGIE D'AUDIT (Le Gendarme)
        # La banque lance un dé pour décider si elle vérifie ce dossier spécifique
        is_audited = self.model.random.random() < self.audit_probability

        if is_audited:
            # L'Audit a lieu : La banque regarde le VRAI revenu (applicant.income)
            # On compare avec une tolérance minime (pour les erreurs d'arrondi)
            if abs(applicant.income - declared_income) > 1.0:
                # FRAUDE DÉTECTÉE !
                # print(f"BANQUE : Fraude détectée pour l'agent {applicant.unique_id} ! Refusé.")
                # Ici, on pourrait ajouter une pénalité (blacklist)
                return False
            else:
                # Audit passé avec succès (Dossier honnête)
                # La banque paie le coût de l'audit (réduit son profit - à implémenter plus tard)
                pass

        # 3. Vérification de la Solvabilité (DTI)
        # ATTENTION : La banque utilise le DECLARED_INCOME pour ce calcul !
        # Si l'agent a menti et n'a pas été audité, il passe cette étape avec son faux revenu.

        loan_amount = property_price - down_payment
        if loan_amount <= 0: return True

        monthly_payment = self.calculate_pmt(loan_amount)

        # Calcul du DTI basé sur la déclaration
        max_allowed_payment = declared_income * self.max_dti

        if monthly_payment > max_allowed_payment:
            return False

        # Si on arrive ici, le prêt est accordé (soit honnêtement, soit par fraude non détectée)
        self.loans_granted += 1
        self.total_loans_volume += loan_amount
        return True

    def process_foreclosures(self):
        """
        La Banque saisit les biens des agents en défaut.
        """
        # On itère sur une copie de la liste des emprunteurs (car on va en supprimer)
        # Note: Il faudrait que la banque tienne une liste 'self.borrowers'.
        # Pour simplifier ici, on scanne tout le monde (pas optimal mais fonctionnel pour 1000 agents)

        for agent in self.model.schedule.agents:
            # On cherche les propriétaires qui ont un crédit chez nous
            # (Simplification: on suppose que tout proprio a un crédit en cours pour l'exercice)
            if type(agent).__name__ == 'Household' and agent.is_owner:

                # Recalcul de la mensualité théorique (approx)
                # On suppose un prêt moyen basé sur le prix actuel
                estimated_loan = self.model.house_price * (1 - self.min_down_payment)
                pmt = self.calculate_pmt(estimated_loan)

                # Vérification du paiement
                if not agent.can_pay_mortgage(pmt):
                    # DÉFAUT -> SAISIE !
                    self.foreclose(agent)

    def foreclose(self, agent):
        """Exécution de la saisie immobilière."""
        # 1. Le ménage perd son statut de propriétaire
        agent.is_owner = False
        agent.property_value = 0

        # 2. SANCTION FINANCIÈRE (Le "Game Over" pour l'agent)
        # La banque saisit tout le cash restant pour couvrir les pertes du prêt non remboursé.
        # Sans cela, l'agent utilise ce cash pour racheter une maison au tour suivant !
        agent.wealth = 0

        # 3. IMPACT SUR L'OFFRE
        # La banque remet la maison sur le marché
        self.model.housing_supply += 1