import streamlit as st

st.set_page_config(page_title="Pricer d'options", page_icon="📈", layout="wide")

st.title("Pricer d’options vanilles")
st.caption("Projet de mathématiques financières · M2 Gestion de portefeuille · Sans dividendes")

st.markdown("""
Cette application permet de valoriser des options vanilles (**Call** et **Put**) et d'analyser leur sensibilité au cours du sous-jacent selon deux approches :
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Options Européennes")
    st.write("Valorisation analytique exacte par la formule fermée de **Black-Scholes-Merton** (exercice uniquement à maturité $T$).")
    st.page_link("pages/1_Options_Europeennes.py", label="Ouvrir le pricer européen", icon="🇪🇺")

with col2:
    st.subheader("Options Américaines")
    st.write("Valorisation numérique par **arbre binomial de Cox-Ross-Rubinstein (CRR)** (exercice anticipé autorisé et calcul de la prime d'exercice anticipé).")
    st.page_link("pages/2_Options_Americaines.py", label="Ouvrir le pricer américain", icon="🇺🇸")
