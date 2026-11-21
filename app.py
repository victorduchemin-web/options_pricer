import math
import csv
import io


# 1. Fonction de répartition de la loi normale centrée réduite
def normale(x):
    resultat = (1 + math.erf(x / math.sqrt(2))) / 2
    return resultat


# 2. Calcul financier : taux et volatilité reçus sous forme décimale
def black_scholes(type_option, S, K, T, r, sigma):
    for valeur in [S, K, T, r, sigma]:
        if not math.isfinite(valeur):
            raise ValueError("Les paramètres doivent être des nombres finis.")
    if type_option not in ["Call", "Put"]:
        raise ValueError("Choisissez Call ou Put.")
    if S < 0 or K <= 0 or T < 0 or sigma < 0:
        raise ValueError("S, T et sigma doivent être positifs ou nuls ; K strictement positif.")

    # À l'échéance, le prix est égal au payoff
    if T == 0:
        if type_option == "Call":
            return max(S - K, 0)
        return max(K - S, 0)

    K_actualise = K * math.exp(-r * T)

    # Ces cas évitent un logarithme de zéro ou une division par zéro
    if sigma == 0 or S == 0:
        if type_option == "Call":
            return max(S - K_actualise, 0)
        return max(K_actualise - S, 0)

    racine_T = math.sqrt(T)
    variance = sigma ** 2
    numerateur = math.log(S / K) + (r + variance / 2) * T
    denominateur = sigma * racine_T
    d1 = numerateur / denominateur
    d2 = d1 - denominateur

    if type_option == "Call":
        prix = S * normale(d1) - K_actualise * normale(d2)
    else:
        prix = K_actualise * normale(-d2) - S * normale(-d1)
    return max(prix, 0)
    
# 3. Interface : 
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Pricer européen", page_icon="📈", layout="wide")
st.title("Pricer d’options européennes")
st.caption("Projet de maths appliquées · Black-Scholes · Sans dividendes")

with st.sidebar:
    st.header("Paramètres")
    type_option = st.selectbox("Type d’option", ["Call", "Put"])
    S = st.number_input("Prix du sous-jacent S (€)", min_value=0.0, max_value=1000000.0, value=100.0)
    K = st.number_input("Prix d’exercice K (€)", min_value=0.01, max_value=1000000.0, value=100.0)
    T = st.number_input("Maturité restante T (années)", min_value=0.0, max_value=100.0, value=1.0, step=0.25)
    taux_pct = st.number_input("Taux sans risque annuel (%)", min_value=-20.0, max_value=100.0, value=5.0)
    volatilite_pct = st.number_input("Volatilité annuelle (%)", min_value=0.0, max_value=500.0, value=20.0)
    st.caption("Saisir 5 pour 5 %. Six mois = 0,5 an. Taux à capitalisation continue.")

# Conversion des pourcentages avant l'appel à la fonction financière
r = taux_pct / 100
sigma = volatilite_pct / 100

try:
    prix = black_scholes(type_option, S, K, T, r, sigma)
except (ValueError, OverflowError):
    st.error("Paramètres invalides ou trop extrêmes. Vérifiez les valeurs saisies.")
    st.stop()

st.metric("Prix théorique du " + type_option.lower(), f"{prix:.4f} €")
st.caption("Prix par unité de sous-jacent, sans multiplicateur de contrat.")

# 4. Courbe : seul le prix du sous-jacent varie
prix_sous_jacent = []
prix_options = []
borne_superieure = max(2 * S, 2 * K)
for i in range(101):
    S_scenario = borne_superieure * i / 100
    prix_scenario = black_scholes(type_option, S_scenario, K, T, r, sigma)
    prix_sous_jacent.append(S_scenario)
    prix_options.append(prix_scenario)

figure, axes = plt.subplots(figsize=(9, 4))
axes.plot(prix_sous_jacent, prix_options, color="#2563eb", label="Prix théorique")
axes.scatter([S], [prix], color="#f59e0b", label="Paramètres actuels", zorder=3)
axes.axvline(K, color="gray", linestyle="--", label="Prix d’exercice K")
axes.set_xlabel("Prix du sous-jacent (€)")
axes.set_ylabel("Prix de l’option (€)")
axes.set_title("Prix du " + type_option.lower() + " selon le sous-jacent")
axes.grid(alpha=0.2)
axes.legend()
figure.tight_layout()
st.pyplot(figure)
plt.close(figure)
st.caption("K, T, r et σ restent constants. La courbe représente le prix, pas le profit.")

# 5. Export CSV : paramètres et prix, lisibles dans un tableur
contenu = io.StringIO()
tableau = csv.writer(contenu, delimiter=";")
tableau.writerow(["Type", "S_EUR", "K_EUR", "T_annees", "Taux_pct", "Volatilite_pct", "Prix_EUR"])
tableau.writerow([type_option, S, K, T, taux_pct, volatilite_pct, prix])
st.download_button("Télécharger le résultat (CSV)", data=contenu.getvalue().encode("utf-8-sig"), file_name="resultat_option.csv", mime="text/csv")
st.caption("À l’importation : séparateur point-virgule ; séparateur décimal point.")
