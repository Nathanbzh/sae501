# Accueil.py - VÉRIFIEZ CE FICHIER
# modif test git

import streamlit as st

# DÉFINITION INITIALE DES MODALITÉS POUR L'ADMINISTRATION
MODALITES_INITIALES = {
    # 1. L'ENTRETIEN
    "Mode d'entretien": ["RDV", "Sans RDV", "Téléphonique", "Courrier", "Mail", "Autre", "Non renseigné"],
    "Durée": ["- 15 min.", "15 à 30 min", "30 à 45 min", "45 à 60 min", "+ de 60 min"],
    
    # 2. L'USAGER (Variables modifiables)
    "Sexe": ["Homme", "Femme", "Couple", "Professionnel"],
    "Age": ["-18 ans", "18-25 ans", "26-40 ans", "41-60 ans", "+ 60 ans"],
    "Vient pour": ["Soi", "Conjoint", "Parent", "Enfant", "Personne morale", "Autre"],
    "Situtation familiale": ["Célibataire", "Concubin", "Pacsé", "Marié", "Séparé/divorcé", "Veuf/ve", "Non renseigné"],
    "Enfant(s) à charge": ["Sans enf. à charge", "Avec enf. en garde alternée", "Avec enf. en garde principale", "Avec enf. en droit de visite/hbgt", "Parent isolé", "Séparés sous le même toit", "Non renseigné"],
    "Profession": ["Scolaire/étudiant/formation", "Pêcheur/agriculteur", "Chef d'entreprise", "Libéral", "Secteur santé/social", "Militaire", "Employé", "Ouvrier", "Cadre", "Retraité", "En recherche d'emploi", "Sans profession", "Non renseigné"],
    "Revenus": ["Salaire", "Revenus pro.", "Retraite/réversion", "Allocations chômage", "RSA", "AAH/invalidité", "ASS", "Bourse d'études.", "Sans revenu"],
} # <--- Assurez-vous que cette accolade fermante est présente et correcte.

# Initialisation de la session state pour stocker toutes les modalités
if 'all_modalities' not in st.session_state:
    st.session_state.all_modalities = MODALITES_INITIALES
    
# --- Configuration de la Page d'Accueil ---

st.set_page_config(
    page_title="Accueil | Mon Application Statistique",
    layout="wide",
)

st.title("🏛️ Application de Gestion des Données d'Accès au Droit")
st.markdown("---")

st.markdown("""
### 🧭 Navigation

Utilisez la barre latérale à gauche pour naviguer entre les différentes fonctions :

* **1 Formulaire Saisie** : Enregistrer les données d'un nouvel entretien.
* **2 Analyse Graphique** : Visualiser les tendances, appliquer des filtres complexes et générer des graphiques personnalisés.
* **3 Administration** : Ajouter de nouvelles variables (colonnes) ou de nouvelles modalités aux variables existantes.
""")