# -*- coding: utf-8 -*-
import sys
import os
from streamlit.testing.v1 import AppTest
from database import get_db_connection

# Ajout du chemin racine pour importer database.py correctement
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_integration_formulaire_succes():
    """
    Test Cas Passant : Remplissage complet et sauvegarde du formulaire.
    """
    at = AppTest.from_file("Accueil.py")
    at.run()

    # 1. Vérification que les selectbox existent
    assert len(at.selectbox) > 0, "Aucune selectbox trouvée. Vérifiez le conftest."

    # 2. Remplissage Selectbox
    # On prend l'index 1 car l'index 0 est souvent "Sélectionner"
    for sb in at.selectbox:
        if sb.options and len(sb.options) > 1:
            sb.select_index(1).run()
        elif sb.options:
            sb.select_index(0).run()

    # 3. Remplissage Radio
    for r in at.radio:
        if r.options:
            r.set_value(r.options[0]).run()

    # 4. Remplissage Multiselect (Champs obligatoires)
    if len(at.multiselect) >= 2:
        # On essaie de sélectionner la première option disponible
        if at.multiselect[0].options:
            at.multiselect[0].select(at.multiselect[0].options[0]).run()
        if at.multiselect[1].options:
            at.multiselect[1].select(at.multiselect[1].options[0]).run()

    # 5. Clic sur le bouton Sauvegarder
    if at.button:
        at.button[0].click().run()

    # 6. Vérifications des messages
    # Aucune erreur ne doit être affichée
    assert len(at.error) == 0, f"Une erreur est affichée : {at.error[0].value if at.error else ''}"
    
    # On récupère tous les messages de succès
    all_success_messages = [s.value for s in at.success]
    
    # Validation souple du message
    found_validation = any("enregistré avec succès" in msg for msg in all_success_messages)
    
    assert found_validation, f"Message de validation introuvable. Messages reçus : {all_success_messages}"

    # 🛑 SECTION DE NETTOYAGE SUPPRIMÉE : Les données restent en base 🛑

def test_validation_champs_manquants():
    """
    Test Cas Erreur : On ne remplit rien.
    """
    at = AppTest.from_file("Accueil.py")
    at.run()

    # 1. On vide le champ obligatoire
    if len(at.multiselect) > 0:
        at.multiselect[0].set_value([]).run()

    # 2. Clic sur Sauvegarder
    if at.button:
        at.button[0].click().run()

    # 3. Vérifications
    assert len(at.warning) > 0, "L'application n'a pas affiché de warning."
    
    all_success_messages = [s.value for s in at.success]
    found_validation = any("succès" in msg for msg in all_success_messages)
    
    assert not found_validation, "L'application a validé le dossier alors qu'il est incomplet !"