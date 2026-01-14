# -*- coding: cp1252 -*-
import pytest
import psycopg2
import sys
import os
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

# Récupération sécurisée
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

@pytest.fixture(scope="session", autouse=True)
def init_db_schema():
    """
    S'assure que la table existe avant de lancer les tests.
    """
    conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
    conn.autocommit = True
    with conn.cursor() as cur:
        # Création de la table si elle n'existe pas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ENTRETIEN(
               NUM SERIAL PRIMARY KEY,
               DATE_ENT DATE,
               MODE SMALLINT,
               DUREE SMALLINT,
               SEXE SMALLINT,
               AGE SMALLINT,
               VIENT_PR SMALLINT,
               SIT_FAM INTEGER, 
               ENFANT SMALLINT,
               PROFESSION SMALLINT,
               RESS SMALLINT
            );
        """)
    conn.close()

@pytest.fixture(scope="function")
def db_connection():
    conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
    conn.autocommit = True
    yield conn
    conn.close()