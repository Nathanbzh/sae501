# tests/test_administration.py
# -*- coding: utf-8 -*-
import sys
import os
import pytest
import psycopg2
from streamlit.testing.v1 import AppTest
from database import LOCAL_DB_CONFIG

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_admin_page_load():
    at = AppTest.from_file("pages/4_Administration.py")
    at.run()
    assert not at.exception

def test_admin_add_modality():
    """Teste l'ajout d'une modalité."""
    at = AppTest.from_file("pages/4_Administration.py")
    at.run()

    if at.radio:
        at.radio[0].set_value("Ajouter une Modalité").run()

    # Sélection de la variable MODE
    if at.selectbox:
        options = at.selectbox[0].options
        opt_mode = next((o for o in options if "MODE" in o), None)
        if opt_mode:
            at.selectbox[0].select(opt_mode).run()

    # Ajout valeur
    new_mod_name = "Test_Visio_Auto"
    if at.text_input:
        at.text_input[0].set_value(new_mod_name).run()

    # Clic Ajouter
    buttons = at.button
    btn_add = next((b for b in buttons if "Ajouter" in b.label), None)
    if btn_add:
        btn_add.click().run()

    # Vérification Erreurs
    if at.error:
        pytest.fail(f"L'application a retourné une erreur : {at.error[0].value}")

    # Vérification BDD
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM MODALITE WHERE lib_m = %s", (new_mod_name,))
        count = cur.fetchone()[0]
    conn.close()
    
    assert count == 1, "La modalité n'a pas été trouvée en BDD."

def test_admin_add_variable():
    """Teste la création d'une variable (colonne)."""
    at = AppTest.from_file("pages/4_Administration.py")
    at.run()

    # 1. Sélection mode Création
    if at.radio:
        at.radio[0].set_value("Créer une nouvelle Variable (Colonne)").run()

    # 2. Remplissage
    var_label = "Ma Variable Test"
    var_col_name = "TEST_VAR_AUTO"
    
    # On s'assure de trouver les inputs visibles
    # Streamlit AppTest peut voir tous les inputs, même ceux cachés des autres onglets si le script n'est pas bien isolé,
    # mais ici le 'if' python les filtre.
    inputs = at.text_input
    if len(inputs) >= 2:
        inputs[0].set_value(var_label).run()
        inputs[1].set_value(var_col_name).run()
    
    if len(at.selectbox) >= 2:
        at.selectbox[0].select_index(0).run() # Rubrique
        at.selectbox[1].select("Texte libre (CHAINE)").run() # Type

    # 3. Soumission
    buttons = at.button
    btn_create = next((b for b in buttons if "Créer la variable" in b.label), None)
    
    if btn_create:
        btn_create.click().run()

    # 4. Vérification Erreurs (CRITIQUE : C'est ici qu'on voit si SQL plante)
    if at.error:
        pytest.fail(f"Erreur affichée dans l'app : {at.error[0].value}")

    # 5. Vérification BDD
    # On ne vérifie PAS at.success car st.rerun() l'efface immédiatement.
    conn = psycopg2.connect(**LOCAL_DB_CONFIG)
    with conn.cursor() as cur:
        # Vérif config
        cur.execute("SELECT count(*) FROM VARIABLE WHERE lib = %s", (var_col_name,))
        cnt_config = cur.fetchone()[0]
        
        # Vérif colonne physique
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='entretien' AND column_name=%s
        """, (var_col_name.lower(),))
        col_physique = cur.fetchone()
        
    conn.close()

    assert cnt_config == 1, "Variable absente de la table VARIABLE."
    assert col_physique is not None, "Colonne absente de la table ENTRETIEN."