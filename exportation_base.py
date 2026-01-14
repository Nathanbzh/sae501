# export la table entretien 

import psycopg2
import pandas as pd
from datetime import date

# Connexion PostgreSQL
DB_HOST = "localhost"
DB_PORT = "5437"
DB_USER = "pgis"
DB_PASS = "pgis"
DB_NAME = "DB_MaisonDuDroit"

# Dates de filtrage
DATE_DEBUT = date(2024, 1, 1)   # date de début
DATE_FIN = date(2024, 3,10)   # date de fin

COLONNE_DATE = "date_ent"  # colonne date dans la table

# Fichier exporté
FICHIER_CSV = "entretien_export.csv"

# 🔌 Connexion
conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
        )


#  Requête SQL avec intervalle de dates
query = f"""
SELECT *
FROM entretien
WHERE {COLONNE_DATE} BETWEEN %s AND %s
ORDER BY {COLONNE_DATE}
"""

#  Export vers CSV
df = pd.read_sql(query, conn, params=(DATE_DEBUT, DATE_FIN))
df.to_csv(FICHIER_CSV, index=False, encoding="utf-8")

#  Fermeture connexion
conn.close()

print(f" Export terminé : {len(df)} lignes exportées")
