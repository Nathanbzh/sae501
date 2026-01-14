# database.py
# -*- coding: utf-8 -*-
import psycopg2
import streamlit as st
import datetime
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Charge les variables d'environnement (pour le mode local)
load_dotenv()

# --- CONFIGURATION LOCALE SÉCURISÉE ---
# On utilise os.getenv pour récupérer les valeurs du fichier .env
# Les valeurs par défaut (ex: "localhost") ne sont là qu'en cas d'oubli du .env
LOCAL_DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "options": "-c client_encoding=WIN1252"
}

def get_db_url():
    """Génère l'URL de connexion pour SQLAlchemy"""
    try:
        # 1. Essai Configuration Streamlit Cloud (secrets.toml)
        creds = st.secrets["postgres"]
        return f"postgresql+psycopg2://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    except (FileNotFoundError, KeyError, AttributeError):
        # 2. Fallback Configuration Locale (.env)
        c = LOCAL_DB_CONFIG
        return f"postgresql+psycopg2://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['database']}"

def get_db_connection():
    """Connexion Psycopg2 classique (pour INSERT/UPDATE et lecture métadonnées)"""
    try:
        # 1. Essai Configuration Streamlit Cloud
        return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            options="-c client_encoding=WIN1252"
        )
    except (FileNotFoundError, KeyError, AttributeError):
        # 2. Fallback Configuration Locale
        try:
            return psycopg2.connect(**LOCAL_DB_CONFIG)
        except Exception as e:
            st.error(f"❌ Erreur de connexion (Locale) : {e}")
            raise e

def get_pandas_data(query, params=None):
    """
    Exécute une requête SQL et retourne un DataFrame via SQLAlchemy
    pour éviter les warnings Pandas.
    """
    db_url = get_db_url()
    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=params)
    except Exception as e:
        # En prod, on évite d'afficher l'erreur brute à l'utilisateur, mais utile pour debug
        print(f"Erreur SQL (Pandas) : {e}")
        return pd.DataFrame()
    finally:
        engine.dispose()

# --- FONCTIONS ESSENTIELLES (PAGE 1) ---

def get_form_config():
    """Récupère la config pour la table principale ENTRETIEN"""
    conn = get_db_connection()
    config = []
    try:
        with conn.cursor() as cur:
            query_vars = """
                SELECT v.pos, v.lib, v.type_v, v.commentaire, r.lib as rubrique_lib
                FROM VARIABLE v
                JOIN RUBRIQUE r ON v.rubrique = r.pos
                WHERE v.tab = 'ENTRETIEN'
                ORDER BY r.pos, v.pos_r
            """
            cur.execute(query_vars)
            vars_rows = cur.fetchall()

            for row in vars_rows:
                pos, lib_col, type_v, label_ui, rubrique = row
                field_info = {
                    "column_name": lib_col,
                    "label": label_ui,
                    "type": type_v,
                    "section": rubrique,
                    "options": {}
                }
                if type_v == 'MOD':
                    cur.execute("SELECT code, lib_m FROM MODALITE WHERE tab='ENTRETIEN' AND pos=%s ORDER BY pos_m", (pos,))
                    for code, lib in cur.fetchall():
                        field_info["options"][lib] = code
                elif type_v == 'CHAINE':
                    cur.execute("SELECT lib FROM VALEURS_C WHERE tab='ENTRETIEN' AND pos=%s ORDER BY lib", (pos,))
                    for val in cur.fetchall():
                        field_info["options"][val[0]] = val[0] 
                config.append(field_info)
        return config
    except Exception as e:
        st.error(f"Erreur config : {e}")
        return []
    finally:
        if conn: conn.close()

def get_options_for_table(table_name, column_pos=3):
    """Récupère les modalités pour DEMANDE et SOLUTION"""
    conn = get_db_connection()
    options = {}
    try:
        with conn.cursor() as cur:
            query = "SELECT code, lib_m FROM MODALITE WHERE tab=%s AND pos=%s ORDER BY pos_m"
            cur.execute(query, (table_name, column_pos))
            rows = cur.fetchall()
            for code, lib in rows:
                options[lib] = code
        return options
    except Exception as e:
        st.error(f"Erreur options {table_name}: {e}")
        return {}
    finally:
        if conn: conn.close()

