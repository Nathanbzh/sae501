# pages/1_Formulaire_Saisie.py

import streamlit as st
import datetime
import psycopg2

# --- 0. CONFIGURATION & TRANSCODIFICATION ---

# ⚠️ Nom de la table (sans 's')
TABLE_NAME = "entretien"

# Dictionnaire de correspondance (Libellé -> Code Base de Données)
TRANSCO = {
    "Mode d'entretien": {
        "RDV": 1, "Sans RDV": 2, "Téléphonique": 3, "Courrier": 4, 
        "Mail": 5, "Autre": 6, "Non renseigné": 99
    },
    "Durée": {
        "- 15 min.": 1, "15 à 30 min": 2, "30 à 45 min": 3, 
        "45 à 60 min": 4, "+ de 60 min": 5
    },
    "Sexe": {
        "Homme": 1, "Femme": 2, "Couple": 3, "Professionnel": 4
    },
    "Age": {
        "-18 ans": 1, "18-25 ans": 2, "26-40 ans": 3, 
        "41-60 ans": 4, "+ 60 ans": 5
    },
    "Vient pour": {
        "Soi": 1, "Conjoint": 2, "Parent": 3, "Enfant": 4, 
        "Personne morale": 5, "Autre": 6
    },
    "Situtation familiale": {
        "Célibataire": 1, "Concubin": 2, "Pacsé": 3, "Marié": 4, 
        "Séparé/divorcé": 5, "Veuf/ve": 6, "Non renseigné": 99
    },
    "Enfant(s) à charge": {
        "Sans enf. à charge": 0, "Avec enf. en garde alternée": 1, 
        "Avec enf. en garde principale": 2, "Avec enf. en droit de visite/hbgt": 3, 
        "Parent isolé": 4, "Séparés sous le même toit": 5, "Non renseigné": 99
    },
    "Profession": {
        "Scolaire/étudiant/formation": 1, "Pêcheur/agriculteur": 2, 
        "Chef d'entreprise": 3, "Libéral": 4, "Secteur santé/social": 5, 
        "Militaire": 6, "Employé": 7, "Ouvrier": 8, "Cadre": 9, 
        "Retraité": 10, "En recherche d'emploi": 11, "Sans profession": 12, 
        "Non renseigné": 99
    },
    "Revenus": {
        "Salaire": 1, "Revenus pro.": 2, "Retraite/réversion": 3, 
        "Allocations chômage": 4, "RSA": 5, "AAH/invalidité": 6, 
        "ASS": 7, "Bourse d'études.": 8, "Sans revenu": 9
    }
}

# --- 1. DONNÉES HIÉRARCHIQUES (Parties 3, 4, 5) ---

# 3. NATURE DE LA DEMANDE
MODALITES_DEMANDE_HIERARCHIQUE = {
    "Droit de la famille / des personnes": {
        "1a": "Union", "1b": "Séparation/ divorce", "1c": "PA/PC", "1d": "Droit de garde",
        "1e": "Autorité parentale", "1f": "Filiation adoption", "1g": "Régimes matrimoniaux",
        "1h": "Protection des majeurs", "1i": "Etat civil", "1j": "Successions",
        "1k": "Assistance éducative", "1l": "Autre",
    },
    "Droit du logement": {
        "2a": "Litiges locatifs", "2b": "Expulsion", "2c": "Achat/vente d'un bien",
        "2d": "Copropriété", "2e": "Droit des biens", "2f": "Construction / urbanisme",
        "2g": "Conflit de voisinage", "2h": "Autre",
    },
    "Droit de la consommation": {
        "3a": "Crédit/reconnaissance de dette", "3b": "Téléphonie/internet", "3c": "Prestation de service",
        "3d": "Banque / Assurance", "3e": "Surendettement", "3f": "Autre",
    },
    "Autres domaines du droit civil": {
        "4a": "Responsabilité", "4b": "Voies d'exécution", "4c": "Procédure civile",
        "4d": "Erreur médicale", "4e": "Accident VTM", "4f": "Autre",
    },
    "Droit du travail / affaires / associations": {
        "5a": "Exécution du contrat de travail", "5b": "Rupture du contrat de travail",
        "5c": "Droit des affaires / sociétés", "5d": "Droit associatif", "5e": "Autre",
    },
    "Droit de la protection sociale": {
        "6a": "Aides sociales", "6b": "Sécurité sociale", "6c": "Retraite",
        "6d": "Cotisations sociales", "6e": "Autre",
    },
    "Droit pénal": {
        "7a": "Auteur/mis en cause", "7b": "Victime", "7c": "Violences faites aux femmes",
        "7d": "Discriminations", "7e": "Procédure pénale", "7f": "Autre",
    },
    "Droit administratif": {
        "8a": "Litige avec une administration", "8b": "Statuts de la fonction publique",
        "8c": "Droit des étrangers", "8d": "Autre",
    },
    "Démarches et formalités": {
        "9a": "Terminologie juridique", "9b": "Aide juridictionnelle", "9c": "Autre",
    }
}

