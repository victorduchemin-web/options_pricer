import math
import csv
import io
import streamlit as st
import matplotlib.pyplot as plt


# 1. Fonction de répartition normale et référence Black-Scholes
def normale(x):
    return (1 + math.erf(x / math.sqrt(2))) / 2


def black_scholes_ref(type_option, S, K, T, r, sigma):
    if T == 0:
        return max(S - K, 0.0) if type_option == "Call" else max(K - S, 0.0)
    K_act = K * math.exp(-r * T)
    if sigma == 0 or S == 0:
        return max(S - K_act, 0.0) if type_option == "Call" else max(K_act - S, 0.0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    if type_option == "Call":
        return max(S * normale(d1) - K_act * normale(d2), 0.0)
    return max(K_act * normale(-d2) - S * normale(-d1), 0.0)


# 2. Moteur binomial de Cox-Ross-Rubinstein (CRR) pour option américaine
def arbre_binomial_americain(type_option, S, K, T, r, sigma, N):
    for valeur in [S, K, T, r, sigma]:
        if not math.isfinite(valeur):
            raise ValueError("Les paramètres doivent être des nombres finis.")
    if type_option not in ["Call", "Put"]:
        raise ValueError("Choisissez Call ou Put.")
    if S < 0 or K <= 0 or T < 0 or sigma < 0 or N < 1:
        raise ValueError("Paramètres invalides.")

    if T == 0:
        return max(S - K, 0.0) if type_option == "Call" else max(K - S, 0.0)

    if sigma == 0 or S == 0:
        prix_final = S * math.exp(r * T)
        val = max(prix_final - K, 0.0) if type_option == "Call" else max(K - prix_final, 0.0)
        val_act = val * math.exp(-r * T)
        exercice_immediat = max(S - K, 0.0) if type_option == "Call" else max(K - S, 0.0)
        return max(val_act, exercice_immediat)

    dt = T / N
    u = math.exp(sigma * math.sqrt(dt))
    d = 1.0 / u
    facteur_act = math.exp(-r * dt)
    p = (math.exp(r * dt) - d) / (u - d)

    if not (0.0 <= p <= 1.0):
        raise ValueError("Condition d'absence d'arbitrage violée dans l'arbre (augmentez N).")

    valeurs = []
    for j in range(N + 1):
        S_T = S * (u ** j) * (d ** (N - j))
        payoff = max(S_T - K, 0.0) if type_option == "Call" else max(K - S_T, 0.0)
        valeurs.append(payoff)

    for i in range(N - 1, -1, -1):
        nouvelles_valeurs = []
        for j in range(i + 1):
            S_noeud = S * (u ** j) * (d ** (i - j))
            continuation = facteur_act * (p * valeurs[j + 1] + (1.0 - p) * valeurs[j])
            exercice = max(S_noeud - K, 0.0) if type_option == "Call" else max(K - S_noeud, 0.0)
            nouvelles_valeurs.append(max(continuation, exercice))
        valeurs = nouvelles_valeurs

    return max(valeurs[0], 0.0)


# 3. Interface Streamlit
st.set_page_config(page_title="Options Américaines", page_icon="🇺🇸", layout="wide")
st.title("Pricer d’options américaines")
st.caption("Modèle binomial de Cox-Ross-Rubinstein (CRR) · Exercice anticipé autorisé · Sans dividendes")

with st.sidebar:
    st.header("Paramètres")
    type_option = st.selectbox("Type d’option", ["Put", "Call"])
    S = st.number_input("Prix du sous-jacent S (€)", min_value=0.0, max_value=1000000.0, value=100.0)
    K = st.number_input("Prix d’exercice K (€)", min_value=0.01, max_value=1000000.0, value=100.0)
    T = st.number_input("Maturité restante T (années)", min_value=0.0, max_value=100.0, value=1.0, step=0.25)
    taux_pct = st.number_input("Taux sans risque annuel (%)", min_value=-20.0, max_value=100.0, value=5.0)
    volatilite_pct = st.number_input("Volatilité annuelle (%)", min_value=0.0, max_value=500.0, value=20.0)
    N = st.slider("Nombre de pas de l'arbre (N)", min_value=10, max_value=500, value=100, step=10)
    st.caption("Plus N est élevé, plus le prix converge vers la valeur continue.")

r = taux_pct / 100
sigma = volatilite_pct / 100

try:
    prix_us = arbre_binomial_americain(type_option, S, K, T, r, sigma, N)
    prix_eu = black_scholes_ref(type_option, S, K, T, r, sigma)
    prime_anticipee = max(prix_us - prix_eu, 0.0)
except (ValueError, OverflowError) as e:
    st.error(f"Erreur de calcul : {e}")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric(f"Prix {type_option} américain", f"{prix_us:.4f} €")
col2.metric("Équivalent européen (BS)", f"{prix_eu:.4f} €")
col3.metric("Prime d'exercice anticipé", f"{prime_anticipee:.4f} €")

if type_option == "Call" and r >= 0:
    st.caption("Propriété théorique : sans dividende et avec r ≥ 0, il n'est jamais optimal d'exercer un Call américain avant maturité.")
else:
    st.caption("La prime d'exercice anticipé mesure la valeur supplémentaire liée au droit d'exercer avant T.")

# Graphique de convergence selon N
pas_testes = list(range(10, min(N + 100, 410), 10))
prix_convergence = [arbre_binomial_americain(type_option, S, K, T, r, sigma, n) for n in pas_testes]

figure, axes = plt.subplots(figsize=(9, 4))
axes.plot(pas_testes, prix_convergence, color="#2563eb", marker="o", markersize=3, label="Prix américain (CRR)")
axes.axhline(prix_eu, color="gray", linestyle="--", label="Prix européen (Black-Scholes)")
axes.scatter([N], [prix_us], color="#f59e0b", zorder=4, label=f"Paramètre actuel (N={N})")
axes.set_xlabel("Nombre de pas de temps (N)")
axes.set_ylabel("Prix de l’option (€)")
axes.set_title(f"Convergence du prix du {type_option.lower()} américain selon N")
axes.grid(alpha=0.2)
axes.legend()
figure.tight_layout()
st.pyplot(figure)
plt.close(figure)

# Export CSV
contenu = io.StringIO()
tableau = csv.writer(contenu, delimiter=";")
tableau.writerow(["Exercice", "Type", "S_EUR", "K_EUR", "T_annees", "Taux_pct", "Volatilite_pct", "Pas_N", "Prix_US_EUR", "Prix_EU_EUR", "Prime_Anticipee_EUR"])
tableau.writerow(["Americaine", type_option, S, K, T, taux_pct, volatilite_pct, N, prix_us, prix_eu, prime_anticipee])
st.download_button(
    "Télécharger le résultat (CSV)",
    data=contenu.getvalue().encode("utf-8-sig"),
    file_name="resultat_option_americaine.csv",
    mime="text/csv"
)
