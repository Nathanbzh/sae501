# pages/4_Administration.py
import streamlit as st
import pandas as pd
import sys
import os

# --- IMPORT BDD ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import (
    get_form_config, 
    add_new_variable_db, 
    add_new_modality_db, 
    get_rubriques
)

def administration_page():
    st.set_page_config(layout="wide", page_title="Administration BDD")
    st.title("⚙️ Administration Base de Données")
    st.markdown("---")
    
    st.warning("⚠️ **Attention** : Les modifications ici impactent directement la structure de la base de données (table ENTRETIEN).")

    # Chargement de la config actuelle
    current_config = get_form_config()
    if not current_config:
        st.error("Impossible de charger la configuration actuelle.")
        return

    tab_gestion, tab_apercu = st.tabs(["🔨 Gérer les Variables", "📖 Aperçu Structure"])
    
    # --- Onglet Gérer ---
    with tab_gestion:
        action = st.radio("Action :", ["Ajouter une Modalité", "Créer une nouvelle Variable (Colonne)"], horizontal=True)
        st.markdown("---")

        # 1. AJOUT DE MODALITÉ
        if action == "Ajouter une Modalité":
            st.subheader("Ajouter une option à une liste existante")
            
            # On ne garde que les champs de type 'MOD' (Liste de choix)
            vars_mod = [f for f in current_config if f['type'] == 'MOD']
            dict_vars = {f"{f['label']} ({f['column_name']})": f for f in vars_mod}
            
            selected_label = st.selectbox("Choisir la variable :", list(dict_vars.keys()))
            
            if selected_label:
                target_field = dict_vars[selected_label]
                st.info(f"Modalités actuelles : {', '.join(list(target_field['options'].keys()))}")
                
                with st.form("add_mod_form"):
                    new_mod_name = st.text_input("Nom de la nouvelle modalité :")
                    submit_mod = st.form_submit_button("Ajouter")
                    
                    if submit_mod:
                        if not new_mod_name:
                            st.error("Le nom ne peut pas être vide.")
                        elif new_mod_name in target_field['options']:
                            st.error("Cette modalité existe déjà.")
                        else:
                            try:
                                add_new_modality_db(target_field['id'], new_mod_name)
                                st.success(f"Modalité '{new_mod_name}' ajoutée avec succès !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur BDD : {e}")

        # 2. AJOUT DE VARIABLE
        elif action == "Créer une nouvelle Variable (Colonne)":
            st.subheader("Créer un nouveau champ dans le formulaire")
            
            rubriques = get_rubriques() # [(id, lib), ...]
            rub_dict = {lib: id_r for id_r, lib in rubriques}
            
            with st.form("add_col_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_label = st.text_input("Libellé (Question posée) :", placeholder="Ex: Situation maritale")
                    new_col_name = st.text_input("Nom technique (Colonne SQL) :", placeholder="Ex: SITUATION_MARITALE")
                
                with col2:
                    target_rub = st.selectbox("Section du formulaire :", list(rub_dict.keys()))
                    type_input = st.selectbox("Type de réponse :", ["Liste de choix (MOD)", "Texte libre (CHAINE)", "Nombre (NUM)"])
                
                mods_input = ""
                if type_input == "Liste de choix (MOD)":
                    mods_input = st.text_area("Options (une par ligne) :", placeholder="Célibataire\nMarié(e)\nDivorcé(e)")

                submitted_col = st.form_submit_button("Créer la variable")

                if submitted_col:
                    if not new_label or not new_col_name:
                        st.error("Le libellé et le nom technique sont obligatoires.")
                    else:
                        # Mapping type UI -> Type BDD
                        type_db = 'MOD' if 'MOD' in type_input else ('NUM' if 'NUM' in type_input else 'CHAINE')
                        rub_id = rub_dict[target_rub]
                        
                        # Parsing modalités
                        liste_mods = []
                        if type_db == 'MOD':
                            liste_mods = [m.strip() for m in mods_input.split('\n') if m.strip()]
                            if not liste_mods:
                                st.error("Pour une liste de choix, il faut au moins une option.")
                                st.stop()

                        try:
                            add_new_variable_db(new_col_name, new_label, type_db, rub_id, liste_mods)
                            st.success(f"Variable '{new_label}' créée avec succès !")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de la création : {e}")

    # --- Onglet Aperçu ---
    with tab_apercu:
        st.write("Liste des champs configurés dans la base :")
        df_preview = pd.DataFrame(current_config)
        # Nettoyage pour affichage
        if not df_preview.empty:
            df_preview['nb_options'] = df_preview['options'].apply(lambda x: len(x))
            st.dataframe(
                df_preview[['column_name', 'label', 'type', 'section', 'nb_options']], 
                use_container_width=True
            )

administration_page()