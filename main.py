import matplotlib.pyplot as plt
from HousingMarketModel import HousingMarketModel

def run_simulation():
    # 1. Configuration
    # On garde 1000 agents pour avoir des stats fiables sur le chômage
    print("--- Démarrage de la simulation MagnumOpus ---")
    model = HousingMarketModel(N_households=1000, N_banks=1, initial_price=100000)

    # 2. Exécution (100 mois)
    print("Simulation en cours [", end="")
    for i in range(100):
        model.step()
        if i % 10 == 0: print("#", end="")
    print("] Terminé.")

    # 3. Récupération des données
    results = model.datacollector.get_model_vars_dataframe()

    # 4. Visualisation Avancée (3 étages)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    # --- Graphique 1 : La Politique Monétaire (Le Déclencheur) ---
    ax1.plot(results["Interest Rate"], color='red', linewidth=2, linestyle='--')
    ax1.set_title("1. Le Choc : Taux Directeur", fontsize=12, fontweight='bold')
    ax1.set_ylabel("Taux")
    ax1.grid(True, alpha=0.3)
    # Marquer le moment du choc
    ax1.axvline(x=50, color='black', alpha=0.5)

    # --- Graphique 2 : L'Économie Réelle (La Transmission) ---
    ax2.plot(results["Unemployment"] * 100, color='orange', linewidth=2) # En pourcentage
    ax2.set_title("2. La Transmission : Taux de Chômage", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Chômeurs (%)")
    ax2.grid(True, alpha=0.3)
    ax2.axvline(x=50, color='black', alpha=0.5)

    # --- Graphique 3 : Le Marché Immobilier (L'Impact) ---
    ax3.plot(results["Price"], color='blue', linewidth=2)
    ax3.set_title("3. La Conséquence : Prix Immobilier", fontsize=12, fontweight='bold')
    ax3.set_ylabel("Prix (Dirhams)")
    ax3.set_xlabel("Temps (Mois)")
    ax3.grid(True, alpha=0.3)
    ax3.axvline(x=50, color='black', alpha=0.5)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()