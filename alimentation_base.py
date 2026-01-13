import os
import glob
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import date

# =========================
# CONFIGURATION
# =========================
DB_HOST = "localhost"
DB_PORT = "5437"
DB_USER = "pgis"
DB_PASS = "pgis"
DB_NAME = "DB_MaisonDuDroit"

DOSSIER_EXCEL = r"H:\SAE501-2\projet\sae501\data_entretien"
ANNEE_FICHIERS = 2024

# =========================
# MOIS FR → NUM
# =========================
MOIS_FR = {
    "janvier": 1, "fevrier": 2, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12, "décembre": 12
}

# =========================
# MAPPING EXCEL → POSTGRES
# =========================
MAPPING_COLONNES = {
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

# =========================
# IMPORT
# =========================
def importer_dossier_excel():
    conn = None

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        fichiers = glob.glob(os.path.join(DOSSIER_EXCEL, "*.xlsx"))
        print(f"📂 {len(fichiers)} fichiers trouvés.")

        for fichier in fichiers:
            # -------------------------
            # A. Mois depuis nom fichier
            # -------------------------
            nom = os.path.splitext(os.path.basename(fichier))[0].lower().strip()
            mois_num = MOIS_FR.get(nom)

            if not mois_num:
                print(f"⚠️ Ignoré : {nom}")
                continue

            date_fichier = date(ANNEE_FICHIERS, mois_num, 1)

            # -------------------------
            # B. Lecture Excel
            # -------------------------
            try:
                df = pd.read_excel(fichier)
            except Exception as e:
                print(f"❌ Lecture impossible : {e}")
                continue

            # -------------------------
            # C. Ajout date
            # -------------------------
            df["date_ent"] = date_fichier

            # -------------------------
            # D. Mapping colonnes
            # -------------------------
            df = df.rename(columns=MAPPING_COLONNES)
            colonnes = list(MAPPING_COLONNES.values()) + ["date_ent"]
            colonnes_presentes = [c for c in colonnes if c in df.columns]
            df_final = df[colonnes_presentes]

            # -------------------------
            # E. Typage strict
            # -------------------------
            df_final = df_final.where(pd.notnull(df_final), None)

            colonnes_smallint = [
                "mode", "duree", "sexe", "age", "vient_pr", "enfant",
                "modele_fam", "profession", "ress"
            ]

            for col in colonnes_smallint:
                if col in df_final.columns:
                    df_final[col] = pd.to_numeric(df_final[col], errors="coerce").astype("Int64")

            colonnes_text = ["sit_fam", "origine", "commune", "partenaire"]

            for col in colonnes_text:
                if col in df_final.columns:
                    df_final[col] = df_final[col].astype(str)

            df_final["date_ent"] = pd.to_datetime(df_final["date_ent"]).dt.date
            # Conversion finale pd.NA -> None pour psycopg2
            df_final = df_final.astype(object).where(df_final.notna(), None)

            # Sécurisation VARCHAR(2)
            for col in ["sit_fam", "origine"]:
                if col in df_final.columns:
                    df_final[col] = (
                        df_final[col]
                        .astype(str)
                        .str.strip()
                        .str[:2]          # coupe à 2 caractères max
                    )


            # -------------------------
            # F. Insertion SQL
            # -------------------------
            cols_sql = ",".join(df_final.columns)
            query_insert = f"INSERT INTO entretien ({cols_sql}) VALUES %s"
            data = [tuple(row) for row in df_final.to_numpy()]

            try:
                execute_values(cur, query_insert, data)
                conn.commit()
                print(f"✅ {len(data)} lignes insérées pour {nom}")
            except Exception as e:
                conn.rollback()
                print(f"❌ Erreur SQL : {e}")

        cur.close()
        print("🎉 Import terminé")

    except Exception as e:
        print(f"❌ Connexion impossible : {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    importer_dossier_excel()
