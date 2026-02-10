import matplotlib.pyplot as plt
import numpy as np
from HousingMarketModel import HousingMarketModel

# --- GESTIONNAIRE DE SCÉNARIOS ---
SCENARIOS = {
    "1": {
        "name": "L'Âge d'Or (Croissance Saine)",
        "description": "Taux bas, entreprises saines, plein emploi.",
        "params": {
            "N_households": 1000,
            "shock_step": 150, # Pas de choc avant la fin
            "base_rate": 0.03,
            "shock_rate": 0.03,
            "firm_debt": 0,       # Entreprises sans dette
            "firm_margin": 1.20,  # Marge confortable (20%)
            "audit_prob": 0.02,
            "init_supply": 500,
            "enable_inequality": False,
            "mean_income": 4000,
            "gini_index": 0.35,
            "min_wage": 2500
        }
    },
    "2": {
        "name": "Le Krach Systémique (Type 2008)",
        "description": "Scénario calibré : Dette de 10M qui devient toxique à 7%.",
        "params": {
            "N_households": 1000,
            "shock_step": 50,
            "base_rate": 0.04,
            "shock_rate": 0.07,

            # --- LE JUSTE MILIEU ---
            "firm_debt": 10000000,  # 10 Millions (Survivable à 4%, Mortel à 7%)
            "firm_margin": 1.05,    # Marge faible (5%)
            # -----------------------

            "audit_prob": 0.05,
            "init_supply": 500,
            "enable_inequality": False,
            "mean_income": 4000,
            "gini_index": 0.35,
            "min_wage": 2500
        }
    },
    "3": {
        "name": "Stagflation (Choc d'Offre)",
        "description": "Taux hauts dès le début, économie qui peine à démarrer.",
        "params": {
            "N_households": 1000,
            "shock_step": 20,
            "base_rate": 0.06,
            "shock_rate": 0.09,
            "firm_debt": 800000,
            "firm_margin": 1.30,
            "audit_prob": 0.20,
            "init_supply": 200  # Pénurie de logements initiale
        }
    },
    "4": {
        "name": "Bac à Sable (Population Réaliste Maroc)",
        "description": "Distribution Log-Normale des revenus (Gini ~0.40).",
        "params": {
            "N_households": 1000,
            "shock_step": 50,
            "base_rate": 0.04,
            "shock_rate": 0.07,
            "firm_debt": 1500000,
            "firm_margin": 1.20,
            "audit_prob": 0.10,
            "init_supply": 500,

            # --- NOUVEAUX PARAMÈTRES DATA ---
            "enable_inequality": True,  # Activer la distribution complexe
            "mean_income": 5000,  # Salaire moyen cible
            "gini_index": 0.20,  # Inégalités (0=Communisme, 1=1 personne a tout)
            "min_wage": 3000  # SMIG (Plancher)
        }
    },
    # ... (Garde tes anciens scénarios, ajoute "enable_inequality": False pour eux)
}



def run_simulation(scenario_id):
    config = SCENARIOS[scenario_id]["params"]
    print(f"\n--- Démarrage : {SCENARIOS[scenario_id]['name']} ---")
    print(f"Paramètres : {config}")

    # Initialisation avec le Dictionnaire de Config
    model = HousingMarketModel(config)

    # Exécution
    print("Simulation en cours [", end="")
    for i in range(100):
        model.step()
        if i % 10 == 0: print("=", end="")
    print("] Terminé.")

    # Extraction
    results = model.datacollector.get_model_vars_dataframe()

    # --- DASHBOARD ULTIME (6 Graphiques) ---
    fig, axes = plt.subplots(3, 2, figsize=(14, 12), sharex=True)
    plt.subplots_adjust(hspace=0.3)

    # 1. Macro: Taux
    ax = axes[0, 0]
    ax.plot(results["Interest Rate"], color='red', linestyle='--', label='Taux Directeur')
    ax.set_title("Politique Monétaire")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Macro: Chômage
    ax = axes[0, 1]
    ax.plot(results["Unemployment"] * 100, color='orange', linewidth=2, label='Taux Chômage')
    ax.set_title("Économie Réelle (Chômage %)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Immo: Prix
    ax = axes[1, 0]
    ax.plot(results["Price"], color='blue', linewidth=2, label='Prix Moyen')
    ax.set_title("Indice des Prix Immobiliers")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Immo: Offre vs Demande (Comprendre le Prix)
    ax = axes[1, 1]
    ax.plot(results["Housing Supply"], color='green', label='Offre (Stock)')
    ax.plot(results["Deals Count"], color='purple', alpha=0.5, label='Ventes Réalisées')
    ax.set_title("Dynamique de Marché (Volume)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 5. Finance: Prêts Toxiques (Risk Monitor)
    ax = axes[2, 0]
    ax.plot(results["Foreclosures"], color='black', label='Saisies (Cumul)')
    ax.set_title("Défauts de Paiement & Saisies")
    ax.fill_between(results.index, results["Foreclosures"], color='black', alpha=0.1)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 6. Social: Richesse Moyenne
    ax = axes[2, 1]
    ax.plot(results["Mean Wealth"], color='gold', linewidth=2, label='Patrimoine Moyen')
    ax.set_title("Richesse des Ménages (Cash)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Marquage du Choc
    shock_t = config["shock_step"]
    if shock_t < 100:
        for ax_row in axes:
            for ax in ax_row:
                ax.axvline(x=shock_t, color='red', alpha=0.3, linestyle=':')

    plt.suptitle(f"Rapport de Simulation : {SCENARIOS[scenario_id]['name']}", fontsize=16)
    plt.show()


if __name__ == "__main__":
    print("CHOISISSEZ VOTRE SCÉNARIO :")
    print("1. L'Âge d'Or (Croissance infinie)")
    print("2. Le Krach 2008 (Votre chef d'oeuvre)")
    print("3. Stagflation (Difficile)")

    choice = input("Entrez le numéro (1-3) : ")
    if choice in SCENARIOS:
        run_simulation(choice)
    else:
        print("Choix invalide. Lancement du scénario 2 par défaut.")
        run_simulation("2")