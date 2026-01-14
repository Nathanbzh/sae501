# pages/2_Analyse_Graphique.py

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Import de la bdd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import get_db_connection, get_translation_dictionary

st.set_page_config(layout="wide", page_title="Analyse Graphique")

# Fonction mise en cache pour éviter de recharger la BDD à chaque clic
@st.cache_data(ttl=300)
def load_and_prep_data():
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # On charge toute la table
        query = "SELECT * FROM ENTRETIEN ORDER BY date_ent"
        df = pd.read_sql(query, conn)
        
        # On charge le dictionnaire de traduction
        transco = get_translation_dictionary()
        conn.close()

        if df.empty:
            return df

        # --- PREPARATION DES DONNEES ---
        
        # 1. Noms de colonnes en minuscules
        df.columns = [c.lower() for c in df.columns]

        # 2. Gestion des dates
        if 'date_ent' in df.columns:
            df['date_ent'] = pd.to_datetime(df['date_ent'])
            # Création d'une colonne 'Mois' (ex: "2024-01") utile pour les graphiques temporels
            df['mois'] = df['date_ent'].dt.strftime('%Y-%m')

        # 3. Application des traductions (Codes -> Libellés)
        for col, mapping in transco.items():
            if col in df.columns:
                df[col] = df[col].map(mapping).fillna(df[col])
        
        return df

    except Exception as e:
        st.error(f"Erreur de chargement des données : {e}")
        return pd.DataFrame()

# --- PAGE PRINCIPALE ---

st.title("📊 Analyse Graphique Dynamique")
st.markdown("Explorez les données en choisissant vos filtres et vos variables.")

# Chargement
with st.spinner("Chargement des données..."):
    df = load_and_prep_data()

if not df.empty:
    
    # --- 1. BARRE LATÉRALE : FILTRES ---
    st.sidebar.header("🔍 Filtres")
    
    # Copie du DF pour filtrage progressif
    df_filtered = df.copy()
    
    # Liste des colonnes filtrables (on retire les IDs techniques)
    excluded_cols = ['num', 'date_ent']
    available_filters = [c for c in df.columns if c not in excluded_cols]
    
    # L'utilisateur choisit d'abord SUR QUOI il veut filtrer
    # Cela évite d'afficher 20 listes déroulantes d'un coup
    filtres_actifs = st.sidebar.multiselect("Ajouter un filtre sur :", available_filters)
    
    # Pour chaque filtre choisi, on affiche les valeurs possibles
    for col in filtres_actifs:
        # Récupère les valeurs uniques triées
        valeurs_uniques = sorted(df[col].astype(str).unique())
        choix = st.sidebar.multiselect(f"Valeurs pour '{col}'", options=valeurs_uniques)
        
        if choix:
            df_filtered = df_filtered[df_filtered[col].astype(str).isin(choix)]

    # Indicateur de volume
    st.sidebar.markdown("---")
    percentage = (len(df_filtered) / len(df)) * 100
    st.sidebar.metric("Dossiers sélectionnés", f"{len(df_filtered)}", delta=f"{percentage:.1f}% du total")

    st.markdown("---")

    # --- 2. CONFIGURATION DU GRAPHIQUE ---
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        type_graph = st.selectbox(
            "1. Type de graphique", 
            ["Barres (Histogramme)", "Camembert (Secteurs)", "Courbe (Evolution Temporelle)", "Treemap (Hiérarchie)"]
        )
    
    with c2:
        # Axe X : On exclut 'num'
        cols_x = [c for c in df.columns if c != 'num']
        # Sélection par défaut intelligente : 'mois' pour courbe, 'mode' pour les autres
        idx_default = cols_x.index('mois') if 'mois' in cols_x else 0
        if type_graph == "Courbe (Evolution Temporelle)" and 'mois' in cols_x:
            pass # garde idx_default sur mois
        elif 'mode' in cols_x:
            try: idx_default = cols_x.index('mode')
            except: idx_default = 0
            
        var_x = st.selectbox("2. Variable principale (Axe X)", cols_x, index=idx_default)

    with c3:
        # Option de couleur / segmentation
        cols_color = ["Aucun"] + [c for c in df.columns if c not in ['num', 'date_ent', var_x]]
        var_color = st.selectbox("3. Segmenter par (Couleur)", cols_color)

    # Argument couleur pour Plotly
    color_arg = None if var_color == "Aucun" else var_color

    # --- 3. GENERATION DU GRAPHIQUE ---
    
    st.markdown("### Résultat")
    
    if len(df_filtered) == 0:
        st.warning("⚠️ Aucun donnée ne correspond aux filtres sélectionnés.")
    else:
        # LOGIQUE PLOTLY
        
        if type_graph == "Barres (Histogramme)":
            # On compte les occurrences
            group_cols = [var_x]
            if color_arg: group_cols.append(color_arg)
            
            data_agg = df_filtered.groupby(group_cols).size().reset_index(name='Nombre')
            
            fig = px.bar(
                data_agg, x=var_x, y='Nombre', color=color_arg,
                text='Nombre', title=f"Répartition par {var_x}",
                template="plotly_white"
            )
            fig.update_traces(textposition='outside')

        elif type_graph == "Camembert (Secteurs)":
            # Camembert ne supporte pas vraiment la segmentation couleur secondaire comme les barres
            # On ignore var_color ou on l'utilise pour définir les secteurs si var_x est vide (cas rare)
            data_agg = df_filtered.groupby(var_x).size().reset_index(name='Nombre')
            
            fig = px.pie(
                data_agg, names=var_x, values='Nombre',
                title=f"Répartition par {var_x}",
                hole=0.4 # Donut chart
            )

        elif type_graph == "Courbe (Evolution Temporelle)":
            if var_x not in ['date_ent', 'mois']:
                st.warning("💡 Conseil : Pour une courbe, choisissez 'date_ent' ou 'mois' en axe X.")
            
            group_cols = [var_x]
            if color_arg: group_cols.append(color_arg)
            
            data_agg = df_filtered.groupby(group_cols).size().reset_index(name='Nombre')
            # Tri important pour que la ligne ne fasse pas des zigzags
            data_agg = data_agg.sort_values(by=var_x)
            
            fig = px.line(
                data_agg, x=var_x, y='Nombre', color=color_arg,
                markers=True, title=f"Évolution temporelle par {var_x}"
            )

        elif type_graph == "Treemap (Hiérarchie)":
            # Treemap a besoin d'une hiérarchie. On utilise X, et Couleur si défini.
            path = [var_x]
            if color_arg: path.append(color_arg)
            
            data_agg = df_filtered.groupby(path).size().reset_index(name='Nombre')
            
            fig = px.treemap(
                data_agg, path=path, values='Nombre',
                title=f"Vue hiérarchique : {var_x}"
            )

        st.plotly_chart(fig, use_container_width=True)

    # --- 4. TABLEAU DES DONNÉES BRUTES DU GRAPHIQUE ---
    with st.expander("Voir les données brutes associées"):
        st.dataframe(df_filtered, use_container_width=True)

else:
    st.error("La base de données est vide ou inaccessible.")