import csv
import io
import streamlit as st
import matplotlib.pyplot as plt
from pricers import black_scholes, arbre_binomial_americain

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
    prix_eu = black_scholes(type_option, S, K, T, r, sigma)
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
