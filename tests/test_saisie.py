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
        sb.select_index(1).run()

    # 3. Remplissage Radio
    for r in at.radio:
        if r.options:
            r.set_value(r.options[0]).run()

    # 4. Remplissage Multiselect (Champs obligatoires)
    if len(at.multiselect) >= 2:
        at.multiselect[0].select("Logement").run()      # Nature demande
        at.multiselect[1].select("Information").run()   # Solution

    # 5. Clic sur le bouton Sauvegarder
    at.button[0].click().run()

    # 6. Vérifications des messages
    
    # Aucune erreur ne doit être affichée
    assert len(at.error) == 0, f"Une erreur est affichée : {at.error[0].value if at.error else ''}"
    
    # On récupère tous les messages de succès
    all_success_messages = [s.value for s in at.success]
    
    # --- CORRECTION ROBUSTE ---
    # On cherche une partie de la phrase qui ne contient PAS d'accents compliqués
    # ou on s'assure que la correspondance est partielle.
    # Ton message est : "✅ Dossier complet n° **1** enregistré avec succès !"
    
    found_validation = any("Dossier complet" in msg for msg in all_success_messages)
    
    assert found_validation, f"Message de validation introuvable. Messages reçus : {all_success_messages}"

    # 7. Nettoyage de la Base de Données
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT num FROM entretien ORDER BY num DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM entretien WHERE num = %s", (row[0],))
        conn.commit()
    conn.close()

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
    at.button[0].click().run()

    # 3. Vérifications
    assert len(at.warning) > 0, "L'application n'a pas affiché de warning."
    
    all_success_messages = [s.value for s in at.success]
    # On vérifie que le message de validation N'EST PAS présent
    found_validation = any("Dossier complet" in msg for msg in all_success_messages)
    
    assert not found_validation, "L'application a validé le dossier alors qu'il est incomplet !"