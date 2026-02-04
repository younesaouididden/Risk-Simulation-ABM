from mesa import Agent


class CentralBank(Agent):
    """
    Agent Banque Centrale.
    Rôle : Fixer le taux sans risque (Base Rate).
    Scénario : Maintient les taux bas, puis provoque un choc.
    """

    def __init__(self, unique_id, model, bank_spread=0.02):
        super().__init__(unique_id, model)
        self.base_rate = 0.02  # Taux initial (2%)
        self.bank_spread = bank_spread  # Marge des banques commerciales (2%)

    def step(self):
        # 1. Définition de la Politique Monétaire (Le Scénario)
        # On utilise le compteur de tours du modèle
        current_step = self.model.schedule.steps

        if current_step < 50:
            self.base_rate = 0.02  # Politique accomodante
        else:
            self.base_rate = 0.05  # Choc restrictif (Le "Minsky Moment")

        # 2. Transmission de la politique monétaire
        # Le nouveau taux commercial cible
        target_market_rate = self.base_rate + self.bank_spread

        # La BC 'force' la mise à jour des taux des banques commerciales
        # Note: Cela suppose que nous puissions accéder aux autres agents via le modèle
        for agent in self.model.schedule.agents:
            # On vérifie si l'agent est une Banque (nécessite d'importer la classe Bank ou de vérifier le type)
            if type(agent).__name__ == 'Bank':
                agent.interest_rate = target_market_rate

        # Log pour debug
        # if current_step == 50:
        #     print(f"!!! CHOC DE TAUX : Passage à {self.base_rate*100}% !!!")