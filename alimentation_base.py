import os
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import date
# --- CONFIGURATION ---
DB_HOST = "localhost"
DB_PORT = "5437"           
DB_USER = "pgis"
DB_PASS = "pgis"
DB_NAME = "DB_MaisonDuDroit_test"
CSV_PATH = r"H:/Projetdroit/tentative.csv"

# Dossier contenant vos fichiers Excel (ex: Janvier.xlsx, Fevrier.xlsx...)
DOSSIER_EXCEL = r"H:\SAE501-2\projet\sae501\data_entretien" 

# L'année à utiliser pour reconstruire la date (Vous aviez écrit 20224, je suppose 2024)
ANNEE_FICHIERS = 2024 

# Mapping pour convertir le nom du fichier en numéro de mois
MOIS_FR = {
    "janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4, 
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8, "août": 8, 
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12, "décembre": 12
}

MAPPING_COLONNES = {
    "Mode": "MODE",
    "Durée": "DUREE",            
    "Sexe": "SEXE",
    "Age": "AGE",
    "Vient pr": "VIENT_PR",        
    "Sit° Fam": "SIT_FAM",         
    "Enfts": "ENFANT",             
    "Modèle fam.": "MODELE_FAM",  
    "Prof°": "PROFESSION",        
    "Ress.1": "RESS",              
    "Origine": "ORIGINE",
    "Domicile": "COMMUNE",         
    "Partenaire": "PARTENAIRE"
}

def importer_dossier_excel():
    conn = None
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()
        
        chemin_recherche = os.path.join(DOSSIER_EXCEL, "*.xlsx")
        fichiers = glob.glob(chemin_recherche)
        
        print(f"📂 {len(fichiers)} fichiers trouvés.")

        for fichier in fichiers:
            # --- A. Extraction du mois depuis le nom du fichier ---
            nom_fichier_sans_ext = os.path.splitext(os.path.basename(fichier))[0]
            nom_propre = nom_fichier_sans_ext.lower().strip() # met en minuscule et enlève les espaces
            
            # On cherche le mois correspondant
            mois_num = MOIS_FR.get(nom_propre)
            
            if not mois_num:
                print(f"⚠️ Ignoré : '{nom_fichier_sans_ext}' ne ressemble pas à un mois connu.")
                continue
                
            # On crée une date (ex: 1er Janvier 2024)
            date_fichier = date(ANNEE_FICHIERS, mois_num, 1)
            
            # --- B. Lecture Excel ---
            try:
                df = pd.read_excel(fichier)
            except Exception as e:
                print(f"   ❌ Erreur de lecture : {e}")
                continue

            # --- C. Ajout de la colonne DATE_ENT ---
            # On remplit toute la colonne avec la date calculée
            df['DATE_ENT'] = date_fichier
            
            # --- D. Renommage ---
            df = df.rename(columns=MAPPING_COLONNES)
            
            # On liste les colonnes qu'on veut insérer (celles du mapping + la date qu'on vient de créer)
            colonnes_visees = list(MAPPING_COLONNES.values()) + ['DATE_ENT']
            
            # On filtre pour ne garder que ce qui existe vraiment dans le DF
            colonnes_presentes = [c for c in colonnes_visees if c in df.columns]
            df_final = df[colonnes_presentes]

            # Nettoyage NaN -> None
            df_final = df_final.where(pd.notnull(df_final), None)

            # --- E. Insertion ---
            cols_str = ",".join(colonnes_presentes)
            values_str = " %s" * len(colonnes_presentes)
            query = f"INSERT INTO ENTRETIEN ({cols_str}) VALUES %s"
            
            data_tuples = [tuple(x) for x in df_final.to_numpy()]

            try:
                execute_values(cur, query, data_tuples)
                conn.commit()
                print(f"   ✅ {len(data_tuples)} lignes insérées pour {nom_fichier_sans_ext}.")
            except Exception as e:
                conn.rollback()
                print(f"   ❌ Erreur SQL : {e}")

        cur.close()
        print("🎉 Terminé !")

    except Exception as e:
        print(f"❌ Erreur connexion : {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    importer_dossier_excel()