import streamlit as st

st.set_page_config(page_title="Pricer d'Options — Accueil", page_icon="📈", layout="wide")


def page_accueil():
    st.title("Pricer d'options — Européennes & Américaines")
    st.caption("Application de valorisation et de gestion des risques · M2 Gestion de Portefeuille")

    st.markdown(
        """
        Cette application permet de valoriser des options vanilles (**Call** et **Put**) sans dividendes,
        d'analyser leurs sensibilités (**Grecques**) et de visualiser leur profil de risque.
        """
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🇪🇺 Options Européennes")
        st.write("Valorisation analytique exacte via le modèle de **Black-Scholes-Merton** et calcul fermé des 5 Grecques.")
        st.page_link("pages/1_Options_Europeennes.py", label="Ouvrir le pricer européen", icon="➡️")

    with col2:
        st.subheader("🇺🇸 Options Américaines")
        st.write("Valorisation numérique via l'arbre binomial de **Cox-Ross-Rubinstein (CRR)**, prime d'exercice anticipé et Grecques numériques.")
        st.page_link("pages/2_Options_Americaines.py", label="Ouvrir le pricer américain", icon="➡️")


navigation = st.navigation(
    [
        st.Page(page_accueil, title="Page d'accueil", icon="🏠", default=True),
        st.Page("pages/1_Options_Europeennes.py", title="Options Européennes", icon="🇪🇺"),
        st.Page("pages/2_Options_Americaines.py", title="Options Américaines", icon="🇺🇸"),
    ]
)
navigation.run()
