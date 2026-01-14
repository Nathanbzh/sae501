import os
import glob
import pandas as pd
import psycopg2
from datetime import date
from dotenv import load_dotenv

# =========================
# 0. SÉCURITÉ & CONFIG
# =========================
# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# Chemins (Relatifs pour la portabilité)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOSSIER_EXCEL = os.path.join(BASE_DIR, "data_entretien")
ANNEE_FICHIERS = 2024

# =========================
# 1. CONFIGURATION DU MAPPING
# =========================

MOIS_FR = {
    "janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12, "décembre": 12
}

# Colonnes directes pour la table ENTRETIEN
MAPPING_ENTRETIEN = {
    "Mode": "mode",
    "Durée": "duree",
    "Sexe": "sexe",
    "Age": "age",
    "Vient pr": "vient_pr",
    "Sit° Fam": "sit_fam",
    "Enfts": "enfant",
    "Modèle fam.": "modele_fam",
    "Prof°": "profession",
    "Ress.1": "ress",
    "Origine": "origine",
    "Domicile": "commune",
    "Partenaire": "partenaire"
}

# ⚠️ LISTE DES COLONNES EXCEL CONTENANT LES DEMANDES
# Ajustez ces noms selon vos vrais entêtes Excel (ex: "Demande 1", "Nature", etc.)
COLS_DEMANDES = ["Dem.1", "Dem.2", "Dem.3"] 

# ⚠️ LISTE DES COLONNES EXCEL CONTENANT LES SOLUTIONS
# Ajustez ces noms selon vos vrais entêtes Excel
COLS_SOLUTIONS = ["Sol.1", "Sol.2", "Sol.3"]


# =========================
# 2. FONCTIONS UTILITAIRES
# =========================
def clean_value(val):
    """Nettoie les valeurs NaN/Nat pour PostgreSQL"""
    if pd.isna(val) or val == "" or str(val).strip() == "":
        return None
    return val

def clean_varchar_limit(val, limit=2):
    """Coupe les chaînes trop longues (ex: sit_fam)"""
    if val is None: return None
    s = str(val).strip()
    return s[:limit] if s else None

# =========================
# 3. MOTEUR D'IMPORTATION
# =========================
def importer_dossier_excel():
    conn = None
    try:
        print("Connexion à la base de données...")
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        conn.autocommit = False # On gère les transactions manuellement
        cur = conn.cursor()

        fichiers = glob.glob(os.path.join(DOSSIER_EXCEL, "*.xlsx"))
        print(f" {len(fichiers)} fichiers trouvés.")

        total_lignes_traitees = 0

        for fichier in fichiers:
            nom_fichier = os.path.basename(fichier)
            nom_mois = os.path.splitext(nom_fichier)[0].lower().strip()
            mois_num = MOIS_FR.get(nom_mois)

            if not mois_num:
                print(f" Fichier ignoré (nom de mois inconnu) : {nom_fichier}")
                continue

            print(f"📄 Traitement de : {nom_fichier} (Mois : {mois_num})")
            
            try:
                df = pd.read_excel(fichier)
            except Exception as e:
                print(f" Erreur lecture Excel {nom_fichier} : {e}")
                continue

            # Ajout de la date (1er du mois par défaut)
            date_default = date(ANNEE_FICHIERS, mois_num, 1)

            # --- BOUCLE LIGNE PAR LIGNE ---
            # Nécessaire pour récupérer l'ID généré (RETURNING num)
            count_local = 0
            
            for index, row in df.iterrows():
                try:
                    # A. PRÉPARATION DONNÉES ENTRETIEN
                    # --------------------------------
                    vals_entretien = {}
                    vals_entretien['date_ent'] = date_default
                    
                    # Mapping dynamique
                    for col_excel, col_sql in MAPPING_ENTRETIEN.items():
                        raw_val = row.get(col_excel) # Récupère valeur ou None
                        
                        # Nettoyage spécifique selon colonne
                        if col_sql in ["sit_fam", "origine"]:
                             vals_entretien[col_sql] = clean_varchar_limit(raw_val, 2)
                        elif col_sql in ["commune", "partenaire"]:
                             vals_entretien[col_sql] = clean_value(raw_val) # Texte normal
                        else:
                            # Numériques (Integer)
                            v = clean_value(raw_val)
                            try:
                                vals_entretien[col_sql] = int(float(v)) if v is not None else None
                            except:
                                vals_entretien[col_sql] = None

                    # B. INSERTION ENTRETIEN & RÉCUPÉRATION ID
                    # ----------------------------------------
                    columns = list(vals_entretien.keys())
                    values = list(vals_entretien.values())
                    
                    # Construction requête SQL dynamique
                    sql_ent = f"""
                        INSERT INTO ENTRETIEN ({', '.join(columns)}) 
                        VALUES ({', '.join(['%s'] * len(values))})
                        RETURNING num;
                    """
                    
                    cur.execute(sql_ent, values)
                    # C'EST ICI QU'ON RÉCUPÈRE LA CLÉ PRIMAIRE GÉNÉRÉE
                    new_id = cur.fetchone()[0]

                    # C. INSERTION DEMANDES (Table liée)
                    # ----------------------------------
                    pos_demande = 1
                    for col_dem in COLS_DEMANDES:
                        val_dem = clean_value(row.get(col_dem))
                        if val_dem:
                            sql_dem = "INSERT INTO DEMANDE (num, pos, nature) VALUES (%s, %s, %s)"
                            cur.execute(sql_dem, (new_id, pos_demande, str(val_dem)))
                            pos_demande += 1

                    # D. INSERTION SOLUTIONS (Table liée)
                    # -----------------------------------
                    pos_sol = 1
                    for col_sol in COLS_SOLUTIONS:
                        val_sol = clean_value(row.get(col_sol))
                        if val_sol:
                            sql_sol = "INSERT INTO SOLUTION (num, pos, nature) VALUES (%s, %s, %s)"
                            cur.execute(sql_sol, (new_id, pos_sol, str(val_sol)))
                            pos_sol += 1
                    
                    count_local += 1

                except Exception as row_error:
                    print(f"❌ Erreur ligne {index} dans {nom_fichier}: {row_error}")
                    conn.rollback() # On annule tout pour ce fichier si critique, ou continue
                    # Ici je choisis de stopper le fichier courant
                    break 

            # Validation de la transaction pour le fichier entier
            conn.commit()
            print(f"✅ {count_local} entretiens (+ demandes/réponses) insérés pour {nom_fichier}")
            total_lignes_traitees += count_local

        cur.close()
        conn.close()
        print("-" * 30)
        print(f"🎉 TERMINÉ. Total entretiens importés : {total_lignes_traitees}")

    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        if conn: conn.rollback()

if __name__ == "__main__":
    importer_dossier_excel()