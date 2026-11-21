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
