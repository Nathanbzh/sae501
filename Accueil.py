import streamlit as st
import os

# --- Configuration de la Page d'Accueil ---
st.set_page_config(
    page_title="Accueil | Application de Gestion",
    layout="wide",
)

# Initialisation de la session (si nécessaire pour d'autres parties)
if 'all_modalities' not in st.session_state:
    st.session_state.all_modalities = {}

# --- EN-TÊTE AVEC LOGO ---
col_logo, col_titre = st.columns([1, 4])

with col_logo:
    # REMPLACE 'logo.png' PAR LE NOM DE TON FICHIER IMAGE
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    else:
        # Placeholder si l'image n'est pas encore là
        st.info("Logo ici")

with col_titre:
    st.title("Application de Gestion des Données d'Accès au Droit")

st.markdown("---")

# --- PRÉSENTATION DE LA MAISON DU DROIT ---
st.header("Bienvenue à la Maison du Droit")

st.markdown("""
La **Maison du Droit et de la Justice** est un lieu d'accueil, d'écoute et d'information gratuit et confidentiel. 
Elle a pour vocation de rapprocher la justice des citoyens et de faciliter l'accès au droit pour tous.

Nos missions principales sont :
* **L'accès au droit** : Informer les citoyens sur leurs droits et obligations et les orienter vers les interlocuteurs compétents.
* **La résolution amiable des conflits** : Proposer des alternatives aux poursuites judiciaires (médiation, conciliation).
* **L'aide aux victimes** : Apporter un soutien juridique et psychologique.

Cette application est l'outil central permettant à notre équipe de suivre l'activité, d'enregistrer les entretiens et d'analyser les statistiques de fréquentation afin de mieux répondre aux besoins des usagers.
""")

st.markdown("---")

# --- NAVIGATION ---
st.subheader("Navigation")

st.markdown("""
Utilisez la barre latérale à gauche pour accéder aux fonctionnalités :

* **1 Formulaire Saisie** : Enregistrer un nouvel entretien et les détails du dossier usager.
* **2 Analyse Graphique** : Consulter les statistiques et visualiser les données d'activité.
* **3 Administration** : Gérer les paramètres de l'application.
""")