def save_entretien_complet(data_entretien, liste_demandes, liste_solutions):
    """Sauvegarde le dossier complet"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            clean_data = {k: v for k, v in data_entretien.items() if v is not None}
            clean_data["DATE_ENT"] = datetime.date.today()

            columns = list(clean_data.keys())
            values = list(clean_data.values())
            cols_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(values))
            
            query_ent = f"INSERT INTO ENTRETIEN ({cols_str}) VALUES ({placeholders}) RETURNING NUM"
            cur.execute(query_ent, values)
            new_num = cur.fetchone()[0]

            for i, code_demande in enumerate(liste_demandes):
                cur.execute("INSERT INTO DEMANDE (NUM, POS, NATURE) VALUES (%s, %s, %s)", (new_num, i+1, code_demande))

            for i, code_sol in enumerate(liste_solutions):
                cur.execute("INSERT INTO SOLUTION (NUM, POS, NATURE) VALUES (%s, %s, %s)", (new_num, i+1, code_sol))
            
            conn.commit()
            return new_num
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        if conn: conn.close()

# --- FONCTIONS POUR ANALYSE ET EXPORT ---

def get_translation_dictionary():
    """Récupère traductions pour ENTRETIEN (Via Psycopg2)"""
    conn = get_db_connection()
    transco = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pos, lib, type_v FROM VARIABLE WHERE tab = 'ENTRETIEN' AND (type_v = 'MOD' OR type_v = 'CHAINE')")
            vars_rows = cur.fetchall()
            for pos, col_name, type_v in vars_rows:
                col_key = col_name.lower()
                transco[col_key] = {}
                if type_v == 'MOD':
                    cur.execute("SELECT code, lib_m FROM MODALITE WHERE tab='ENTRETIEN' AND pos=%s", (pos,))
                    for code, lib in cur.fetchall():
                        try: key_val = int(code)
                        except ValueError: key_val = code
                        transco[col_key][key_val] = lib
                elif type_v == 'CHAINE':
                    cur.execute("SELECT lib FROM VALEURS_C WHERE tab='ENTRETIEN' AND pos=%s", (pos,))
                    for val in cur.fetchall():
                        transco[col_key][val[0]] = val[0]
        return transco
    except Exception as e:
        st.error(f"Erreur dictionnaire traduction : {e}")
        return {}
    finally:
        if conn: conn.close()

def get_available_months():
    """Utilise SQLAlchemy pour éviter les warnings Pandas"""
    query = "SELECT DISTINCT TO_CHAR(date_ent, 'YYYY-MM') as mois FROM ENTRETIEN ORDER BY mois DESC"
    df = get_pandas_data(query)
    if not df.empty:
        return df['mois'].tolist()
    return []

def get_recent_dossiers_list(limit=50):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT num, date_ent FROM ENTRETIEN ORDER BY date_ent DESC, num DESC LIMIT %s", (limit,))
            return cur.fetchall()
    except Exception:
        return []
    finally:
        if conn: conn.close()

def get_dossier_complete_data(num_dossier):
    """Utilise SQLAlchemy pour éviter les warnings Pandas"""
    # 1. ENTRETIEN
    df_ent = get_pandas_data("SELECT * FROM ENTRETIEN WHERE num = %(num)s", params={"num": num_dossier})
    # 2. DEMANDE
    df_dem = get_pandas_data("SELECT * FROM DEMANDE WHERE num = %(num)s ORDER BY pos", params={"num": num_dossier})
    # 3. SOLUTION
    df_sol = get_pandas_data("SELECT * FROM SOLUTION WHERE num = %(num)s ORDER BY pos", params={"num": num_dossier})
    
    return df_ent, df_dem, df_sol