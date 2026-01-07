# pages/4_Export_Donnees.py

import streamlit as st
import pandas as pd
import psycopg2
import io

# --- 1. CONFIGURATION ET DICTIONNAIRE ---

st.set_page_config(layout="wide", page_title="Données Brutes & Export")

# Dictionnaire de traduction (Identique aux autres pages)
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

# Fonction pour convertir le DataFrame en fichier Excel binaire
def to_excel(df):
    output = io.BytesIO()
    # Utilise 'xlsxwriter' ou 'openpyxl' comme moteur
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Données_Entretiens')
    processed_data = output.getvalue()
    return processed_data

# --- 2. CHARGEMENT ET AFFICHAGE ---

st.title("📂 Vue des Données Brutes")
st.markdown("Consultez et exportez les données de la table `entretien`.")

conn = init_connection()

if conn:
    # 1. Récupération des données
    query = """
        SELECT *
        FROM entretien
        ORDER BY date_ent DESC
    """
    # Note: J'ai ajouté 'id' si tu en as un (clé primaire), sinon retire-le de la requête
    
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            
            # 2. Nettoyage et Traduction
            # Formatage de la date (enlève les heures si inutiles)
            if 'date_ent' in df.columns:
                df['date_ent'] = pd.to_datetime(df['date_ent']).dt.date

            # Traduction des codes en texte
            df_decoded = df.copy()
            for col, mapping in TRANSCO.items():
                if col in df_decoded.columns:
                    df_decoded[col] = df_decoded[col].map(mapping).fillna(df_decoded[col])

            # Renommage des colonnes pour l'export (plus propre)
            column_rename = {
                "date_ent": "Date Entretien",
                "mode": "Mode",
                "duree": "Durée",
                "sexe": "Genre",
                "age": "Tranche Age",
                "vient_pr": "Vient Pour",
                "sit_fam": "Situation Familiale",
                "enfant": "Enfants",
                "profession": "Profession",
                "ress": "Ressources"
            }
            df_decoded = df_decoded.rename(columns=column_rename)

            # 3. Zone de Filtres Rapides (Optionnel mais pratique)
            with st.expander("🔎 Filtrer avant export"):
                col1, col2 = st.columns(2)
                with col1:
                    if "Mode" in df_decoded.columns:
                        modes = st.multiselect("Filtrer par Mode", df_decoded["Mode"].unique())
                        if modes:
                            df_decoded = df_decoded[df_decoded["Mode"].isin(modes)]
                with col2:
                    if "Genre" in df_decoded.columns:
                        genres = st.multiselect("Filtrer par Genre", df_decoded["Genre"].unique())
                        if genres:
                            df_decoded = df_decoded[df_decoded["Genre"].isin(genres)]

            # 4. Affichage du tableau
            st.markdown(f"**Nombre de lignes :** {len(df_decoded)}")
            st.dataframe(df_decoded, use_container_width=True)

            # 5. Bouton d'Export Excel
            st.markdown("### 📥 Exporter")
            
            excel_data = to_excel(df_decoded)
            
            st.download_button(
                label="Télécharger en Excel (.xlsx)",
                data=excel_data,
                file_name=f"export_entretiens_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.warning("La table est vide.")

    except Exception as e:
        st.error(f"Erreur lors de la lecture des données : {e}")
        if conn: conn.close()
else:
    st.error("Impossible de se connecter à la base.")