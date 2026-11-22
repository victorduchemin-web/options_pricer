import math
import csv
import io
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Options Américaines", page_icon="🇺🇸", layout="wide")


# 1. Fonction de répartition normale et Black-Scholes
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


# 2. Moteur binomial CRR
def arbre_binomial_detaille(type_option, S, K, T, r, sigma, N):
    """Renvoie le prix US ainsi que les nœuds aux pas i=1 et i=2 pour Delta, Gamma et Theta."""
    for valeur in [S, K, T, r, sigma]:
        if not math.isfinite(valeur):
            raise ValueError("Les paramètres doivent être des nombres finis.")
    if type_option not in ["Call", "Put"]:
        raise ValueError("Choisissez Call ou Put.")
    if S < 0 or K <= 0 or T < 0 or sigma < 0 or N < 2:
        raise ValueError("Paramètres invalides (N doit être >= 2).")

    if T == 0:
        prix_0 = max(S - K, 0.0) if type_option == "Call" else max(K - S, 0.0)
        return {"prix": prix_0, "limite": True}

    if sigma == 0 or S == 0:
        prix_final = S * math.exp(r * T)
        val = max(prix_final - K, 0.0) if type_option == "Call" else max(K - prix_final, 0.0)
        val_act = val * math.exp(-r * T)
        exercice_immediat = max(S - K, 0.0) if type_option == "Call" else max(K - S, 0.0)
        return {"prix": max(val_act, exercice_immediat), "limite": True}

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

    noeuds_pas_2 = None
    noeuds_pas_1 = None

    for i in range(N - 1, -1, -1):
        nouvelles_valeurs = []
        for j in range(i + 1):
            S_noeud = S * (u ** j) * (d ** (i - j))
            continuation = facteur_act * (p * valeurs[j + 1] + (1.0 - p) * valeurs[j])
            exercice = max(S_noeud - K, 0.0) if type_option == "Call" else max(K - S_noeud, 0.0)
            nouvelles_valeurs.append(max(continuation, exercice))
        valeurs = nouvelles_valeurs
        if i == 2:
            noeuds_pas_2 = list(valeurs)
        elif i == 1:
            noeuds_pas_1 = list(valeurs)

    return {
        "prix": max(valeurs[0], 0.0),
        "limite": False,
        "dt": dt,
        "u": u,
        "d": d,
        "pas_1": noeuds_pas_1,
        "pas_2": noeuds_pas_2,
    }


def arbre_binomial_americain(type_option, S, K, T, r, sigma, N):
    return arbre_binomial_detaille(type_option, S, K, T, r, sigma, N)["prix"]


