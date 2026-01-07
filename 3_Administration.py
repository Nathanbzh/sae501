# pages/3_Administration.py

import streamlit as st
import pandas as pd

def administration_page():
    st.set_page_config(layout="wide")
    st.title("⚙️ Administration des Variables et Modalités")
    st.markdown("---")

    # Vérifiez que les modalités sont initialisées
    if 'all_modalities' not in st.session_state:
        st.error("⚠️ Erreur : La structure des modalités n'a pas été initialisée (Veuillez recharger la page d'accueil).")
        return

    # Utilisation d'onglets pour séparer l'affichage et la gestion
    tab_gestion, tab_apercu = st.tabs(["🔨 Gérer les Variables", "📖 Aperçu Actuel"])
    
    # --- Onglet Gérer les Variables ---
    with tab_gestion:
        st.header("Que souhaitez-vous ajouter ?")
        
        type_ajout = st.radio(
            "**Choisir l'élément à ajouter :**",
            options=["Nouvelle Modalité (à une variable existante)", "Nouvelle Colonne (variable)"],
            horizontal=True
        )
        
        st.markdown("---")

        if type_ajout == "Nouvelle Colonne (variable)":
            ## --- AJOUT D'UNE NOUVELLE COLONNE (VARIABLE) ---
            
            st.subheader("Création d'une nouvelle Variable/Colonne")
            
            with st.form("form_add_column"):
                new_col_name = st.text_input("**Nom de la nouvelle Colonne (ex: 'Situation Sociale')**")
                
                modalities_input = st.text_area(
                    "**Modalités de cette colonne (une par ligne)**",
                    help="Entrez chaque option de la nouvelle variable sur une nouvelle ligne."
                )
                
                submitted_col = st.form_submit_button("Ajouter la Colonne")
                
                if submitted_col:
                    if not new_col_name:
                        st.error("Le nom de la colonne ne peut pas être vide.")
                    else:
                        modalities_list = [m.strip() for m in modalities_input.split('\n') if m.strip()]
                        
                        if not modalities_list:
                            st.warning("Veuillez entrer au moins une modalité pour la nouvelle colonne.")
                        else:
                            new_col_key = new_col_name.strip()
                            if new_col_key in st.session_state.all_modalities:
                                st.error(f"La colonne '{new_col_key}' existe déjà. Veuillez choisir un autre nom.")
                            else:
                                st.session_state.all_modalities[new_col_key] = modalities_list
                                st.success(f"✔️ Colonne **'{new_col_key}'** et ses {len(modalities_list)} modalités ajoutées avec succès !")
                                # Utilisation de st.rerun()
                                st.rerun() 
                                
        elif type_ajout == "Nouvelle Modalité (à une variable existante)":
            ## --- AJOUT D'UNE NOUVELLE MODALITÉ ---
            
            st.subheader("Ajout d'une Modalité à une Variable Existante")
            
            existing_vars = list(st.session_state.all_modalities.keys())
            
            with st.form("form_add_modality"):
                var_selected = st.selectbox(
                    "**Choisir la Variable :**",
                    options=existing_vars
                )
                
                new_modality = st.text_input("**Nom de la nouvelle Modalité :**")
                
                submitted_mod = st.form_submit_button("Ajouter la Modalité")
                
                if submitted_mod:
                    if not new_modality:
                        st.error("Le nom de la modalité ne peut pas être vide.")
                    elif new_modality.strip() in st.session_state.all_modalities[var_selected]:
                        st.warning(f"La modalité '{new_modality.strip()}' existe déjà dans '{var_selected}'.")
                    else:
                        st.session_state.all_modalities[var_selected].append(new_modality.strip())
                        st.success(f"✔️ Modalité **'{new_modality.strip()}'** ajoutée à la variable **'{var_selected}'**.")
                        # Utilisation de st.rerun()
                        st.rerun() 
                        
    # --- Onglet Aperçu Actuel ---
    with tab_apercu:
        st.header("Aperçu de la Structure de Données Actuelle")
        
        data_to_display = []
        for col, mods in st.session_state.all_modalities.items():
            data_to_display.append({
                "Nom de la Colonne (Variable)": col,
                "Nombre de Modalités": len(mods),
                "Modalités": ", ".join(mods)
            })
            
        st.dataframe(pd.DataFrame(data_to_display), use_container_width=True)


# Exécuter la fonction de la page d'administration
administration_page()