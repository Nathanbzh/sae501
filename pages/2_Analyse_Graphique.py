# pages/2_Analyse_Graphique.py

import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

# --- 1. CONFIGURATION ET CONNEXION ---

# ⚠️ Dictionnaire de correspondance (Doit être IDENTIQUE à celui du formulaire)
TRANSCO = {
    "mode": {
        1: "RDV", 2: "Sans RDV", 3: "Téléphonique", 4: "Courrier", 
        5: "Mail", 6: "Autre", 99: "Non renseigné"
    },
    "duree": {
        1: "- 15 min.", 2: "15 à 30 min", 3: "30 à 45 min", 
        4: "45 à 60 min", 5: "+ de 60 min"
    },
    "sexe": {
        1: "Homme", 2: "Femme", 3: "Couple", 4: "Professionnel"
    },
    "age": {
        1: "-18 ans", 2: "18-25 ans", 3: "26-40 ans", 
        4: "41-60 ans", 5: "+ 60 ans"
    },
    "vient_pr": {
        1: "Soi", 2: "Conjoint", 3: "Parent", 4: "Enfant", 
        5: "Personne morale", 6: "Autre"
    },
    "sit_fam": {
        1: "Célibataire", 2: "Concubin", 3: "Pacsé", 4: "Marié", 
        5: "Séparé/divorcé", 6: "Veuf/ve", 99: "Non renseigné"
    },
    "enfant": {
        0: "Sans enf. à charge", 1: "Avec enf. en garde alternée", 
        2: "Avec enf. en garde principale", 3: "Avec enf. en droit de visite/hbgt", 
        4: "Parent isolé", 5: "Séparés sous le même toit", 99: "Non renseigné"
    },
    "profession": {
        1: "Scolaire/étudiant/formation", 2: "Pêcheur/agriculteur", 
        3: "Chef d'entreprise", 4: "Libéral", 5: "Secteur santé/social", 
        6: "Militaire", 7: "Employé", 8: "Ouvrier", 9: "Cadre", 
        10: "Retraité", 11: "En recherche d'emploi", 12: "Sans profession", 
        99: "Non renseigné"
    },
    "ress": {
        1: "Salaire", 2: "Revenus pro.", 3: "Retraite/réversion", 
        4: "Allocations chômage", 5: "RSA", 6: "AAH/invalidité", 
        7: "ASS", 8: "Bourse d'études.", 9: "Sans revenu"
    }
}

def init_connection():
    """Initialise la connexion à PostgreSQL."""
    try:
        return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            options="-c client_encoding=WIN1252"
        )
    except Exception as e:
        st.error(f"❌ Erreur de connexion BDD : {e}")
        return None

@st.cache_data(ttl=60) # Mise en cache des données pour 60 secondes
def load_data_from_db():
    """Charge les données depuis la base et applique le décodage."""
    conn = init_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # On sélectionne toutes les colonnes utiles
        query = """
            SELECT date_ent, mode, duree, sexe, age, vient_pr, sit_fam, enfant, profession, ress 
            FROM entretien
        """
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return df

        # --- TRANSFORMATION DES DONNÉES ---

        # 1. Conversion de la date
        df['date_ent'] = pd.to_datetime(df['date_ent'])
        df['Mois'] = df['date_ent'].dt.strftime('%Y-%m') # Création colonne Mois

        # 2. Décodage (Chiffre -> Texte)
        # On boucle sur chaque colonne du dictionnaire TRANSCO
        for col_name, mapping in TRANSCO.items():
            if col_name in df.columns:
                # On map les valeurs. Les codes inconnus resteront tels quels ou NaN
                df[col_name] = df[col_name].map(mapping).fillna("Inconnu/Non renseigné")

        # 3. Renommage des colonnes pour l'affichage (Optionnel, pour faire joli)
        df = df.rename(columns={
            "mode": "Mode Entretien",
            "duree": "Durée",
            "sexe": "Sexe",
            "age": "Tranche d'âge",
            "vient_pr": "Vient pour",
            "sit_fam": "Situation Familiale",
            "enfant": "Enfants",
            "profession": "Profession",
            "ress": "Ressources"
        })

        return df

    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        if conn: conn.close()
        return pd.DataFrame()


# --- 2. FONCTIONS DE VISUALISATION ---

