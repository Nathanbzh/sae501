# tests/test_analyse.py
# -*- coding: utf-8 -*-
import sys
import os
import pytest
import psycopg2
from streamlit.testing.v1 import AppTest
from database import LOCAL_DB_CONFIG

# Ajout du chemin racine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def inject_data_analyse():
    """
    Injecte des données factices pour que les graphiques aient quelque chose à afficher.
    """
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ENTRETIEN, DEMANDE, SOLUTION CASCADE;")
        # On insère des données qui correspondent aux MODALITE créées dans conftest
        cur.execute("""
            INSERT INTO ENTRETIEN (NUM, DATE_ENT, MODE, DUREE, SEXE, AGE) VALUES 
            (1001, '2024-01-15', 1, 1, 1, 1),
            (1002, '2024-02-20', 2, 2, 2, 2),
            (1003, '2024-03-10', 1, 1, 1, 3);
        """)
    conn.close()

def test_page_analyse_chargement(inject_data_analyse):
    """
    Vérifie que la page se charge sans erreur et affiche un graphique par défaut.
    """
    at = AppTest.from_file("pages/2_Analyse_Graphique.py")
    at.run()

    # 1. Pas d'erreur au lancement
    assert not at.exception, f"Exception levée : {at.exception}"
    
    # 2. Vérifie la présence du titre
    assert "Analyse Graphique" in at.title[0].value

    # 3. Vérification compatible (Workaround)
    charts = at.get("plotly_chart")
    assert len(charts) > 0, "Aucun graphique affiché"

def test_page_analyse_filtres(inject_data_analyse):
    """
    Teste l'interaction avec la sidebar (Filtres) et le changement de configuration.
    """
    at = AppTest.from_file("pages/2_Analyse_Graphique.py")
    at.run()

    # Changement de type de graphique
    if len(at.selectbox) > 0:
        at.selectbox[0].select_index(1).run()
        assert not at.exception

    # Ajout d'un filtre
    if len(at.multiselect) > 0:
        options = at.multiselect[0].options
        if options:
            at.multiselect[0].select(options[0]).run()
            assert len(at.multiselect) > 1, "Le sous-filtre n'est pas apparu"

def test_page_analyse_donnees_brutes(inject_data_analyse):
    at = AppTest.from_file("pages/2_Analyse_Graphique.py")
    at.run()
    assert len(at.dataframe) > 0