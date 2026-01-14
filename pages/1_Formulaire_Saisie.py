# -*- coding: utf-8 -*-
import streamlit as st
import sys
import os

# --- CORRECTION DU CHEMIN ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_form_config, get_options_for_table, save_entretien_complet

def build_form():
    st.set_page_config(layout="wide", page_title="Saisie Entretien")
    st.title("Formulaire de Saisie")

    # 1. Chargement des configurations
    form_config = get_form_config()
    opts_demande = get_options_for_table('DEMANDE', 3)
    opts_solution = get_options_for_table('SOLUTION', 3)
    
    if not form_config:
        st.error("Impossible de charger la structure de la base de données.")
        return

    user_inputs = {}

    # --- TRI ET REGROUPEMENT DES CHAMPS ---
    fields_entretien = [f for f in form_config if f["section"] == "Entretien"]
    sections_usager_etendu = ["Usager", "Repérage du dispositif", "Résidence", "Partenaire"]
    fields_usager = [f for f in form_config if f["section"] in sections_usager_etendu]

    # --- FONCTION D'AFFICHAGE DYNAMIQUE ---
    def render_field(field, col):
        col_name = field["column_name"]
        label = field["label"] if field["label"] else col_name
        
        if col_name in ['NUM', 'DATE_ENT']:
            return

        with col:
            if field["options"]:
                options_map = field["options"]
                list_labels = list(options_map.keys())
                
                if len(list_labels) < 6:
                    val = st.radio(label, list_labels, key=col_name, index=None) 
                    user_inputs[col_name] = options_map[val] if val else None
                else:
                    options_display = ["Sélectionner"] + list_labels
                    choice = st.selectbox(label, options_display, key=col_name)
                    user_inputs[col_name] = options_map[choice] if choice != "Sélectionner" else None
            
            elif field["type"] == 'NUM':
                user_inputs[col_name] = st.number_input(label, step=1, key=col_name)
            else:
                user_inputs[col_name] = st.text_input(label, key=col_name)

    # ==========================================
    # 1. BLOC ENTRETIEN
    # ==========================================
    st.subheader("1. L'ENTRETIEN")
    c_ent_1, c_ent_2 = st.columns(2)
    
    for i, field in enumerate(fields_entretien):
        col = c_ent_1 if i % 2 == 0 else c_ent_2
        render_field(field, col)

    st.markdown("---")

    # ==========================================
    # 2. BLOC USAGER
    # ==========================================
    st.subheader("2. L'USAGER & CONTEXTE")
    cols_usager = st.columns(3)
    
    for i, field in enumerate(fields_usager):
        col = cols_usager[i % 3]
        render_field(field, col)

    st.markdown("---")

    # ==========================================
    # 3. BLOC DETAILS
    # ==========================================
    st.subheader("3. DETAILS DU DOSSIER")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.info("**Nature(s) de la demande**")
        selected_demandes_labels = st.multiselect(
            "Sélectionnez une ou plusieurs demandes",
            options=list(opts_demande.keys()),
            label_visibility="collapsed"
        )
        selected_demandes_codes = [opts_demande[lbl] for lbl in selected_demandes_labels]

    with c2:
        st.success("**Solution(s) apportée(s)**")
        selected_solutions_labels = st.multiselect(
            "Sélectionnez une ou plusieurs solutions",
            options=list(opts_solution.keys()),
            label_visibility="collapsed"
        )
        selected_solutions_codes = [opts_solution[lbl] for lbl in selected_solutions_labels]

    # ==========================================
    # 4. ENREGISTREMENT
    # ==========================================
    st.markdown("---")
    submitted = st.button("Enregistrer le dossier complet", type="primary", use_container_width=True)

    if submitted:
        if user_inputs.get("MODE") is None:
            st.warning("Le champ 'Mode de l'entretien' est requis (Section Entretien).")
        elif not selected_demandes_codes:
            st.warning("Veuillez sélectionner au moins une nature de demande.")
        else:
            try:
                new_num = save_entretien_complet(
                    user_inputs, 
                    selected_demandes_codes, 
                    selected_solutions_codes
                )
                
                st.success(f"Dossier complet n° **{new_num}** enregistré avec succès !")
                
                if st.button("Nouvelle saisie"):
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Erreur lors de l'enregistrement : {e}")

if __name__ == "__main__":
    build_form()