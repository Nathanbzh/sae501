# pages/2_Analyse_Graphique_(Maquette).py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- 1. Simulation des données (DataFrame fictif) ---

DATA_SIZE = 750

# Simulation des modalités (Utilise une structure similaire à celle attendue après initialisation)
agglomerations = ['Agglo Vannes', 'Agglo Lorient', 'Agglo Ploërmel']
communes_data = {
    'Agglo Vannes': ['Vannes', 'Theix', 'Sarzeau'],
    'Agglo Lorient': ['Lorient', 'Ploemeur'],
    'Agglo Ploërmel': ['Ploërmel', 'Josselin']
}
quartiers_vannes = ['Ménimur', 'Kercado', 'Centre-ville', 'Cliscouet', 'Pohé']

sexes = ['Homme', 'Femme', 'Couple', 'Professionnel']
ages = ["-18 ans", "18-25 ans", "26-40 ans", "41-60 ans", "+ 60 ans"]

# Récupérer les variables dynamiques (pour la maquette)
if 'all_modalities' in st.session_state:
    dynamic_modalities = st.session_state.all_modalities
else:
    # Fallback si l'initialisation a échoué
    dynamic_modalities = {"Sexe": sexes, "Age": ages}


# Génération des données
data = pd.DataFrame({
    'Mois': np.random.choice(pd.date_range(start='2024-01-01', end='2024-12-31', periods=12).strftime('%Y-%m'), DATA_SIZE),
    'Agglomeration': np.random.choice(agglomerations, DATA_SIZE, p=[0.6, 0.3, 0.1]),
    'Commune': [''] * DATA_SIZE, # Sera rempli par set_geo_data
    'Quartier': [''] * DATA_SIZE, # Sera rempli par set_geo_data
    'Type_Demande': np.random.choice(["Droit de la famille", "Droit du logement", "Droit pénal"], DATA_SIZE),
    'Nombre_Demandes': np.random.randint(1, 5, DATA_SIZE),
    'Age_Moyen': np.random.randint(20, 70, DATA_SIZE) 
})

# Intégrer les variables dynamiques dans la simulation
for var_name, modalities in dynamic_modalities.items():
    if var_name not in data.columns:
        data[var_name] = np.random.choice(modalities, DATA_SIZE)

# Remplir les colonnes 'Commune' et 'Quartier'
def set_geo_data(row):
    agglo = row['Agglomeration']
    row['Commune'] = np.random.choice(communes_data[agglo])
    if row['Commune'] == 'Vannes':
        row['Quartier'] = np.random.choice(quartiers_vannes)
    else:
        row['Quartier'] = 'Non applicable'
    return row

data = data.apply(set_geo_data, axis=1)
data = data.sort_values(by='Mois').reset_index(drop=True)


# Définir l'état de la session pour les filtres avancés
if 'custom_filters' not in st.session_state:
    st.session_state.custom_filters = {}


# --- 2. Fonctions de visualisation avec Plotly Express ---

def create_chart_plotly(df_filtered, chart_type, x_var, y_var):
    """Génère un graphique Plotly basé sur le type sélectionné."""

    if df_filtered.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    MEASURE_COL = 'Mesure_Aggregee'
    fig = None

    try:
        # --- Logique d'Agrégation ---
        if chart_type in ["Diagramme en Barre", "Nuage de Points"]:
            plot_data = df_filtered.groupby(x_var, dropna=False)[y_var].sum().reset_index(name=MEASURE_COL)
        elif chart_type in ["Diagramme Circulaire", "Treemap", "Diagramme Linéaire Cumulatif"]:
            plot_data = df_filtered.groupby(x_var, dropna=False).size().reset_index(name=MEASURE_COL)
        else:
             return
            
        # --- Logique de Charting ---
        if chart_type == "Diagramme en Barre":
            fig = px.bar(plot_data, x=x_var, y=MEASURE_COL, title=f'Distribution de {y_var} par {x_var}')

        elif chart_type == "Diagramme Circulaire":
            fig = px.pie(plot_data, names=x_var, values=MEASURE_COL, title=f'Répartition par {x_var}')

        elif chart_type == "Treemap":
            fig = px.treemap(
                df_filtered.groupby([x_var, 'Type_Demande']).size().reset_index(name='Count'),
                path=[px.Constant("Tout"), x_var, 'Type_Demande'],
                values='Count',
                title=f'Treemap: {x_var} et Type de Demande'
            )

        elif chart_type == "Nuage de Points":
            fig = px.scatter(plot_data, x=x_var, y=MEASURE_COL, title=f'Nuage de points de {y_var} par {x_var}')
            
        elif chart_type == "Diagramme Linéaire Cumulatif":
            if x_var == 'Mois':
                plot_data = plot_data.sort_values(by=x_var)
                plot_data['Cumul'] = plot_data[MEASURE_COL].cumsum()
                
                fig = px.line(
                    plot_data,
                    x=x_var,
                    y='Cumul',
                    markers=True,
                    title=f'Nombre cumulatif de demandes par {x_var}'
                )
            else:
                st.warning("Le graphique cumulatif est optimisé pour la variable **Mois**.")
                fig = px.bar(plot_data, x=x_var, y=MEASURE_COL, title=f'Distribution par {x_var} (Non Cumulatif)')

        # Affichage du graphique
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erreur lors de la génération du graphique : Vérifiez les variables sélectionnées. Détail : {e}")


