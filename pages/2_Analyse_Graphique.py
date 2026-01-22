# pages/2_Analyse_Graphique.py
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_db_connection, get_translation_dictionary

st.set_page_config(layout="wide", page_title="Analyse Graphique", page_icon="📊")

# --- AJOUT LOGO SIDEBAR ---
logo_path = "logo_mdd.png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=100)
st.sidebar.markdown("---")

@st.cache_data(ttl=60)
def load_and_prep_data():
    conn = get_db_connection()
    if not conn: return pd.DataFrame()
    
    try:
        query = "SELECT * FROM ENTRETIEN ORDER BY date_ent"
        df = pd.read_sql(query, conn)
        transco = get_translation_dictionary()
        conn.close()

        if df.empty: return df

        df.columns = [c.lower() for c in df.columns]
        if 'date_ent' in df.columns:
            df['date_ent'] = pd.to_datetime(df['date_ent'])
            df['mois'] = df['date_ent'].dt.strftime('%Y-%m')

        for col, mapping in transco.items():
            if col in df.columns:
                # 1. On remplace les codes par les libellés
                df[col] = df[col].map(mapping)
                # 2. IMPORTANT : On remplit les vides par une chaine vide pour éviter le mélange String/Float(NaN)
                df[col] = df[col].fillna("Non renseigné").astype(str)
        
        return df
    except Exception as e:
        st.error(f"Erreur data : {e}")
        return pd.DataFrame()

st.title("📊 Analyse Graphique")
st.markdown("---")

df = load_and_prep_data()

if not df.empty:
    # --- FILTRES EN SIDEBAR ---
    st.sidebar.header("🔍 Filtres")
    df_filtered = df.copy()
    excluded_cols = ['num', 'date_ent', 'mois']
    available_filters = [c for c in df.columns if c not in excluded_cols]
    
    filtres_actifs = st.sidebar.multiselect("Critères de filtrage :", available_filters)
    
    for col in filtres_actifs:
        valeurs = sorted(df[col].astype(str).unique())
        choix = st.sidebar.multiselect(f"{col}", valeurs)
        if choix:
            df_filtered = df_filtered[df_filtered[col].astype(str).isin(choix)]

    # --- KPI EN HAUT DE PAGE ---
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Dossiers", len(df))
    kpi2.metric("Dossiers Filtrés", len(df_filtered))
    
    pourcentage = (len(df_filtered)/len(df))*100 if len(df) > 0 else 0
    kpi3.metric("% du total", f"{pourcentage:.1f} %")
    
    st.markdown("---")

    # --- CONFIGURATION GRAPHIQUE ---
    with st.container():
        st.subheader("Visualisation")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            type_graph = st.selectbox("Type de graphique", ["Barres", "Camembert", "Courbe", "Treemap"])
        with c2:
            cols_x = [c for c in df.columns if c != 'num']
            var_x = st.selectbox("Axe X / Groupe principal", cols_x, index=0)
        with c3:
            var_color = st.selectbox("Segmentation (Couleur)", ["Aucun"] + [c for c in cols_x if c != var_x])

        color_arg = None if var_color == "Aucun" else var_color

        if not df_filtered.empty:
            if type_graph == "Barres":
                data = df_filtered.groupby([var_x, color_arg] if color_arg else [var_x]).size().reset_index(name='Count')
                fig = px.bar(data, x=var_x, y='Count', color=color_arg, title=f"Répartition par {var_x}", text_auto=True)
            elif type_graph == "Camembert":
                data = df_filtered.groupby(var_x).size().reset_index(name='Count')
                fig = px.pie(data, names=var_x, values='Count', title=f"Répartition {var_x}", hole=0.4)
            elif type_graph == "Courbe":
                grp = [var_x, color_arg] if color_arg else [var_x]
                data = df_filtered.groupby(grp).size().reset_index(name='Count').sort_values(var_x)
                fig = px.line(data, x=var_x, y='Count', color=color_arg, markers=True)
            elif type_graph == "Treemap":
                path = [var_x]
                if color_arg: path.append(color_arg)
                data = df_filtered.groupby(path).size().reset_index(name='Count')
                fig = px.treemap(data, path=path, values='Count')
            
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("🔎 Voir les données brutes correspondantes"):
                st.dataframe(df_filtered, use_container_width=True)
        else:
            st.warning("Aucune donnée avec ces filtres.")
else:
    st.info("La base de données est vide.")