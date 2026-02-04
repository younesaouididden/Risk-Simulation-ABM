import matplotlib.pyplot as plt
from HousingMarketModel import HousingMarketModel


def run_simulation():
    # 1. Initialisation du modèle
    # On prend 1000 ménages pour avoir une loi des grands nombres décente
    print("Initialisation de la simulation...")
    model = HousingMarketModel(N_households=1000, N_banks=1, initial_price=100000)

    # 2. Exécution de la boucle temporelle (100 mois)
    # Le choc de la Banque Centrale est prévu au step 50
    print("Exécution en cours", end="")
    for i in range(100):
        model.step()
        if i % 10 == 0: print(".", end="")  # Barre de chargement simple
    print(" Terminé.")

    # 3. Extraction des données
    results = model.datacollector.get_model_vars_dataframe()

    # 4. Visualisation (Dashboard de Risque)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Graphique 1 : L'évolution du Prix Immobilier
    ax1.plot(results["Price"], color='#1f77b4', linewidth=2, label='Prix Immobilier Moyen')
    ax1.set_title("Dynamique du Marché Immobilier")
    ax1.set_ylabel("Prix (Dirhams)")
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()

    # Graphique 2 : Le Taux d'Intérêt (Le déclencheur)
    ax2.plot(results["Interest Rate"], color='#d62728', linewidth=2, linestyle='--', label="Taux d'intérêt (Crédit)")
    ax2.set_title("Politique Monétaire & Taux Commerciaux")
    ax2.set_ylabel("Taux")
    ax2.set_xlabel("Temps (Mois)")
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend()

    # Marquage visuel du Choc
    ax1.axvline(x=50, color='black', alpha=0.3)
    ax2.axvline(x=50, color='black', alpha=0.3)
    ax1.text(52, results["Price"].max(), "Choc de Taux", fontsize=10, color='black')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    run_simulation()