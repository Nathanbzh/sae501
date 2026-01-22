# Accueil.py
# -*- coding: utf-8 -*-
import streamlit as st
import sys
import os
from PIL import Image
import datetime

# --- CORRECTION DU CHEMIN POUR IMPORTS ---
sys.path.append(os.path.dirname(__file__))
from database import get_form_config, get_options_for_table, save_entretien_complet

def build_home():
    st.set_page_config(
        page_title="Maison du Droit - Accueil & Saisie", 
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- CSS PERSONNALISÉ POUR LE STYLE ---
    st.markdown("""
        <style>
        .big-font { font-size:20px !important; }
        .card {
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 10px;
        }
        .main-header {
            font-size: 2.5rem;
            color: #2E4053;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- EN-TÊTE AVEC LOGO ---
    col_logo, col_titre = st.columns([1, 5])

    with col_logo:
        logo_path = "pages/logo_mdd.png"
        if os.path.exists(logo_path):
            image = Image.open(logo_path)
            st.image(image, width=130)
        else:
            st.info("🏛️") # Fallback icône si pas d'image

    with col_titre:
        st.markdown('<h1 class="main-header">Maison du Droit</h1>', unsafe_allow_html=True)
        st.caption("Gestion administrative, Saisie des entretiens et Suivi statistique")

    st.markdown("---")

    # --- ACCÈS RAPIDE AUX AUTRES PAGES (ADMIN / STATS) ---
    with st.expander("🧭 Accès Rapide aux autres modules", expanded=False):
        c1, c2, c3 = st.columns(3)
        # Utilisation sécurisée de page_link pour éviter les crashs dans les tests AppTest
        # (AppTest ne gère pas toujours bien le contexte de navigation multipages)
        try:
            with c1:
                st.page_link("pages/2_Analyse_Graphique.py", label="📊 Voir les Statistiques", icon="📈", use_container_width=True)
            with c2:
                st.page_link("pages/3_Export_Donnees.py", label="📥 Exporter les Données", icon="💾", use_container_width=True)
            with c3:
                st.page_link("pages/4_Administration.py", label="⚙️ Administration BDD", icon="🔧", use_container_width=True)
        except Exception:
            st.warning("⚠️ Navigation désactivée en mode test (AppTest)")
    
    st.markdown("---")

    # =========================================================================
    # FORMULAIRE DE SAISIE (INTÉGRÉ SUR LA PAGE D'ACCUEIL)
    # =========================================================================
    st.header("📝 Nouvel Entretien")
    st.info("Remplissez ce formulaire pour enregistrer un nouveau passage usager.")

    # 1. Chargement de la configuration dynamique depuis la BDD
    form_config = get_form_config()
    if not form_config:
        st.error("❌ Erreur technique : Impossible de charger la structure du formulaire depuis la base de données.")
        return

    # Chargement des listes déroulantes pour les demandes/solutions
    opts_demande = get_options_for_table('DEMANDE', 3)
    opts_solution = get_options_for_table('SOLUTION', 3)

    user_inputs = {}

    # --- TRI ET REGROUPEMENT DES CHAMPS ---
    fields_entretien = [f for f in form_config if f["section"] == "Entretien"]
    fields_usager = [f for f in form_config if f["section"] != "Entretien"]

    # Fonction locale pour afficher un champ (Selectbox, Text, Number)
    def render_field(field, col):
        col_name = field["column_name"]
        label = field["label"] if field["label"] else col_name
        
        # Ignorer les champs techniques
        if col_name in ['NUM', 'DATE_ENT']:
            return

        with col:
            if field["options"]:
                options_map = field["options"]
                list_labels = list(options_map.keys())
                
                # Radio pour les petits choix, Selectbox pour les grands
                if len(list_labels) < 5:
                    val = st.radio(label, list_labels, key=f"in_{col_name}", index=None, horizontal=True) 
                    user_inputs[col_name] = options_map[val] if val else None
                else:
                    options_display = ["Sélectionner"] + list_labels
                    choice = st.selectbox(label, options_display, key=f"in_{col_name}")
                    user_inputs[col_name] = options_map[choice] if choice != "Sélectionner" else None
            
            elif field["type"] == 'NUM':
                user_inputs[col_name] = st.number_input(label, step=1, min_value=0, key=f"in_{col_name}")
            else:
                user_inputs[col_name] = st.text_input(label, key=f"in_{col_name}")

    # --- BLOC 1 : CARACTÉRISTIQUES DE L'ENTRETIEN ---
    st.subheader("1. L'Entretien")
    c_ent_1, c_ent_2 = st.columns(2)
    for i, field in enumerate(fields_entretien):
        render_field(field, c_ent_1 if i % 2 == 0 else c_ent_2)

    # --- BLOC 2 : PROFIL USAGER ---
    st.subheader("2. L'Usager")
    cols_usager = st.columns(3)
    for i, field in enumerate(fields_usager):
        render_field(field, cols_usager[i % 3])

    st.markdown("---")

    # --- BLOC 3 : DÉTAILS JURIDIQUES ---
    st.subheader("3. Détails du Dossier")
    
    c_dem, c_sol = st.columns(2)
    
    with c_dem:
        st.markdown("##### ❓ Nature de la demande")
        selected_demandes_labels = st.multiselect(
            "Sélectionnez une ou plusieurs qualifications :",
            options=list(opts_demande.keys()),
            label_visibility="collapsed",
            key="multi_demandes"
        )
        selected_demandes_codes = [opts_demande[lbl] for lbl in selected_demandes_labels]

    with c_sol:
        st.markdown("##### 💡 Réponse / Orientation")
        selected_solutions_labels = st.multiselect(
            "Sélectionnez la ou les réponses apportées :",
            options=list(opts_solution.keys()),
            label_visibility="collapsed",
            key="multi_solutions"
        )
        selected_solutions_codes = [opts_solution[lbl] for lbl in selected_solutions_labels]

    # --- BOUTON D'ACTION ---
    st.markdown("---")
    col_submit, _ = st.columns([1, 4])
    
    with col_submit:
        submitted = st.button("💾 Enregistrer le dossier", type="primary", use_container_width=True)

    if submitted:
        # Validation minimale
        # On peut adapter les règles selon vos besoins (ex: Mode obligatoire)
        is_valid = True
        
        # Exemple de règle : Si "Mode" est une colonne configurée et qu'elle est vide
        if "MODE" in user_inputs and user_inputs["MODE"] is None:
             st.warning("⚠️ Le champ 'Mode de l'entretien' est requis.")
             is_valid = False
        
        if not selected_demandes_codes:
            st.warning("⚠️ Veuillez qualifier au moins une 'Nature de la demande'.")
            is_valid = False

        if is_valid:
            try:
                new_num = save_entretien_complet(
                    user_inputs, 
                    selected_demandes_codes, 
                    selected_solutions_codes
                )
                
                st.success(f"✅ Dossier complet n° **{new_num}** enregistré avec succès !")
                # st.balloons() # Désactivé pour rester sobre (et ne pas gêner les tests)
                
                # Bouton pour recharger la page et vider le formulaire
                if st.button("Saisir un nouveau dossier"):
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de l'enregistrement en base : {e}")

if __name__ == "__main__":
    build_home()