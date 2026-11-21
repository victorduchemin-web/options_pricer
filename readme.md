# Pricer d'options — Européennes & Américaines

Application interactive développée en Python (Streamlit) dans le cadre du M2 Gestion de portefeuille. 
L'objectif de ce projet est de valoriser des options vanilles (Call et Put) en combinant les approches analytiques (options européennes) et numériques (options américaines), de visualiser la sensibilité du prix au cours du sous-jacent et d'exporter les résultats.

## Avancement du développement

* [x] **Module Options Européennes (Black-Scholes-Merton)** : Valorisation analytique sans dividendes, traitement des cas limites ($T = 0$, $\sigma = 0$, $S = 0$), courbe de sensibilité et export CSV.
* [ ] **Module Options Américaines (en cours)** : Implémentation d'un modèle numérique (arbre binomial de Cox-Ross-Rubinstein) sur la même interface pour intégrer la prime d'exercice anticipé.
* [ ] **Sensibilités (Grecques)** : Calcul et affichage du $\Delta$, $\Gamma$, $\mathcal{V}$, $\Theta$ et $\rho$.

---

## Installation et lancement

### 1. Prérequis
Python 3 (version 3.10 ou supérieure recommandée) avec `pip` et `venv` installés.

### 2. Mise en place de l'environnement
Depuis le terminal, à la racine du dossier du projet :

```bash
# Création et activation de l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate      # Sur macOS / Linux
# .venv\Scripts\activate       # Sur Windows

# Installation des dépendances
pip install -r requirements.txt
```

### 3. Démarrage de l'application
Une fois l'environnement activé, lancer le serveur local Streamlit :

```bash
streamlit run app.py
```

L'interface s'ouvre automatiquement dans le navigateur par défaut (généralement à l'adresse `http://localhost:8501`). Pour arrêter l'application, utiliser `Ctrl + C` dans le terminal.

---

## Utilisation et paramètres du pricer

L'ensemble des paramètres se configure depuis le panneau latéral gauche de l'interface :

| Paramètre | Description | Unité / Format attendu | Exemple |
| :--- | :--- | :--- | :--- |
| **Type d'option** | Nature du contrat (`Call` ou `Put`) | Sélection | `Call` |
| **Sous-jacent ($S$)** | Cours actuel de l'actif sous-jacent | Euros (`€`), $\ge 0$ | `100.0` |
| **Strike ($K$)** | Prix d'exercice fixé au contrat | Euros (`€`), $> 0$ | `100.0` |
| **Maturité ($T$)** | Temps restant jusqu'à l'échéance | Années ($\ge 0$) | `1.0` (1 an), `0.5` (6 mois) |
| **Taux sans risque ($r$)** | Taux annuel à capitalisation continue | Pourcentage (`%`) | `5.0` pour $5\,\%$ |
| **Volatilité ($\sigma$)** | Volatilité annuelle implicite ou historique | Pourcentage (`%`), $\ge 0$ | `20.0` pour $20\,\%$ |

### Fonctionnalités de l'interface
* **Valorisation instantanée** : Affichage du prix théorique par unité de sous-jacent (sans multiplicateur de contrat), recalculé dynamiquement à chaque modification d'un paramètre.
* **Graphique de sensibilité** : Tracé de l'évolution du prix de l'option sur 101 points pour $S \in [0, 2 \max(S, K)]$, à $K, T, r, \sigma$ constants, avec repérage du cours actuel et du strike $K$.
* **Export CSV** : Téléchargement d'un fichier `resultat_option.csv` (séparateur `;`, encodage UTF-8 BOM) directement exploitable sous Excel.

---

## Architecture et logique d'implémentation (à modifier)

Le code de `app.py` est structuré de manière séquentielle afin de séparer le moteur mathématique de la couche d'affichage :

1. **Fonction de répartition normale (`normale(x)`)** : Calcul de $\mathcal{N}(x)$ via la fonction d'erreur de Gauss `math.erf` de la bibliothèque standard Python, évitant d'alourdir le projet avec `scipy`.
2. **Moteur de pricing (`black_scholes`)** :
   * Validation stricte des entrées (rejet des valeurs non finies, négatives ou incohérentes via `ValueError`).
   * Traitement explicite des cas limites avant le calcul logarithmique : payoff intrinsèque à maturité ($T = 0$) et prix déterministe actualisé si $\sigma = 0$ ou $S = 0$.
   * Application de la formule fermée de Black-Scholes-Merton après conversion des taux et volatilités en format décimal.
3. **Interface et visualisation (`streamlit` & `matplotlib`)** : Gestion des saisies utilisateur dans la barre latérale, interception des erreurs de calcul via `try/except` et génération dynamique du graphique et du flux mémoire `io.StringIO` pour l'export CSV.

### Structure du dépôt (à modifier)
* `app.py` : Code principal (calcul financier, interface Streamlit, graphique et export).
* `requirements.txt` : Liste des bibliothèques requises (`streamlit`, `matplotlib`).
* `README.md` : Documentation du projet.
