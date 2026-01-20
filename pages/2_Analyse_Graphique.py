# pages/2_Analyse_Graphique.py
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_db_connection, get_translation_dictionary

st.set_page_config(layout="wide", page_title="Analyse Graphique")

@st.cache_data(ttl=60) # Cache court car les données changent
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
                # Mapping robuste (int vs str)
                df[col] = df[col].map(mapping).fillna(df[col])
        
        return df
    except Exception as e:
        st.error(f"Erreur data : {e}")
        return pd.DataFrame()

st.title("📊 Analyse Graphique")

df = load_and_prep_data()

if not df.empty:
    st.sidebar.header("Filtres")
    df_filtered = df.copy()
    excluded_cols = ['num', 'date_ent', 'mois']
    available_filters = [c for c in df.columns if c not in excluded_cols]
    
    filtres_actifs = st.sidebar.multiselect("Filtrer par :", available_filters)
    
    for col in filtres_actifs:
        valeurs = sorted(df[col].astype(str).unique())
        choix = st.sidebar.multiselect(f"{col}", valeurs)
        if choix:
            df_filtered = df_filtered[df_filtered[col].astype(str).isin(choix)]

    st.sidebar.metric("Dossiers", len(df_filtered))

    c1, c2, c3 = st.columns(3)
    type_graph = c1.selectbox("Type", ["Barres", "Camembert", "Courbe", "Treemap"])
    cols_x = [c for c in df.columns if c != 'num']
    var_x = c2.selectbox("Axe X / Groupe", cols_x, index=0)
    var_color = c3.selectbox("Couleur / Segment", ["Aucun"] + [c for c in cols_x if c != var_x])

    color_arg = None if var_color == "Aucun" else var_color

    if not df_filtered.empty:
        if type_graph == "Barres":
            data = df_filtered.groupby([var_x, color_arg] if color_arg else [var_x]).size().reset_index(name='Count')
            fig = px.bar(data, x=var_x, y='Count', color=color_arg, title=f"Répartition par {var_x}")
        elif type_graph == "Camembert":
            data = df_filtered.groupby(var_x).size().reset_index(name='Count')
            fig = px.pie(data, names=var_x, values='Count', title=f"Répartition {var_x}")
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
        with st.expander("Données brutes"):
            st.dataframe(df_filtered)
    else:
        st.info("Aucune donnée avec ces filtres.")
else:
    st.info("La base est vide.")