# 4. REPONSE APPORTEE
MODALITES_REPONSE_HIERARCHIQUE = {
    "Information": { "1": "Information" },
    "Aide aux démarches": { "2a": "Saisine justice internet", "2b": "Aide CAF (ASF)", "2c": "Autre démarche" },
    "Aide à la rédaction": { "3a": "Courrier" },
    "Orientation prof-el du droit": {
        "4a": "Avocat", "4b": "Avocat mineur", "4c": "Notaire", "4d": "Huissier",
        "4e": "Tribunal", "4f": "Police/gendarmerie", "4g": "Autre",
    },
    "Orientation MARD": {
        "5a": "Conciliateur de justice", "5b": "Délégué du Défenseur des Droits",
        "5c": "Médiation familiale", "5d": "Médiation administrative",
        "5e": "Médiation consommation", "5f": "Médiation banque / assurance",
    },
    "Orientation administration": {
        "6a": "Mairie/EPCI", "6b": "DIRECCTE", "6c": "CAF", "6d": "Maison France Service",
        "6e": "Préfecture", "6f": "Impôts", "6g": "Autre",
    },
    "Orientation association": {
        "7a": "Aide aux victimes", "7b": "Accès au Droit", "7c": "ADIL",
        "7d": "Association de consommateurs", "7e": "Autre",
    },
    "Orientation santé / social": {
        "8a": "Travailleur social", "8b": "Professionnel de santé", "8c": "Professionnel jeunesse", "8d": "Autre",
    },
    "Orientation organisme privé": { "9a": "Protection juridique", "9b": "Autre organisme privé" },
    "RIPAM": { "10": "RIPAM" },
    "Action collective": { "11": "Action collective" },
    "3949 (NUAD)": { "12": "3949 (NUAD)" }
}

# 5. REPERAGE DU DISPOSITIF
MODALITES_REPERAGE_HIERARCHIQUE = {
    "Communication": { "1a": "Bouche à oreille", "1b": "Internet", "1c": "Presse" },
    "Déjà venu": { "2a": "Suite problématique", "2b": "Autre problématique" },
    "Par un professinonel du droit": { "3a": "Tribunaux", "3b": "Police/gendarmerie", "3c": "Professionnel du droit" },
    "Par une administration": { "4a": "CAF", "4b": "DIRECCTE", "4c": "Maison France Service", "4d": "Mairie/EPCI", "4e": "Autre" },
    "Par une association": {
        "6a": "France Victimes", "6b": "Associations de consommateurs", "6c": "ADIL",
        "6d": "UDAF", "6e": "Association d'accès au droit", "6f": "Autre",
    },
    "Organismes privés": { "7a": "Protection juridique", "7b": "Autre organisme privé" }
}

# --- 2. FONCTIONS UTILITAIRES ---

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

def get_code(category, label):
    """Traduit un libellé texte en code chiffre pour la BDD."""
    if label == "Sélectionner" or label is None:
        return None
    return TRANSCO.get(category, {}).get(label, None)

def generate_hierarchical_multiselect(title, hierarchical_data, key_prefix):
    """
    Génère les sélecteurs pour les parties 3, 4 et 5.
    Retourne la liste des choix (Code, Libellé).
    """
    st.header(title)
    
    # 1. Sélection des catégories principales
    categories = list(hierarchical_data.keys())
    selected_categories = st.multiselect(
        f"**Sélectionnez les grandes catégories concernées** pour {title}",
        options=categories,
        key=f"{key_prefix}_categories"
    )

    all_selections = []

    # 2. Sélection des détails pour chaque catégorie choisie
    for cat in selected_categories:
        options_map = hierarchical_data[cat] 
        libelles = list(options_map.values())
        
        st.markdown(f"**Catégorie : {cat}**")
        # Petit texte d'aide pour afficher les codes
        codes_list = [f"({code})" for code in options_map.keys()]
        st.caption(f"Codes possibles : {', '.join(codes_list)}")

        selections = st.multiselect(
            f"Choisissez les précisions pour {cat}",
            options=libelles,
            key=f"{key_prefix}_{cat.replace(' ', '_')}"
        )
        
        # Retrouver le code associé au libellé
        code_to_libelle = {v: k for k, v in options_map.items()}
        for libelle in selections:
            code = code_to_libelle.get(libelle)
            if code:
                all_selections.append((code, libelle))

    return all_selections


# --- 3. FORMULAIRE PRINCIPAL ---