def grecques_americaines_crr(type_option, S, K, T, r, sigma, N):
    """Calcule Delta, Gamma, Theta via l'arbre CRR et Vega, Rho par différences finies."""
    res = arbre_binomial_detaille(type_option, S, K, T, r, sigma, N)

    # Cas limites (T = 0, sigma = 0 ou S = 0)
    if res["limite"]:
        K_act = K * math.exp(-r * T)
        if type_option == "Call":
            itm = S > K_act
            delta = 1.0 if itm else 0.0
            rho = (T * K_act / 100.0) if itm else 0.0
            theta = (-r * K_act / 365.0) if itm else 0.0
        else:
            itm = S < K
            delta = -1.0 if itm else 0.0
            rho = 0.0
            theta = 0.0
        return {"delta": delta, "gamma": 0.0, "vega": 0.0, "theta": theta, "rho": rho}

    V00 = res["prix"]
    V10, V11 = res["pas_1"]
    V20, V21, V22 = res["pas_2"]
    u, d, dt = res["u"], res["d"], res["dt"]

    S_u = S * u
    S_d = S * d
    S_uu = S * (u ** 2)
    S_dd = S * (d ** 2)

    # Extraction directe sur les premiers pas de l'arbre
    delta = (V11 - V10) / (S_u - S_d)

    delta_up = (V22 - V21) / (S_uu - S)
    delta_down = (V21 - V20) / (S - S_dd)
    gamma = (delta_up - delta_down) / (0.5 * (S_uu - S_dd))

    theta = ((V21 - V00) / (2.0 * dt)) / 365.0

    # Vega par différence finie centrée (pour +1 % de volatilité)
    h_sigma = 0.005
    if sigma > h_sigma:
        v_plus = arbre_binomial_americain(type_option, S, K, T, r, sigma + h_sigma, N)
        v_moins = arbre_binomial_americain(type_option, S, K, T, r, sigma - h_sigma, N)
        vega = ((v_plus - v_moins) / (2.0 * h_sigma)) / 100.0
    else:
        v_plus = arbre_binomial_americain(type_option, S, K, T, r, sigma + h_sigma, N)
        vega = ((v_plus - V00) / h_sigma) / 100.0

    # Rho par différence finie centrée (pour +1 % de taux sans risque)
    h_r = 0.001  # 0.1 %
    try:
        r_plus = arbre_binomial_americain(type_option, S, K, T, r + h_r, sigma, N)
        r_moins = arbre_binomial_americain(type_option, S, K, T, r - h_r, sigma, N)
        rho = ((r_plus - r_moins) / (2.0 * h_r)) / 100.0
    except ValueError:
        rho = 0.0

    return {
        "delta": delta,
        "gamma": gamma,
        "vega": max(vega, 0.0),
        "theta": theta,
        "rho": rho,
    }


# 3. Interface Streamlit
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
    st.caption("Plus N est élevé, plus le prix et les Grecques convergent vers la limite continue.")

r = taux_pct / 100
sigma = volatilite_pct / 100

try:
    prix_us = arbre_binomial_americain(type_option, S, K, T, r, sigma, N)
    prix_eu = black_scholes_ref(type_option, S, K, T, r, sigma)
    prime_anticipee = max(prix_us - prix_eu, 0.0)
    grecques_us = grecques_americaines_crr(type_option, S, K, T, r, sigma, N)
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

st.subheader("Sensibilités numériques (Grecques CRR)")
g1, g2, g3, g4, g5 = st.columns(5)
g1.metric("Delta (Δ)", f"{grecques_us['delta']:.4f}")
g2.metric("Gamma (Γ)", f"{grecques_us['gamma']:.4f}")
g3.metric("Vega (𝒱 / +1 %)", f"{grecques_us['vega']:.4f} €")
g4.metric("Theta (Θ / jour)", f"{grecques_us['theta']:.4f} €")
g5.metric("Rho (ρ / +1 %)", f"{grecques_us['rho']:.4f} €")
st.caption("Δ, Γ et Θ extraits des premiers nœuds de l'arbre CRR · 𝒱 et ρ par différences finies centrées.")

# 4. Graphique de convergence selon N
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

# 5. Export CSV
contenu = io.StringIO()
tableau = csv.writer(contenu, delimiter=";")
tableau.writerow([
    "Exercice", "Type", "S_EUR", "K_EUR", "T_annees", "Taux_pct", "Volatilite_pct", "Pas_N",
    "Prix_US_EUR", "Prix_EU_EUR", "Prime_Anticipee_EUR",
    "Delta", "Gamma", "Vega_1pct_EUR", "Theta_jour_EUR", "Rho_1pct_EUR"
])
tableau.writerow([
    "Americaine", type_option, S, K, T, taux_pct, volatilite_pct, N,
    prix_us, prix_eu, prime_anticipee,
    grecques_us["delta"], grecques_us["gamma"], grecques_us["vega"], grecques_us["theta"], grecques_us["rho"]
])
st.download_button(
    "Télécharger le résultat (CSV)",
    data=contenu.getvalue().encode("utf-8-sig"),
    file_name="resultat_option_americaine.csv",
    mime="text/csv",
)
st.caption("À l’importation : séparateur point-virgule ; séparateur décimal point.")
