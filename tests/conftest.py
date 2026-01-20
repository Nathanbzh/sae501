# tests/conftest.py
# -*- coding: utf-8 -*-
import pytest
import psycopg2
from database import LOCAL_DB_CONFIG

@pytest.fixture(scope="session", autouse=True)
def init_db_schema():
    """
    Crée la structure BDD pour les tests.
    MISE À JOUR : Ajout des colonnes de contraintes dans VARIABLE.
    """
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    conn.autocommit = True
    with conn.cursor() as cur:
        # 1. Nettoyage
        tables = ["SOLUTION", "DEMANDE", "ENTRETIEN", "VALEURS_C", "MODALITE", "VARIABLE", "RUBRIQUE"]
        for t in tables:
            cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

        # 2. Création des tables
        cur.execute("""
            CREATE TABLE RUBRIQUE (pos SERIAL PRIMARY KEY, lib VARCHAR(100));
            
            -- DEFINITION MISE À JOUR --
            CREATE TABLE VARIABLE (
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
            
            CREATE TABLE MODALITE (id SERIAL PRIMARY KEY, tab VARCHAR(50), pos INTEGER, pos_m INTEGER, code INTEGER, lib_m VARCHAR(100));
            CREATE TABLE VALEURS_C (id SERIAL PRIMARY KEY, tab VARCHAR(50), pos INTEGER, lib VARCHAR(100));
            
            CREATE TABLE ENTRETIEN(NUM SERIAL PRIMARY KEY, DATE_ENT DATE, MODE INTEGER, DUREE INTEGER, SEXE INTEGER, AGE INTEGER, VIENT_PR INTEGER, SIT_FAM INTEGER, ENFANT INTEGER, PROFESSION INTEGER, RESS INTEGER);
            CREATE TABLE DEMANDE (NUM INTEGER, POS INTEGER, NATURE INTEGER);
            CREATE TABLE SOLUTION (NUM INTEGER, POS INTEGER, NATURE INTEGER);
        """)

        # 3. Injection Configuration initiale
        cur.execute("INSERT INTO RUBRIQUE (pos, lib) VALUES (1, 'Entretien'), (2, 'Usager');")
        
        # Variables (Mode, Durée)
        cur.execute("INSERT INTO VARIABLE (pos, tab, rubrique, pos_r, lib, type_v, commentaire) VALUES (10, 'ENTRETIEN', 1, 1, 'MODE', 'MOD', 'Mode entretien');")
        cur.execute("INSERT INTO VARIABLE (pos, tab, rubrique, pos_r, lib, type_v, commentaire) VALUES (20, 'ENTRETIEN', 1, 2, 'DUREE', 'MOD', 'Durée');")

        # Selectbox Modalités
        modes = ["RDV", "Sans RDV", "Téléphone", "Mail", "Courrier", "Autre"]
        for idx, lbl in enumerate(modes):
            cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('ENTRETIEN', 10, %s, %s, %s)", (idx+1, idx+1, lbl))

        cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('ENTRETIEN', 20, 1, 1, '-15 min'), ('ENTRETIEN', 20, 2, 2, '+15 min');")

        cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('DEMANDE', 3, 1, 100, 'Logement');")
        cur.execute("INSERT INTO MODALITE (tab, pos, pos_m, code, lib_m) VALUES ('SOLUTION', 3, 1, 200, 'Information');")

    conn.close()