def build_form():
    st.set_page_config(layout="wide")
    st.title("📝 Formulaire de Saisie")
    st.markdown("---")

    # Vérification que l'initialisation (Accueil.py) a été faite
    if 'all_modalities' not in st.session_state:
        st.error("Structure des modalités non trouvée. Veuillez recharger la page d'accueil.")
        return
        
    MODALITES = st.session_state.all_modalities
    
    # Stockage des inputs utilisateur pour les parties 1 et 2
    user_inputs = {}

    # --- PARTIE 1 : L'ENTRETIEN ---
    st.header("1. L'ENTRETIEN")
    col_mode, col_duree = st.columns(2)

    with col_mode:
        user_inputs["Mode d'entretien"] = st.selectbox(
            "**Mode d'entretien**",
            options=["Sélectionner"] + MODALITES["Mode d'entretien"],
            key="mode_entretien_key"
        )
    with col_duree:
        user_inputs["Durée"] = st.selectbox(
            "**Durée de l'entretien**",
            options=["Sélectionner"] + MODALITES["Durée"],
            key="duree_entretien_key"
        )

    st.markdown("---")

    # --- PARTIE 2 : L'USAGER ---
    st.header("2. L'USAGER")

    cols_count = 4 
    user_vars = [k for k in MODALITES.keys() if k not in ["Mode d'entretien", "Durée"]]
    
    for i in range(0, len(user_vars), cols_count):
        cols = st.columns(cols_count)
        for j in range(cols_count):
            if i + j < len(user_vars):
                key = user_vars[i + j]
                options = MODALITES[key]
                with cols[j]:
                    if len(options) > 5 or key not in ["Sexe", "Age"]: 
                         user_inputs[key] = st.selectbox(f"**{key}**", options=["Sélectionner"] + options, key=f"user_{key.replace(' ', '_')}_select")
                    else:
                         user_inputs[key] = st.radio(f"**{key}**", options=options, key=f"user_{key.replace(' ', '_')}_radio")

    st.markdown("---")
    
    # --- PARTIE 3, 4, 5 (Visuel uniquement pour l'instant) ---
    
    selected_demandes = generate_hierarchical_multiselect(
        "3. NATURE DE LA DEMANDE",
        MODALITES_DEMANDE_HIERARCHIQUE,
        "demande"
    )

    st.markdown("---")

    selected_reponses = generate_hierarchical_multiselect(
        "4. SOLUTION APPORTÉE",
        MODALITES_REPONSE_HIERARCHIQUE,
        "reponse"
    )

    st.markdown("---")

    selected_reperage = generate_hierarchical_multiselect(
        "5. REPÉRAGE DU DISPOSITIF",
        MODALITES_REPERAGE_HIERARCHIQUE,
        "reperage"
    )

    st.markdown("---")
    
    # --- SOUMISSION DU FORMULAIRE ---
    st.header("Enregistrement en Base de Données")
    st.info("ℹ️ Seules les parties 1 (Entretien) et 2 (Usager) sont enregistrées en base pour le moment.")
    
    submitted = st.button("💾 Enregistrer l'entretien")

    if submitted:
        # Validation basique
        if user_inputs["Mode d'entretien"] == "Sélectionner" or user_inputs["Durée"] == "Sélectionner":
            st.error("⚠️ Veuillez sélectionner au moins le **Mode d'entretien** et la **Durée**.")
            return

        # Préparation des données pour SQL
        try:
            conn = init_connection()
            if not conn:
                return

            cur = conn.cursor()

            # --- ETAPE 1 : CALCUL DU NOUVEAU NUMERO (CORRECTION BUG PK) ---
            # On cherche le max actuel + 1 pour éviter l'erreur de clé dupliquée
            cur.execute(f"SELECT COALESCE(MAX(num), 0) + 1 FROM {TABLE_NAME}")
            new_num = cur.fetchone()[0]

            # --- ETAPE 2 : TRANSCODIFICATION ---
            vals = {
                "num": new_num,
                "date_ent": datetime.date.today(),
                "mode": get_code("Mode d'entretien", user_inputs.get("Mode d'entretien")),
                "duree": get_code("Durée", user_inputs.get("Durée")),
                "sexe": get_code("Sexe", user_inputs.get("Sexe")),
                "age": get_code("Age", user_inputs.get("Age")),
                "vient_pr": get_code("Vient pour", user_inputs.get("Vient pour")),
                "sit_fam": get_code("Situtation familiale", user_inputs.get("Situtation familiale")),
                "enfant": get_code("Enfant(s) à charge", user_inputs.get("Enfant(s) à charge")),
                "profession": get_code("Profession", user_inputs.get("Profession")),
                "ress": get_code("Revenus", user_inputs.get("Revenus"))
            }

            # --- ETAPE 3 : INSERTION SQL ---
            query = f"""
                INSERT INTO {TABLE_NAME} 
                (num, date_ent, mode, duree, sexe, age, vient_pr, sit_fam, enfant, profession, ress)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cur.execute(query, (
                vals["num"], vals["date_ent"], vals["mode"], vals["duree"], 
                vals["sexe"], vals["age"], vals["vient_pr"], vals["sit_fam"], 
                vals["enfant"], vals["profession"], vals["ress"]
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            st.success(f"✅ Enregistrement réussi avec le numéro **{new_num}** !")
            st.balloons()
            
            # Feedback visuel (Optionnel : montrer ce qu'on a saisi dans les parties non-connectées)
            if selected_demandes or selected_reponses:
                with st.expander("Détails saisis (Non enregistrés en base)"):
                    st.write("Demandes :", [lib for code, lib in selected_demandes])
                    st.write("Réponses :", [lib for code, lib in selected_reponses])

        except Exception as e:
            st.error(f"❌ Erreur technique : {e}")
            if conn:
                conn.rollback()
                conn.close()

# Exécuter l'application
build_form()