def create_chart_plotly(df_filtered, chart_type, x_var, y_var=None):
    """Génère un graphique Plotly."""
    
    if df_filtered.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    # Par défaut, on compte le nombre de lignes (Nombre d'entretiens)
    # On groupe par la variable X pour avoir les totaux
    if chart_type in ["Diagramme en Barre", "Nuage de Points", "Diagramme Linéaire"]:
        data_grouped = df_filtered.groupby(x_var).size().reset_index(name='Nombre d\'entretiens')
    
    # --- Génération du Graphique ---
    
    if chart_type == "Diagramme en Barre":
        fig = px.bar(
            data_grouped, x=x_var, y='Nombre d\'entretiens', 
            title=f'Répartition par {x_var}', text='Nombre d\'entretiens'
        )
        fig.update_traces(textposition='outside') # Affiche le chiffre au dessus de la barre

    elif chart_type == "Diagramme Circulaire":
        # Pour le camembert, on groupe aussi
        data_grouped = df_filtered.groupby(x_var).size().reset_index(name='Count')
        fig = px.pie(
            data_grouped, names=x_var, values='Count', 
            title=f'Répartition par {x_var}'
        )

    elif chart_type == "Diagramme Linéaire (Chronologie)":
        # Spécifique pour voir l'évolution dans le temps
        if x_var != 'Mois' and x_var != 'date_ent':
            st.warning("⚠️ Pour un graphique linéaire, il est conseillé de choisir 'Mois' ou 'date_ent' en Axe X.")
        
        data_grouped = df_filtered.groupby(x_var).size().reset_index(name='Nombre d\'entretiens')
        fig = px.line(
            data_grouped, x=x_var, y='Nombre d\'entretiens', markers=True,
            title=f'Évolution temporelle par {x_var}'
        )

    elif chart_type == "Treemap":
        # Treemap nécessite souvent deux niveaux, on en ajoute un par défaut si possible
        path_vars = [x_var]
        if "Sexe" in df_filtered.columns and x_var != "Sexe":
            path_vars.append("Sexe") # On ajoute Sexe comme sous-catégorie par défaut
            
        fig = px.treemap(
            df_filtered, path=path_vars, 
            title=f'Treemap : {x_var}'
        )

    st.plotly_chart(fig, use_container_width=True)


# --- 3. PAGE PRINCIPALE ---

def visualisation_page():
    st.set_page_config(layout="wide")
    st.title("📊 Analyse des Données (Base Réelle)")
    st.markdown("---")

    # 1. Chargement des données
    with st.spinner("Chargement des données depuis la base PostgreSQL..."):
        df = load_data_from_db()

    if df.empty:
        st.info("Aucune donnée trouvée dans la table 'entretien' ou erreur de connexion.")
        return

    # 2. Paramètres Graphique
    st.sidebar.header("Paramètres du Graphique")

    chart_type = st.selectbox(
        "Type de graphique :",
        ["Diagramme en Barre", "Diagramme Circulaire", "Diagramme Linéaire (Chronologie)", "Treemap"]
    )

    # Création de la liste des variables disponibles (Catégorielles + Temps)
    # On exclut les colonnes qui ne sont pas pertinentes pour l'axe X principal
    available_columns = [c for c in df.columns if c not in ['ress', 'enfant']] # On peut tout garder si on veut
    available_columns = df.columns.tolist()

    x_var = st.selectbox("Choisissez la variable à analyser (Axe X / Catégorie) :", options=available_columns)

    st.markdown("---")

    # 3. Filtres Dynamiques (Sidebar)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtres Avancés")
    
    df_filtered = df.copy()

    # On propose de filtrer sur quelques variables clés
    filters_cols = ["Mois", "Mode Entretien", "Sexe", "Tranche d'âge"]
    
    for col in filters_cols:
        if col in df.columns:
            unique_vals = df[col].unique()
            selected = st.sidebar.multiselect(f"Filtrer par {col}", options=unique_vals)
            if selected:
                df_filtered = df_filtered[df_filtered[col].isin(selected)]

    # Indicateur de volume
    st.metric(label="Nombre d'entretiens affichés", value=len(df_filtered))

    # 4. Affichage du Graphique
    create_chart_plotly(df_filtered, chart_type, x_var)

    # 5. Affichage du tableau de données (Optionnel, utile pour vérifier)
    with st.expander("Voir les données brutes correspondantes"):
        st.dataframe(df_filtered, use_container_width=True)

# Lancer la page
visualisation_page()