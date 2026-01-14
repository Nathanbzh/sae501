import psycopg2
import pandas as pd

def export_entretien(
    conn_params: dict,
    date_debut,
    date_fin,
    colonne_date: str,
    fichier_csv: str
):
    conn = psycopg2.connect(**conn_params)

    query = f"""
    SELECT *
    FROM entretien
    WHERE {colonne_date} BETWEEN %s AND %s
    ORDER BY {colonne_date}
    """

    df = pd.read_sql(query, conn, params=(date_debut, date_fin))
    df.to_csv(fichier_csv, index=False, encoding="utf-8")

    conn.close()
    return len(df)
