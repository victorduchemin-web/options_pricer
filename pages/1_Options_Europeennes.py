import math
import csv
import io
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Pricer européen", page_icon="🇪🇺", layout="wide")


# 1. Fonctions de la loi normale centrée réduite
def normale(x):
    resultat = (1 + math.erf(x / math.sqrt(2))) / 2
    return resultat


def densite_normale(x):
    return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)


# 2. Calcul financier : prix Black-Scholes et sensibilités (Grecques)
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
            return max(S - K, 0.0)
        return max(K - S, 0.0)

    K_actualise = K * math.exp(-r * T)

    # Ces cas évitent un logarithme de zéro ou une division par zéro
    if sigma == 0 or S == 0:
        if type_option == "Call":
            return max(S - K_actualise, 0.0)
        return max(K_actualise - S, 0.0)

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
    return max(prix, 0.0)


def grecques_black_scholes(type_option, S, K, T, r, sigma):
    """Calcule les 5 Grecques analytiques selon les conventions de marché."""
    K_actualise = K * math.exp(-r * T)

    # Gestion des cas limites (maturité nulle, volatilité nulle ou sous-jacent nul)
    if T == 0 or sigma == 0 or S == 0:
        if type_option == "Call":
            in_the_money = S > K_actualise
            delta = 1.0 if in_the_money else 0.0
            rho = (T * K_actualise / 100.0) if in_the_money else 0.0
            theta = (-r * K_actualise / 365.0) if in_the_money else 0.0
        else:
            in_the_money = S < K_actualise
            delta = -1.0 if in_the_money else 0.0
            rho = (-T * K_actualise / 100.0) if in_the_money else 0.0
            theta = (r * K_actualise / 365.0) if in_the_money else 0.0
        return {"delta": delta, "gamma": 0.0, "vega": 0.0, "theta": theta, "rho": rho}

    racine_T = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * racine_T)
    d2 = d1 - sigma * racine_T
    phi_d1 = densite_normale(d1)

    gamma = phi_d1 / (S * sigma * racine_T)
    vega = (S * phi_d1 * racine_T) / 100.0  # Pour +1 % de volatilité

    if type_option == "Call":
        delta = normale(d1)
        theta_annuel = -(S * phi_d1 * sigma) / (2 * racine_T) - r * K_actualise * normale(d2)
        rho = (K * T * math.exp(-r * T) * normale(d2)) / 100.0  # Pour +1 % de taux
    else:
        delta = normale(d1) - 1.0
        theta_annuel = -(S * phi_d1 * sigma) / (2 * racine_T) + r * K_actualise * normale(-d2)
        rho = -(K * T * math.exp(-r * T) * normale(-d2)) / 100.0  # Pour +1 % de taux

    theta = theta_annuel / 365.0  # Par jour calendaire

    return {
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
        "rho": rho,
    }


# 3. Interface Streamlit
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

r = taux_pct / 100
sigma = volatilite_pct / 100

try:
    prix = black_scholes(type_option, S, K, T, r, sigma)
    grecques = grecques_black_scholes(type_option, S, K, T, r, sigma)
except (ValueError, OverflowError):
    st.error("Paramètres invalides ou trop extrêmes. Vérifiez les valeurs saisies.")
    st.stop()

st.metric("Prix théorique du " + type_option.lower(), f"{prix:.4f} €")
st.caption("Prix par unité de sous-jacent, sans multiplicateur de contrat.")

st.subheader("Sensibilités (Grecques)")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Delta (Δ)", f"{grecques['delta']:.4f}")
col2.metric("Gamma (Γ)", f"{grecques['gamma']:.4f}")
col3.metric("Vega (𝒱 / +1 %)", f"{grecques['vega']:.4f} €")
col4.metric("Theta (Θ / jour)", f"{grecques['theta']:.4f} €")
col5.metric("Rho (ρ / +1 %)", f"{grecques['rho']:.4f} €")
st.caption("Δ et Γ pour +1 € de sous-jacent · 𝒱 et ρ pour +1 point de pourcentage · Θ par jour calendaire.")

# 4. Courbe dynamique selon le sous-jacent S
courbe_choisie = st.radio(
    "Grandeur à afficher sur le graphique selon S :",
    ["Prix (€)", "Delta (Δ)", "Gamma (Γ)", "Vega (𝒱)", "Theta (Θ)"],
    horizontal=True,
)

prix_sous_jacent = []
valeurs_courbe = []
borne_superieure = max(2 * S, 2 * K)

for i in range(101):
    S_scenario = borne_superieure * i / 100
    prix_sous_jacent.append(S_scenario)
    if courbe_choisie == "Prix (€)":
        valeurs_courbe.append(black_scholes(type_option, S_scenario, K, T, r, sigma))
    else:
        g_scen = grecques_black_scholes(type_option, S_scenario, K, T, r, sigma)
        cle = {"Delta (Δ)": "delta", "Gamma (Γ)": "gamma", "Vega (𝒱)": "vega", "Theta (Θ)": "theta"}[courbe_choisie]
        valeurs_courbe.append(g_scen[cle])

valeur_actuelle_map = {
    "Prix (€)": prix,
    "Delta (Δ)": grecques["delta"],
    "Gamma (Γ)": grecques["gamma"],
    "Vega (𝒱)": grecques["vega"],
    "Theta (Θ)": grecques["theta"],
}

figure, axes = plt.subplots(figsize=(9, 4))
axes.plot(prix_sous_jacent, valeurs_courbe, color="#2563eb", label=courbe_choisie)
axes.scatter([S], [valeur_actuelle_map[courbe_choisie]], color="#f59e0b", label="Paramètres actuels", zorder=3)
axes.axvline(K, color="gray", linestyle="--", label="Prix d’exercice K")
axes.set_xlabel("Prix du sous-jacent (€)")
axes.set_ylabel(courbe_choisie)
axes.set_title(f"{courbe_choisie} du {type_option.lower()} selon le sous-jacent")
axes.grid(alpha=0.2)
axes.legend()
figure.tight_layout()
st.pyplot(figure)
plt.close(figure)
st.caption("K, T, r et σ restent constants.")

# 5. Export CSV : prix et Grecques
contenu = io.StringIO()
tableau = csv.writer(contenu, delimiter=";")
tableau.writerow([
    "Type", "S_EUR", "K_EUR", "T_annees", "Taux_pct", "Volatilite_pct",
    "Prix_EUR", "Delta", "Gamma", "Vega_1pct_EUR", "Theta_jour_EUR", "Rho_1pct_EUR"
])
tableau.writerow([
    type_option, S, K, T, taux_pct, volatilite_pct,
    prix, grecques["delta"], grecques["gamma"], grecques["vega"], grecques["theta"], grecques["rho"]
])
st.download_button(
    "Télécharger le résultat (CSV)",
    data=contenu.getvalue().encode("utf-8-sig"),
    file_name="resultat_option_europeenne.csv",
    mime="text/csv",
)
st.caption("À l’importation : séparateur point-virgule ; séparateur décimal point.")