# --- 3. Construction de la page Streamlit ---

def visualisation_page():
    st.set_page_config(layout="wide")
    st.title("📊 Générateur de Graphiques (MAQUETTE)")
    st.markdown("---")

    st.header("Options de Graphique")
    chart_type = st.selectbox(
        "**Choisissez le type de graphique :**",
        options=["Diagramme en Barre", "Diagramme Circulaire", "Treemap", "Nuage de Points", "Diagramme Linéaire Cumulatif"]
    )
    
    st.markdown("---")

    # --- 3.1. Sidebar (Choix des Axes) ---
    st.sidebar.header("⚙️ Variables et Filtres")

    available_vars_numeric = ['Nombre_Demandes', 'Age_Moyen'] 
    available_vars_cat = [col for col in data.columns if col not in available_vars_numeric]

    st.sidebar.subheader("Axes du Graphique")

    if chart_type in ["Diagramme en Barre", "Nuage de Points", "Diagramme Linéaire Cumulatif"]:
        x_var = st.sidebar.selectbox("Axe des X (Catégorie/Temps)", options=[""] + available_vars_cat)
        y_var = st.sidebar.selectbox("Axe des Y (Mesure)", options=[""] + available_vars_numeric)
    elif chart_type in ["Diagramme Circulaire", "Treemap"]:
        x_var = st.sidebar.selectbox("Variable de Répartition", options=[""] + available_vars_cat)
        y_var = 'Nombre_Demandes' 
        st.sidebar.markdown("*(La taille du graphique est mesurée par **Nombre_Demandes**)*")
    else:
        x_var, y_var = None, None
    
    st.sidebar.markdown("---")
    
    # --- 3.2. Filtres Avancés Personnalisés ---
    st.sidebar.subheader("Filtres Avancés Personnalisés")

    all_filterable_vars = [col for col in data.columns if col not in available_vars_numeric]

    variable_to_add = st.sidebar.selectbox(
        "**Ajouter un filtre sur la variable...**",
        options=[""] + [col for col in all_filterable_vars if col not in st.session_state.custom_filters]
    )

    if variable_to_add and variable_to_add not in st.session_state.custom_filters:
        st.session_state.custom_filters[variable_to_add] = data[variable_to_add].unique().tolist()
        st.rerun()

    # Application des filtres
    df_filtered = data.copy()
    applied_filters = []
    
    with st.sidebar.expander(f"Gérer les {len(st.session_state.custom_filters)} filtres actifs"):
        keys_to_delete = []
        
        if not st.session_state.custom_filters:
            st.info("Aucun filtre avancé actif.")

        for var, current_selection in st.session_state.custom_filters.items():
            
            unique_values_initial = data[var].unique().tolist()
            
            st.markdown(f"**Variable : `{var}`**")
            
            selected_values = st.multiselect(
                f"Sélectionnez les valeurs de `{var}`",
                options=unique_values_initial,
                default=current_selection,
                key=f"custom_filter_{var}"
            )
            
            st.session_state.custom_filters[var] = selected_values
            
            if selected_values and set(selected_values) != set(unique_values_initial):
                applied_filters.append((var, selected_values))

            if st.button(f"Supprimer le filtre {var}", key=f"delete_{var}"):
                keys_to_delete.append(var)
        
        # Application des filtres avant la suppression
        for var, values in applied_filters:
            df_filtered = df_filtered[df_filtered[var].isin(values)]
        
        # Suppression des filtres
        if keys_to_delete:
            for key in keys_to_delete:
                del st.session_state.custom_filters[key]
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(f"Nombre total d'enregistrements filtrés : **{len(df_filtered)}** sur {DATA_SIZE}")
    
    # --- 3.3. Affichage du Graphique ---
    st.header("Résultat de la Visualisation")
    
    is_valid_chart = chart_type in ["Diagramme Circulaire", "Treemap"] and x_var
    is_valid_chart = is_valid_chart or (chart_type in ["Diagramme en Barre", "Nuage de Points", "Diagramme Linéaire Cumulatif"] and x_var and y_var)
    
    if is_valid_chart:
        create_chart_plotly(df_filtered, chart_type, x_var, y_var)
    else:
        st.info("Veuillez sélectionner un type de graphique et les variables d'axe correspondantes dans la barre latérale pour commencer la visualisation.")


# Exécuter la fonction de visualisation
visualisation_page()