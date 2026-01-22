# tests/conftest.py
# -*- coding: utf-8 -*-
import pytest
import psycopg2
from database import LOCAL_DB_CONFIG

@pytest.fixture(scope="session", autouse=True)
def init_db_schema():
    """
    Initialise la BDD pour les tests de manière NON DESTRUCTIVE.
    Crée les tables seulement si elles n'existent pas.
    N'injecte les données de config que si les tables sont vides.
    """
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # 1. Création des tables (IF NOT EXISTS) - ON NE FAIT PLUS DE DROP
            cur.execute("""
                CREATE TABLE IF NOT EXISTS RUBRIQUE (pos SERIAL PRIMARY KEY, lib VARCHAR(100));
                
                CREATE TABLE IF NOT EXISTS VARIABLE (
                    pos SERIAL PRIMARY KEY, 
                    tab VARCHAR(50), 
                    rubrique INTEGER, 
                    pos_r INTEGER, 
                    lib VARCHAR(50), 
                    type_v VARCHAR(10), 
                    commentaire VARCHAR(100),
                    mois_debut_validite INTEGER,
                    mois_fin_validite INTEGER,
                    est_contrainte BOOLEAN
                );
                
                CREATE TABLE IF NOT EXISTS MODALITE (id SERIAL PRIMARY KEY, tab VARCHAR(50), pos INTEGER, pos_m INTEGER, code INTEGER, lib_m VARCHAR(100));
                CREATE TABLE IF NOT EXISTS VALEURS_C (id SERIAL PRIMARY KEY, tab VARCHAR(50), pos INTEGER, lib VARCHAR(100));
                
                CREATE TABLE IF NOT EXISTS ENTRETIEN(
                    NUM SERIAL PRIMARY KEY, 
                    DATE_ENT DATE, 
                    MODE INTEGER, 
                    DUREE INTEGER, 
                    SEXE INTEGER, 
                    AGE INTEGER, 
                    VIENT_PR INTEGER, 
                    SIT_FAM INTEGER, 
                    ENFANT INTEGER, 
                    PROFESSION INTEGER, 
                    RESS INTEGER
                );
                CREATE TABLE IF NOT EXISTS DEMANDE (NUM INTEGER, POS INTEGER, NATURE INTEGER);
                CREATE TABLE IF NOT EXISTS SOLUTION (NUM INTEGER, POS INTEGER, NATURE INTEGER);
            """)

            # 2. Injection conditionnelle de la configuration
            # On vérifie si la table VARIABLE contient déjà des données pour ne pas dupliquer
            cur.execute("SELECT COUNT(*) FROM VARIABLE")
            count_vars = cur.fetchone()[0]

            if count_vars == 0:
                print("⚠️ Initialisation de la configuration BDD (Table vide détectée)...")
                
                # Rubriques
                cur.execute("INSERT INTO RUBRIQUE (pos, lib) VALUES (1, 'Entretien'), (2, 'Usager');")
                
                # Variables
                cur.execute("INSERT INTO VARIABLE (pos, tab, rubrique, pos_r, lib, type_v, commentaire) VALUES (10, 'ENTRETIEN', 1, 1, 'MODE', 'MOD', 'Mode entretien');")
                cur.execute("INSERT INTO VARIABLE (pos, tab, rubrique, pos_r, lib, type_v, commentaire) VALUES (20, 'ENTRETIEN', 1, 2, 'DUREE', 'MOD', 'Durée');")
                cur.execute("INSERT INTO VARIABLE (pos, tab, rubrique, pos_r, lib, type_v, commentaire) VALUES (30, 'ENTRETIEN', 2, 1, 'SEXE', 'MOD', 'Sexe');")

                # Modalités
                modes = ["RDV", "Sans RDV", "Téléphone", "Mail", "Courrier", "Autre"]
                for idx, lbl in enumerate(modes):
                    cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('ENTRETIEN', 10, %s, %s, %s)", (idx+1, idx+1, lbl))

                # Codes fixes pour Durée (1 et 2)
                cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('ENTRETIEN', 20, 1, 1, '-15 min'), ('ENTRETIEN', 20, 2, 2, '+15 min');")
                
                # Codes fixes pour Sexe
                cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('ENTRETIEN', 30, 1, 1, 'Homme'), ('ENTRETIEN', 30, 2, 2, 'Femme');")

                # Codes fixes pour Demande/Solution
                cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('DEMANDE', 3, 1, 100, 'Logement');")
                cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('SOLUTION', 3, 1, 200, 'Information');")
            else:
                print("ℹ️ Configuration existante conservée.")

    finally:
        conn.close()