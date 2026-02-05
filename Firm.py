from mesa import Agent
import math


class Firm(Agent):
    """
    Agent Entreprise.
    Rôle : Produire de la valeur, verser des salaires, et ajuster la main d'oeuvre.
    Jeu : Minimiser les coûts pour survivre face aux chocs de taux.
    """

    def __init__(self, unique_id, model, wage=2000, initial_employees=None):
        super().__init__(unique_id, model)
        self.wage = wage
        self.employees = [] if initial_employees is None else initial_employees
        self.cash_on_hand = 100000  # Trésorerie tampon
        self.revenue = 0  # Revenu exogène (chiffre d'affaires)

        # Structure de la dette de l'entreprise
        self.debt = 1500000
        # L'entreprise est endettée (Leurvier), ce qui la rend sensible aux taux

    def step(self):
        # 1. Génération de Revenu (Simplifié: proportionnel à la taille)
        # Chaque employé génère un peu plus que son salaire (marge)
        productivity_per_worker = self.wage * 1.20
        self.revenue = len(self.employees) * productivity_per_worker

        # 2. Calcul des Coûts
        wage_bill = len(self.employees) * self.wage

        # Le coût de la dette dépend du taux directeur actuel !
        # C'est le CANAL DE TRANSMISSION : Taux BC -> Bilan Entreprise
        interest_payment = self.debt * self.model.interest_rate

        # 3. Calcul du Profit Net
        profit = self.revenue - wage_bill - interest_payment

        # Mise à jour de la trésorerie
        self.cash_on_hand += profit

        # 4. Décision Stratégique : Embauche ou Licenciement
        if profit < 0:
            self.fire_staff(abs(profit))
        elif profit > 0 and self.model.random.random() < 0.1:
            # En temps normal, petite chance d'embaucher (croissance organique)
            self.hire_staff()

    def fire_staff(self, deficit):
        """
        Algorithme de licenciement pour combler le déficit.
        """
        # Combien de têtes faut-il couper ?
        if self.wage > 0:
            nb_to_fire = math.ceil(deficit / self.wage)
        else:
            nb_to_fire = 0

        # On ne peut pas virer plus que l'effectif total
        nb_to_fire = min(nb_to_fire, len(self.employees))

        if nb_to_fire > 0:
            # On choisit les victimes (Aléatoire = Pas de stratégie de protection)
            fired_employees = self.model.random.sample(self.employees, nb_to_fire)

            for household in fired_employees:
                # ACTION DU JEU : L'entreprise coupe le flux de revenu
                household.lose_job()  # Méthode à ajouter dans Household
                self.employees.remove(household)

            # print(f"Entreprise {self.unique_id}: {nb_to_fire} licenciements pour sauver {deficit:.0f} de marge.")

    def hire_staff(self):
        """
        Logique d'embauche : Trouve un chômeur et l'embauche.
        """
        # 1. Scanner le marché pour trouver des chômeurs
        # (Dans une version optimisée, on aurait une liste 'labor_market' dans le modèle)
        potential_hires = [
            agent for agent in self.model.schedule.agents
            if getattr(agent, "employer", -1) is None and agent.unique_id != self.unique_id
        ]

        # Note technique : getattr(agent, "employer", -1) est une sécurité
        # pour éviter de planter si on tombe sur la Banque ou la BC qui n'ont pas d'attribut 'employer'.

        if potential_hires:
            # 2. Choisir un chômeur au hasard (Matching aléatoire)
            new_employee = self.model.random.choice(potential_hires)

            # 3. Signer le contrat
            new_employee.get_job(self)  # On appelle la méthode du ménage
            self.employees.append(new_employee)

            # print(f"Entreprise {self.unique_id} a embauché {new_employee.unique_id}.")