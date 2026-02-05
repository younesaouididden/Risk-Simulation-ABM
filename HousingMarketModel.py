from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np
# Import des modules locaux (puisque tu as créé des fichiers séparés)
from Household import Household
from Bank import Bank
from CentralBank import CentralBank
from Firm import Firm

# Import des classes précédentes (supposées dans le même fichier ou importées)
# from agents import Household, Bank, CentralBank

class HousingMarketModel(Model):
    """
    Le Modèle Global (L'Environnement).
    Gère le prix du marché, l'offre et la boucle de rétroaction.
    """

    def __init__(self, N_households, N_banks, initial_price=100000):
        super().__init__()
        self.num_agents = N_households
        self.schedule = RandomActivation(self)

        # Paramètres Macro
        self.house_price = initial_price
        self.housing_supply = int(N_households * 0.4)  # Offre fixe: 40% des agents peuvent loger
        self.alpha = 0.05  # Sensibilité du prix (5% d'ajustement max par excès unitaire)

        # Variables dynamiques pour les agents
        self.interest_rate = 0.02  # Initialisé par la BC plus tard
        self.bank_max_dti = 0.33
        self.bank_min_down_payment = 0.20
        self.loan_duration = 20

        # 1. Création de la Banque Centrale
        self.central_bank = CentralBank(999, self)
        self.schedule.add(self.central_bank)

        # 2. Création de la Banque Commerciale (Unique pour simplifier)
        self.bank = Bank(888, self)
        self.schedule.add(self.bank)

        # 3. Création des Ménages
        for i in range(self.num_agents):
            # Au début, tout le monde est chômeur ou on les assigne aléatoirement
            # Pour faire simple : Chômeur avec une épargne initiale
            wealth = np.random.uniform(10000, 50000)

            # Note: Income mis à 0 initialement, l'entreprise les embauchera au tour 1
            a = Household(i, self, income=0, initial_wealth=wealth, savings_rate=0.2)
            self.schedule.add(a)

        self.firms = []
        for i in range(5):  # 5 Grosses Entreprises
            unique_id = 500 + i
            # On donne un ID et un salaire moyen de 2000
            f = Firm(unique_id, self, wage=2000)
            self.schedule.add(f)
            self.firms.append(f)

        all_households = [a for a in self.schedule.agents if isinstance(a, Household)]

        # On mélange les agents pour ne pas prendre que les premiers
        self.random.shuffle(all_households)

        # On définit combien de gens travaillent au jour 0 (ex: 850 sur 1000)
        num_workers = int(self.num_agents * 0.85)

        for i in range(num_workers):
            worker = all_households[i]
            # On choisit une entreprise au hasard
            employer = self.random.choice(self.firms)

            # On effectue l'embauche manuelle (Force hiring)
            worker.get_job(employer)
            employer.employees.append(worker)

        # 4. Collecteur de Données (Module 5 intégré)
        self.datacollector = DataCollector(
            model_reporters={
                "Price": "house_price",
                "Interest Rate": "interest_rate",
                # Calcul du Taux de Chômage en temps réel
                "Unemployment": lambda m: sum(
                    [1 for a in m.schedule.agents if isinstance(a, Household) and a.employer is None]) / m.num_agents,
                # Volume de crédit (Indicateur de gel du marché)
                "Credit Volume": lambda m: m.bank.loans_granted
            }
        )

    def step(self):
        """
        Une étape de simulation (1 mois).
        """
        # Reset des compteurs de la banque pour ce tour
        self.bank.loans_granted = 0

        # 1. Tous les agents agissent (Revenu, Décision, Politique Monétaire)
        self.schedule.step()

        # 2. Mise à jour du taux du modèle depuis la Banque (Transmission)
        # La BC change le taux de la bank -> Le modèle le lit pour les calculs des ménages
        self.interest_rate = self.bank.interest_rate

        # 3. Mécanisme de Marché (Clearing)
        self.update_market_price()

        # 4. Enregistrement des données
        self.datacollector.collect(self)

    def update_market_price(self):
        """
        Loi de l'Offre et la Demande (Version Crash Systémique).
        """
        demand_count = 0

        # 1. CALCUL DE LA DEMANDE (D)
        for agent in self.schedule.agents:
            # On ne s'intéresse qu'aux Ménages Locataires qui veulent acheter
            # (Note: On utilise le nom de la classe en string pour éviter les erreurs d'import si nécessaire)
            if type(agent).__name__ == 'Household' and not agent.is_owner:

                # L'agent décide de sa stratégie (Mentir ou pas ?)
                declared_income, is_fraudster = agent.decide_application_strategy(self.house_price)

                # Il soumet son dossier à la Banque
                loan_approved = self.bank.evaluate_loan_application(
                    agent,
                    self.house_price,
                    declared_income
                )

                # Si la Banque dit OUI, c'est une demande effective
                if loan_approved:
                    demand_count += 1

        # 2. RÉCUPÉRATION DE L'OFFRE (S)
        # C'est ici que le Krach se joue : 'housing_supply' augmente à chaque saisie de la Banque !
        supply = self.housing_supply

        # Sécurité anti-crash numérique (division par zéro)
        if supply <= 0: supply = 1

        # 3. CALCUL DU GAP (Pression sur les prix)
        # Formule : (D - S) / S
        # Exemple Krach : Demande=5 (ruinés), Offre=500 (saisies) -> (5 - 500)/500 = -0.99
        excess_demand = (demand_count - supply) / supply

        # 4. MISE À JOUR DU PRIX
        # On applique le facteur d'ajustement (alpha)
        # Si excess_demand est très négatif (ex: -0.99), le prix va chuter violemment.
        self.house_price = self.house_price * (1 + self.alpha * excess_demand)

        # Plancher à 0 (Le prix ne peut pas être négatif)
        if self.house_price < 0:
            self.house_price = 0

        # Debug print optionnel pour voir le massacre en direct dans la console
        # print(f"T={self.schedule.steps} | Prix={self.house_price:.0f} | D={demand_count} vs S={supply} | Gap={excess_demand:.2f}")