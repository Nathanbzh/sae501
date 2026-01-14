# -*- coding: utf-8 -*-
import psycopg2
import streamlit as st
import datetime
import os
from dotenv import load_dotenv

# Charge les variables si on exécute hors de Streamlit
load_dotenv()

def get_db_connection():
    """
    Tente de se connecter via les secrets Streamlit (Cloud/Prod),
    sinon bascule sur les variables d'environnement locales (.env).
    """
    try:
        # 1. Essai via Streamlit Secrets
        return psycopg2.connect(
            host=st.secrets["postgres"]["host"],
            port=st.secrets["postgres"]["port"],
            database=st.secrets["postgres"]["database"],
            user=st.secrets["postgres"]["user"],
            password=st.secrets["postgres"]["password"],
            options="-c client_encoding=WIN1252"
        )
    except (FileNotFoundError, KeyError, AttributeError):
        # 2. Fallback via .env (Local Script / Tests)
        try:
            return psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5437"),
                database=os.getenv("DB_NAME", "DB_MaisonDuDroit"),
                user=os.getenv("DB_USER", "pgis"),
                password=os.getenv("DB_PASS", "pgis"),
                options="-c client_encoding=WIN1252"
            )
        except Exception as e:
            st.error(f"❌ Impossible de se connecter à la base : {e}")
            raise e

def get_form_config():
    """Récupère la config pour la table principale ENTRETIEN"""
    conn = get_db_connection()
    config = []
    try:
        with conn.cursor() as cur:
            # On récupère les champs de l'entretien
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
                    # Options depuis MODALITE
                    cur.execute("SELECT code, lib_m FROM MODALITE WHERE tab='ENTRETIEN' AND pos=%s ORDER BY pos_m", (pos,))
                    for code, lib in cur.fetchall():
                        field_info["options"][lib] = code

                elif type_v == 'CHAINE':
                    # Options depuis VALEURS_C
                    cur.execute("SELECT lib FROM VALEURS_C WHERE tab='ENTRETIEN' AND pos=%s ORDER BY lib", (pos,))
                    for val in cur.fetchall():
                        field_info["options"][val[0]] = val[0] 

                config.append(field_info)
        return config
    except Exception as e:
        # En mode script, st.error n'affiche rien, on print
        print(f"Erreur config : {e}")
        return []
    finally:
        conn.close()

def get_options_for_table(table_name, column_pos=3):
    """
    Récupère les modalités pour les tables satellites (DEMANDE, SOLUTION).
    Par défaut, la colonne 'NATURE' est souvent en position 3 dans ton schéma.
    Retourne un dictionnaire { "Libellé": "Code" }
    """
    conn = get_db_connection()
    options = {}
    try:
        with conn.cursor() as cur:
            # On suppose que les choix sont stockés dans MODALITE pour ces tables
            query = "SELECT code, lib_m FROM MODALITE WHERE tab=%s AND pos=%s ORDER BY pos_m"
            cur.execute(query, (table_name, column_pos))
            rows = cur.fetchall()
            for code, lib in rows:
                options[lib] = code
        return options
    except Exception as e:
        print(f"Erreur options {table_name}: {e}")
        return {}
    finally:
        conn.close()

def save_entretien_complet(data_entretien, liste_demandes, liste_solutions):
    """
    Sauvegarde l'entretien ET les listes associées (Demandes/Solutions)
    en une seule transaction.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Nettoyage et Ajout Date pour ENTRETIEN
            clean_data = {k: v for k, v in data_entretien.items() if v is not None}
            clean_data["DATE_ENT"] = datetime.date.today() # Date du jour forcée

            # 2. Insertion ENTRETIEN
            columns = list(clean_data.keys())
            values = list(clean_data.values())
            cols_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(values))
            
            query_ent = f"INSERT INTO ENTRETIEN ({cols_str}) VALUES ({placeholders}) RETURNING NUM"
            cur.execute(query_ent, values)
            new_num = cur.fetchone()[0]

            # 3. Insertion DEMANDES (Boucle)
            # Table DEMANDE(NUM, POS, NATURE)
            for i, code_demande in enumerate(liste_demandes):
                # POS commence à 1
                cur.execute("INSERT INTO DEMANDE (NUM, POS, NATURE) VALUES (%s, %s, %s)", (new_num, i+1, code_demande))

            # 4. Insertion SOLUTIONS (Boucle)
            # Table SOLUTION(NUM, POS, NATURE)
            for i, code_sol in enumerate(liste_solutions):
                cur.execute("INSERT INTO SOLUTION (NUM, POS, NATURE) VALUES (%s, %s, %s)", (new_num, i+1, code_sol))
            
            # Si tout est bon, on valide
            conn.commit()
            return new_num
            
    except Exception as e:
        conn.rollback() # Annule tout si une erreur survient
        raise e
    finally:
        conn.close()