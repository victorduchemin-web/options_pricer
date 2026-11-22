# Pricer d'options — Européennes & Américaines

Application interactive développée en Python (Streamlit) dans le cadre du cours de mathématiques financières - M2 gestion de portefeuille. 
L'objectif de ce projet est de valoriser des options vanilles (Call et Put) en observant des options européennes et des options américaines, de visualiser la sensibilité et la convergence des prix et d'exporter les résultats.

## Avancement du développement

- [x] **Module Options Européennes (Black-Scholes-Merton)** : Valorisation analytique sans dividendes, traitement des cas limites ($T = 0$, $\sigma = 0$, $S = 0$), courbe de sensibilité et export CSV.
- [x] **Module Options Américaines (CRR)** : Implémentation d'un modèle numérique (arbre binomial de Cox-Ross-Rubinstein) sur une page dédiée pour intégrer l'exercice anticipé, calculer la prime d'exercice anticipé et visualiser la convergence selon le nombre de pas $N$.
- [x] **Sensibilités (Grecques)** : Calcul et affichage du $\Delta$, $\Gamma$, $\mathcal{V}$, $\Theta$ et $\rho$.

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
Une fois l'environnement activé, lancer le serveur local Streamlit depuis la racine :

```bash
streamlit run app.py
```

L'interface s'ouvre automatiquement dans le navigateur par défaut (généralement à l'adresse `http://localhost:8501`). La navigation entre la page d'accueil, le module européen et le module américain s'effectue via le menu latéral gauche ou les boutons d'accès direct. Pour arrêter l'application, utiliser `Ctrl + C` dans le terminal.

---

## Utilisation et paramètres des pricers

L'ensemble des paramètres se configure depuis le panneau latéral gauche de chaque module :

| Paramètre | Description | Unité / Format attendu | Exemple |
| :--- | :--- | :--- | :--- |
| **Type d'option** | Nature du contrat (`Call` ou `Put`) | Sélection | `Call` / `Put` |
| **Sous-jacent ($S$)** | Cours actuel de l'actif sous-jacent | Euros (`€`), $\ge 0$ | `100.0` |
| **Strike ($K$)** | Prix d'exercice fixé au contrat | Euros (`€`), $> 0$ | `100.0` |
| **Maturité ($T$)** | Temps restant jusqu'à l'échéance | Années ($\ge 0$) | `1.0` (1 an), `0.5` (6 mois) |
| **Taux sans risque ($r$)** | Taux annuel à capitalisation continue | Pourcentage (`%`) | `5.0` pour $5\,\%$ |
| **Volatilité ($\sigma$)** | Volatilité annuelle implicite ou historique | Pourcentage (`%`), $\ge 0$ | `20.0` pour $20\,\%$ |
| **Nombre de pas ($N$)** | *(Module Américain)* Discrétisation de l'arbre binomial | Entier ($10$ à $500$) | `100` |

### Fonctionnalités de l'interface
- **Valorisation instantanée & prime d'exercice anticipé** : Affichage du prix théorique par unité de sous-jacent. Sur le module américain, comparaison directe avec l'équivalent européen Black-Scholes et calcul de la prime d'exercice anticipé ($P_{\text{US}} - P_{\text{EU}}$).
- **Sensibilités (Grecques)** : Affichage en temps réel des 5 Grecques selon les conventions de marché ($\Delta$ et $\Gamma$ par euro de sous-jacent, $\mathcal{V}$ et $\rho$ pour $+1\,\%$ de volatilité ou de taux, $\Theta$ par jour calendaire).
- **Graphiques dynamiques** :
  - *Options Européennes* : Sélecteur interactif permettant de tracer au choix le Prix (€), $\Delta$, $\Gamma$, $\mathcal{V}$, $\Theta$ ou $\rho$ sur 101 points pour $S \in [0, 2 \max(S, K)]$.
  - *Options Américaines* : Même sélecteur de courbes selon $S$ avec superposition de la référence européenne en pointillés (mettant en évidence la frontière d'exercice anticipé), complété par l'analyse de convergence du prix CRR selon le nombre de pas $N$.
- **Export CSV** : Téléchargement des résultats complets (paramètres, prix, prime d'exercice anticipé et 5 Grecques) au format CSV (`;`) directement exploitable sous Excel.

---

## Architecture et logique d'implémentation

L'application repose sur l'architecture multi-pages native de Streamlit afin d'isoler chaque modèle tout en conservant une navigation unifiée :

1. **Point d'entrée (`app.py`)** : Page d'accueil et routeur principal (`st.navigation`) présentant les deux approches de valorisation et offrant des liens directs vers les deux modules.
2. **Moteur Européen (`pages/1_Options_Europeennes.py`)** :
   - Calcul de $\mathcal{N}(x)$ et $\varphi(x)$ via `math.erf` et `math.exp` de la bibliothèque standard Python, évitant d'alourdir le projet avec `scipy`.
   - Validation stricte des entrées (`ValueError`), traitement explicite des cas limites ($T = 0$, $\sigma = 0$, $S = 0$) et application des formules fermées de Black-Scholes-Merton pour le prix et les 5 Grecques.
3. **Moteur Américain (`pages/2_Options_Americaines.py`)** :
   - Construction de l'arbre binomial de Cox-Ross-Rubinstein ($u = e^{\sigma \sqrt{\Delta t}}$, $d = 1/u$, probabilité risque-neutre $p = \frac{e^{r \Delta t} - d}{u - d}$) avec vérification de la condition d'absence d'arbitrage ($0 \le p \le 1$).
   - Rétropropagation dans l'arbre comparant à chaque nœud la valeur de continuation actualisée et le payoff d'exercice immédiat.
   - Extraction directe de $\Delta$, $\Gamma$ et $\Theta$ à partir des premiers nœuds de l'arbre ($i = 1, 2$) et calcul de $\mathcal{V}$ et $\rho$ par différences finies centrées.
4. **Interface et visualisation (`streamlit` & `matplotlib`)** : Gestion des saisies utilisateur dans la barre latérale, interception des erreurs de calcul via `try/except`, génération dynamique des graphiques et création d'un flux mémoire `io.StringIO` pour l'export CSV.

### Structure du projet
- `app.py` : Page d'accueil et navigation principale de l'application multi-pages.
- `pages/1_Options_Europeennes.py` : Module d'options européennes (formules fermées de Black-Scholes-Merton, courbes de prix et Grecques, export CSV).
- `pages/2_Options_Americaines.py` : Module d'options américaines (arbre binomial CRR, prime d'exercice anticipé, Grecques numériques, graphiques de sensibilité et de convergence, export CSV).
- `requirements.txt` : Liste des bibliothèques requises (`streamlit`, `matplotlib`).
- `README.md` : Documentation du projet.
- `.gitignore` : Fichier d'exclusion Git standard pour Python
