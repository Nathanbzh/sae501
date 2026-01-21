# pages/3_Export_Donnees.py

import streamlit as st
import pandas as pd
import io
import sys
import os
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import (
    get_db_connection, 
    get_translation_dictionary, 
    get_recent_dossiers_list, 
    get_dossier_complete_data,
    get_options_for_table
)

st.set_page_config(layout="wide", page_title="Données & Export", page_icon="📥")

logo_path = "logo_mdd.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=100)

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

st.title("📥 Données & Archives")
st.markdown("---")

# CRÉATION DES ONGLETS AVEC ICONES
tab_export, tab_detail = st.tabs(["📊 Export Global (Excel)", "🔍 Détail Dossier"])

# =========================================================
# ONGLET 1 : EXPORT GLOBAL
# =========================================================
with tab_export:
    st.info("Sélectionnez une période pour générer un fichier Excel complet.")
    
    col_filter, col_action = st.columns([3, 1])
    
    with col_filter:
        liste_mois = get_available_months()
        if not liste_mois:
            st.warning("Aucune donnée disponible.")
            selected_months = []
        else:
            selected_months = st.multiselect("Mois à exporter :", options=liste_mois, default=liste_mois[:1])

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

                    st.dataframe(df, use_container_width=True, height=300)
                    
                    excel_data = to_excel(df)
                    
                    with col_action:
                        st.write("Action :")
                        st.download_button(
                            "📥 Télécharger Excel", 
                            data=excel_data, 
                            file_name=f"export_mdd_{selected_months[0]}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                else:
                    st.info("Aucune donnée pour cette période.")
            except Exception as e:
                st.error(f"Erreur: {e}")
                if conn: conn.close()

# =========================================================
# ONGLET 2 : DÉTAIL DOSSIER
# =========================================================
with tab_detail:
    c1, c2 = st.columns([2, 1])
    
    recent_dossiers = get_recent_dossiers_list(limit=50) 
    dict_dossiers = {num: f"N° {num} du {date_ent}" for num, date_ent in recent_dossiers}
    
    selected_num = None
    
    with c1:
        choix_recent = st.selectbox(
            "Sélectionner un dossier récent :", 
            options=list(dict_dossiers.keys()), 
            format_func=lambda x: dict_dossiers[x]
        )
    
    with c2:
        input_num = st.number_input("Recherche par N° :", min_value=0, value=0, step=1)
    
    if input_num > 0:
        selected_num = input_num
    else:
        selected_num = choix_recent

    st.markdown("---")

    if selected_num:
        st.subheader(f"📁 Dossier N° {selected_num}")
        
        df_ent, df_dem, df_sol = get_dossier_complete_data(selected_num)
        
        if df_ent.empty:
            st.error(f"Le dossier n°{selected_num} n'existe pas.")
        else:
            # --- A. TABLE ENTRETIEN ---
            transco_ent = get_translation_dictionary()
            df_ent.columns = [c.lower() for c in df_ent.columns]
            
            for col, mapping in transco_ent.items():
                if col in df_ent.columns:
                    df_ent[col] = df_ent[col].map(mapping).fillna(df_ent[col])
            
            with st.container():
                st.markdown("#### 👤 Informations Usager")
                st.dataframe(df_ent, use_container_width=True, hide_index=True)
            
            opts_demande = get_options_for_table('DEMANDE')
            map_demande = {v: k for k, v in opts_demande.items()}
            
            opts_solution = get_options_for_table('SOLUTION')
            map_solution = {v: k for k, v in opts_solution.items()}

            c_left, c_right = st.columns(2)

            with c_left:
                st.markdown("#### ❓ Demandes")
                if not df_dem.empty:
                    df_dem.columns = [c.lower() for c in df_dem.columns]
                    if 'nature' in df_dem.columns:
                        df_dem['nature'] = df_dem['nature'].map(map_demande).fillna(df_dem['nature'])
                    st.dataframe(df_dem[['pos', 'nature']], use_container_width=True, hide_index=True)
                else:
                    st.info("Aucune demande.")

            with c_right:
                st.markdown("#### 💡 Solutions")
                if not df_sol.empty:
                    df_sol.columns = [c.lower() for c in df_sol.columns]
                    if 'nature' in df_sol.columns:
                        df_sol['nature'] = df_sol['nature'].map(map_solution).fillna(df_sol['nature'])
                    st.dataframe(df_sol[['pos', 'nature']], use_container_width=True, hide_index=True)
                else:
                    st.info("Aucune solution.")