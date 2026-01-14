# tests/test_export.py
# -*- coding: utf-8 -*-
import sys
import os
import pytest
import psycopg2
from streamlit.testing.v1 import AppTest
from database import LOCAL_DB_CONFIG

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def inject_data_export():
    """
    Injecte des données complètes pour tester l'export.
    """
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ENTRETIEN, DEMANDE, SOLUTION CASCADE;")
        
        # Donnée avec date précise
        cur.execute("INSERT INTO ENTRETIEN (NUM, DATE_ENT, MODE) VALUES (500, '2024-05-15', 1);")
        cur.execute("INSERT INTO DEMANDE (NUM, POS, NATURE) VALUES (500, 1, 100);")
        cur.execute("INSERT INTO SOLUTION (NUM, POS, NATURE) VALUES (500, 1, 200);")
        
    conn.close()

def test_onglet_export_global(inject_data_export):
    """Teste l'onglet 1."""
    at = AppTest.from_file("pages/3_Export_Donnees.py")
    at.run()

    # Si la page crashe (ImportError), on fail tout de suite
    if at.exception:
        pytest.fail(f"La page 3 a crashé : {at.exception}")

    # Sélection onglet 1
    at.tabs[0].run()
    
    # Sélection du mois
    ms_mois = at.multiselect[0]
    assert len(ms_mois.options) > 0, "Aucun mois trouvé dans le sélecteur"
    ms_mois.select(ms_mois.options[0]).run()

    # Vérification présence tableau
    assert len(at.dataframe) > 0
    
    # Vérification présence bouton (Compatible toutes versions)
    buttons = at.get("download_button")
    assert len(buttons) > 0, "Bouton de téléchargement introuvable"

def test_onglet_detail_dossier_succes(inject_data_export):
    """Teste l'onglet 2 (Succès)."""
    at = AppTest.from_file("pages/3_Export_Donnees.py")
    at.run()

    # Sélection onglet 2
    at.tabs[1].run()

    # Recherche dossier 500
    num_input = at.number_input[0]
    num_input.set_value(500).run()

    # Vérification : 3 tableaux (Entretien, Demande, Solution)
    assert len(at.dataframe) >= 3
    assert len(at.error) == 0

def test_onglet_detail_dossier_inconnu(inject_data_export):
    """Teste l'onglet 2 (Erreur)."""
    at = AppTest.from_file("pages/3_Export_Donnees.py")
    at.run()
    
    at.tabs[1].run()

    # Recherche dossier inexistant
    at.number_input[0].set_value(999999).run()

    assert len(at.error) > 0
    assert "n'existe pas" in at.error[0].value