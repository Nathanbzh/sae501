# database.py
# -*- coding: utf-8 -*-
import psycopg2
import streamlit as st
import datetime
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

# --- CONFIGURATION LOCALE SÉCURISÉE ---
LOCAL_DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5437"),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "password"),
    "options": "-c client_encoding=WIN1252"
}

def get_db_url():
    """Génère l'URL de connexion pour SQLAlchemy"""
    try:
        creds = st.secrets["postgres"]
        return f"postgresql+psycopg2://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    except (FileNotFoundError, KeyError, AttributeError):
        c = LOCAL_DB_CONFIG
        return f"postgresql+psycopg2://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['database']}"

def get_db_connection():
    """Connexion Psycopg2 classique"""
    try:
        return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            options="-c client_encoding=WIN1252"
        )
    except (FileNotFoundError, KeyError, AttributeError):
        return psycopg2.connect(**LOCAL_DB_CONFIG)

def get_pandas_data(query, params=None):
    db_url = get_db_url()
    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=params)
    except Exception as e:
        print(f"Erreur SQL (Pandas) : {e}")
        return pd.DataFrame()
    finally:
        engine.dispose()

# --- LECTURE CONFIG FORMULAIRE ---

def get_rubriques():
    """Récupère la liste des sections (Rubriques) disponibles"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pos, lib FROM RUBRIQUE ORDER BY pos")
            return cur.fetchall()
    except Exception:
        return []
    finally:
        if conn: conn.close()

def get_form_config():
    """Récupère la config pour la table principale ENTRETIEN"""
    conn = get_db_connection()
    config = []
    try:
        with conn.cursor() as cur:
            # On récupère les variables actives
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
                    "id": pos,
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
                config.append(field_info)
        return config
    except Exception as e:
        st.error(f"Erreur config : {e}")
        return []
    finally:
        if conn: conn.close()

def get_options_for_table(table_name, column_pos=3):
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

# --- ECRITURE (SAISIE) ---

def save_entretien_complet(data_entretien, liste_demandes, liste_solutions):
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
        if conn: conn.rollback()
        raise e
    finally:
        if conn: conn.close()

# --- ADMINISTRATION (CORRIGÉ) ---

def add_new_variable_db(nom_colonne, label_ui, type_var, id_rubrique, modalites_initiales=None):
    """
    Crée une variable. 
    CORRECTIONS CUMULÉES & FINALES : 
    1. mois_debut_validite = YYMM (ex: 2601).
    2. mois_fin_validite = 9999.
    3. est_contrainte = FALSE (pour satisfaire le NOT NULL).
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            safe_col_name = "".join(c for c in nom_colonne if c.isalnum() or c == '_').upper()
            if not safe_col_name:
                raise ValueError("Nom de colonne invalide")

            # Vérifie si la colonne existe déjà
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'entretien' AND column_name = %s", (safe_col_name.lower(),))
            if cur.fetchone():
                raise ValueError(f"La colonne {safe_col_name} existe déjà.")

            # 1. ALTER TABLE
            sql_type = "VARCHAR(255)" if type_var in ['CHAINE', 'MOD'] else "INTEGER"
            cur.execute(f"ALTER TABLE ENTRETIEN ADD COLUMN {safe_col_name} {sql_type}")

            # 2. INSERT INTO VARIABLE
            cur.execute("SELECT COALESCE(MAX(pos), 0) + 1 FROM VARIABLE WHERE tab='ENTRETIEN'")
            new_pos = cur.fetchone()[0]
            
            cur.execute("SELECT COALESCE(MAX(pos_r), 0) + 1 FROM VARIABLE WHERE tab='ENTRETIEN' AND rubrique=%s", (id_rubrique,))
            new_pos_r = cur.fetchone()[0]

            # --- CORRECTION DATES & CONTRAINTES ---
            today = datetime.date.today()
            current_month_int = int(today.strftime('%y%m')) # Ex: 2601
            end_month_infinite = 9999 
            est_contrainte_val = False # Valeur par défaut : pas de contrainte

            # Ajout de la colonne 'est_contrainte' dans l'INSERT
            cur.execute("""
                INSERT INTO VARIABLE (tab, pos, lib, type_v, rubrique, pos_r, commentaire, mois_debut_validite, mois_fin_validite, est_contrainte)
                VALUES ('ENTRETIEN', %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (new_pos, safe_col_name, type_var, id_rubrique, new_pos_r, label_ui, current_month_int, end_month_infinite, est_contrainte_val))

            # 3. INSERT INTO MODALITE
            if type_var == 'MOD' and modalites_initiales:
                for i, mod_label in enumerate(modalites_initiales):
                    code_mod = str(i + 1)
                    cur.execute("""
                        INSERT INTO MODALITE (tab, pos, code, lib_m, pos_m)
                        VALUES ('ENTRETIEN', %s, %s, %s, %s)
                    """, (new_pos, code_mod, mod_label, i+1))
            
            conn.commit()
            return True
    except Exception as e:
        if conn: conn.rollback()
        raise e
    finally:
        if conn: conn.close()

def add_new_modality_db(variable_pos, new_label):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(pos_m), 0) + 1 FROM MODALITE WHERE tab='ENTRETIEN' AND pos=%s", (variable_pos,))
            new_pos_m = cur.fetchone()[0]
            new_code = str(new_pos_m)

            cur.execute("""
                INSERT INTO MODALITE (tab, pos, code, lib_m, pos_m)
                VALUES ('ENTRETIEN', %s, %s, %s, %s)
            """, (variable_pos, new_code, new_label, new_pos_m))
            
            conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        raise e
    finally:
        if conn: conn.close()

# --- ANALYSE ET EXPORT ---

def get_translation_dictionary():
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
                        transco[col_key][str(key_val)] = lib
        return transco
    except Exception:
        return {}
    finally:
        if conn: conn.close()

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
    df_ent = get_pandas_data("SELECT * FROM ENTRETIEN WHERE num = %(num)s", params={"num": num_dossier})
    df_dem = get_pandas_data("SELECT * FROM DEMANDE WHERE num = %(num)s ORDER BY pos", params={"num": num_dossier})
    df_sol = get_pandas_data("SELECT * FROM SOLUTION WHERE num = %(num)s ORDER BY pos", params={"num": num_dossier})
    return df_ent, df_dem, df_sol