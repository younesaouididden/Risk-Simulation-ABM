from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np
# Import des modules locaux (puisque tu as créé des fichiers séparés)
from Household import Household
from Bank import Bank
from CentralBank import CentralBank

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
            # Revenu log-normal (pour créer des riches et des pauvres)
            income = np.random.lognormal(mean=9, sigma=0.5)  # ~8000 +/- variabilité
            wealth = np.random.uniform(10000, 50000)  # Apport initial

            a = Household(i, self, income, wealth, savings_rate=0.2)
            self.schedule.add(a)

        # 4. Collecteur de Données (Module 5 intégré)
        self.datacollector = DataCollector(
            model_reporters={
                "Price": "house_price",
                "Interest Rate": "interest_rate",
                "Transactions": lambda m: m.bank.loans_granted
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
        Loi de l'Offre et la Demande.
        """
        demand_count = 0

        # On compte la demande solvable
        for agent in self.schedule.agents:
            if isinstance(agent, Household) and not agent.is_owner:
                # L'agent calcule son budget max (Module 1)
                budget = agent.calculate_purchasing_power()

                # Si Budget >= Prix Actuel, c'est une demande valide
                if budget >= self.house_price:
                    # Simulation de la transaction :
                    # La banque valide-t-elle vraiment ? (Module 2)
                    # Pour simplifier le market clearing, on suppose ici que
                    # Budget 'suffisant' implique pré-approbation.
                    demand_count += 1

        # Calcul de l'excès de demande (Gap)
        # Formule : (D - S) / S
        # Si D=12 et S=10 -> +20% de pression -> Prix monte
        if self.housing_supply > 0:
            excess_demand = (demand_count - self.housing_supply) / self.housing_supply
        else:
            excess_demand = 0

        # Mise à jour du prix
        # On limite la variation pour éviter des explosions numériques (Smoothing)
        price_change = self.house_price * self.alpha * excess_demand
        self.house_price += price_change

        # Empêcher les prix négatifs
        if self.house_price < 0:
            self.house_price = 0

        # print(f"Step {self.schedule.steps}: Prix={self.house_price:.0f}, Demande={demand_count}, Taux={self.interest_rate:.3f}")