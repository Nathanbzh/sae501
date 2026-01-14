# pages/3_Export_Donnees.py

import streamlit as st
import pandas as pd
import io
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import (
    get_db_connection, 
    get_translation_dictionary, 
    get_recent_dossiers_list, 
    get_dossier_complete_data,
    get_options_for_table
)

st.set_page_config(layout="wide", page_title="Données & Export")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Données')
        worksheet = writer.sheets['Données']
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)
    return output.getvalue()

def get_available_months():
    conn = get_db_connection()
    months = []
    if conn:
        try:
            query = "SELECT DISTINCT TO_CHAR(date_ent, 'YYYY-MM') as mois FROM ENTRETIEN ORDER BY mois DESC"
            df = pd.read_sql(query, conn)
            months = df['mois'].tolist()
        except Exception: pass
        finally: conn.close()
    return months

# --- INTERFACE ---
st.title("Données & Archives")

# CRÉATION DES ONGLETS
tab_export, tab_detail = st.tabs(["Export Global (Par Mois)", "Détail Dossier (Demandes & Solutions)"])

# =========================================================
# ONGLET 1 : EXPORT GLOBAL
# =========================================================
with tab_export:
    st.markdown("### Export des entretiens par période")
    
    with st.spinner("Chargement des périodes..."):
        liste_mois = get_available_months()

    if not liste_mois:
        st.warning("Aucune donnée disponible.")
    else:
        with st.expander("Sélectionner la période", expanded=True):
            selected_months = st.multiselect("Mois :", options=liste_mois)

        if selected_months:
            conn = get_db_connection()
            if conn:
                try:
                    query = "SELECT * FROM ENTRETIEN WHERE TO_CHAR(date_ent, 'YYYY-MM') = ANY(%s) ORDER BY date_ent DESC"
                    df = pd.read_sql(query, conn, params=(selected_months,))
                    transco = get_translation_dictionary()
                    conn.close()

                    if not df.empty:
                        df.columns = [c.lower() for c in df.columns]
                        if 'date_ent' in df.columns:
                            df['date_ent'] = pd.to_datetime(df['date_ent']).dt.date
                        
                        for col, mapping in transco.items():
                            if col in df.columns:
                                df[col] = df[col].map(mapping).fillna(df[col])

                        st.dataframe(df, use_container_width=True)
                        
                        excel_data = to_excel(df)
                        st.download_button(
                            "Télécharger Excel", 
                            data=excel_data, 
                            file_name="export_entretiens.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.info("Aucune donnée.")
                except Exception as e:
                    st.error(f"Erreur: {e}")
                    if conn: conn.close()

# =========================================================
# ONGLET 2 : DÉTAIL DOSSIER
# =========================================================
with tab_detail:
    st.markdown("### Consultation complète d'un dossier")
    
    # 1. Barre de recherche : Liste déroulante + Recherche manuelle
    c1, c2 = st.columns([2, 1])
    
    # Récupération des 50 derniers dossiers pour faciliter le choix
    recent_dossiers = get_recent_dossiers_list(limit=50) # [(num, date), ...]
    dict_dossiers = {num: f"N° {num} du {date_ent}" for num, date_ent in recent_dossiers}
    
    selected_num = None
    
    with c1:
        # Selectbox affichant les récents
        choix_recent = st.selectbox(
            "Sélectionner un dossier récent :", 
            options=list(dict_dossiers.keys()), 
            format_func=lambda x: dict_dossiers[x]
        )
    
    with c2:
        # Input manuel si le dossier est vieux et pas dans la liste
        input_num = st.number_input("Ou chercher par N° précis :", min_value=0, value=0, step=1)
    
    # Priorité à la recherche manuelle si remplie, sinon le choix de la liste
    if input_num > 0:
        selected_num = input_num
    else:
        selected_num = choix_recent

    st.divider()

    # 2. Affichage des données
    if selected_num:
        st.subheader(f"Dossier N° {selected_num}")
        
        # Récupération des 3 tables
        df_ent, df_dem, df_sol = get_dossier_complete_data(selected_num)
        
        if df_ent.empty:
            st.error(f"Le dossier n°{selected_num} n'existe pas.")
        else:
            # --- A. TABLE ENTRETIEN (Info principale) ---
            # Traduction
            transco_ent = get_translation_dictionary()
            df_ent.columns = [c.lower() for c in df_ent.columns]
            
            # Application traduction
            for col, mapping in transco_ent.items():
                if col in df_ent.columns:
                    df_ent[col] = df_ent[col].map(mapping).fillna(df_ent[col])
            
            st.info("**Informations Générales (Table ENTRETIEN)**")
            st.dataframe(df_ent, use_container_width=True, hide_index=True)
            
            # Préparation des dictionnaires de traduction inversés pour Demande/Solution
            # get_options_for_table renvoie {Libellé: Code}, on veut {Code: Libellé}
            opts_demande = get_options_for_table('DEMANDE')
            map_demande = {v: k for k, v in opts_demande.items()}
            
            opts_solution = get_options_for_table('SOLUTION')
            map_solution = {v: k for k, v in opts_solution.items()}

            c_left, c_right = st.columns(2)

            # --- B. TABLE DEMANDE ---
            with c_left:
                st.warning("**Demandes (Table DEMANDE)**")
                if not df_dem.empty:
                    df_dem.columns = [c.lower() for c in df_dem.columns]
                    # Traduction de la colonne 'nature'
                    if 'nature' in df_dem.columns:
                        df_dem['nature'] = df_dem['nature'].map(map_demande).fillna(df_dem['nature'])
                    
                    st.dataframe(df_dem[['pos', 'nature']], use_container_width=True, hide_index=True)
                else:
                    st.markdown("*Aucune demande enregistrée.*")

            # --- C. TABLE SOLUTION ---
            with c_right:
                st.success("**Solutions (Table SOLUTION)**")
                if not df_sol.empty:
                    df_sol.columns = [c.lower() for c in df_sol.columns]
                    # Traduction de la colonne 'nature'
                    if 'nature' in df_sol.columns:
                        df_sol['nature'] = df_sol['nature'].map(map_solution).fillna(df_sol['nature'])
                    
                    st.dataframe(df_sol[['pos', 'nature']], use_container_width=True, hide_index=True)
                else:
                    st.markdown("*Aucune solution enregistrée.*")