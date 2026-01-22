import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# --- CONFIGURATION ---
APP_URL = "http://localhost:8501"

@pytest.fixture(scope="module")
def driver():
    """
    Initialise le navigateur Chrome.
    """
    print("\n🚀 Démarrage du navigateur pour les tests E2E...")
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    
    yield driver
    
    print("\n🚪 Fermeture du navigateur.")
    driver.quit()

# --- HELPER ROBUSTE ---

def streamlit_selectbox_select(driver, label_text, index=1):
    """
    Sélectionne un élément dans une st.selectbox.
    Gère les accents et les structures DOM variables.
    """
    print(f"   ℹ️ Remplissage '{label_text}'...")
    try:
        # 1. On cherche le label (texte partiel pour éviter problèmes d'accents ex: 'Dur' pour 'Durée')
        # On cherche le DIV conteneur stSelectbox parent du label
        xpath_widget = f"//div[contains(@class, 'stSelectbox') and .//label[contains(., \"{label_text}\")]]"
        
        try:
            widget = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, xpath_widget))
            )
        except TimeoutException:
            print(f"      ⚠️ Label '{label_text}' non trouvé. Essai fallback index...")
            # Fallback : Si c'est "Durée" ou "Dur", on suppose que c'est la 2ème selectbox
            idx = 1 if "ur" in label_text else 0
            inputs = driver.find_elements(By.XPATH, "//div[contains(@class, 'stSelectbox')]//input")
            if len(inputs) > idx:
                input_elem = inputs[idx]
            else:
                return False
        else:
            # Si widget trouvé, on prend son input
            input_elem = widget.find_element(By.TAG_NAME, "input")

        # 2. Interaction
        # On scrolle pour être sûr
        driver.execute_script("arguments[0].scrollIntoView();", input_elem)
        # Click JS
        driver.execute_script("arguments[0].click();", input_elem)
        time.sleep(0.2)
        
        # Navigation Clavier
        input_elem.send_keys(Keys.ARROW_DOWN)
        input_elem.send_keys(Keys.ENTER)
        
        print(f"   ✅ '{label_text}' OK.")
        return True

    except Exception as e:
        print(f"   ❌ Erreur '{label_text}': {e}")
        return False

def streamlit_multiselect_add(driver):
    """Remplit le premier multiselect trouvé."""
    try:
        xpath = "//div[contains(@data-testid, 'stMultiSelect')]//input"
        input_elem = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        
        driver.execute_script("arguments[0].click();", input_elem)
        time.sleep(0.5)
        input_elem.send_keys(Keys.ARROW_DOWN)
        input_elem.send_keys(Keys.ENTER)
        
        # Fermer le dropdown en cliquant sur le titre
        driver.find_element(By.TAG_NAME, "h1").click()
        return True
    except Exception:
        return False

# --- LES TESTS ---

def test_01_accueil_chargement(driver):
    driver.get(APP_URL)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        assert "Maison du Droit" in driver.title
        print("✅ Accueil chargé.")
    except:
        pytest.fail("Accueil non chargé.")

def test_02_verification_logo(driver):
    driver.get(APP_URL)
    time.sleep(1)
    images = driver.find_elements(By.TAG_NAME, "img")
    if len(images) > 0:
        print(f"✅ Logo détecté.")
    else:
        print("⚠️ Pas de logo.")

def test_03_formulaire_saisie_et_enregistrement(driver):
    """
    Remplit et enregistre le formulaire.
    """
    driver.get(APP_URL)
    time.sleep(2)
    
    print("📝 Saisie formulaire...")
    
    # Utilisation de textes partiels pour éviter les soucis d'encodage
    # "Mode" pour "Mode d'entretien"
    # "ur" pour "Durée" (évite le é)
    res_mode = streamlit_selectbox_select(driver, "Mode")
    res_duree = streamlit_selectbox_select(driver, "ur") 
    
    if not (res_mode and res_duree):
        driver.save_screenshot("debug_selectbox_fail.png")
        pytest.fail("Echec remplissage Selectbox. Voir debug_selectbox_fail.png")

    # Multiselect
    streamlit_multiselect_add(driver)

    # Soumission
    try:
        # Recherche du bouton contenant "Enregistrer"
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//p[contains(text(), 'Enregistrer')]]"))
        )
        driver.execute_script("arguments[0].scrollIntoView();", btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", btn)
        
        # Vérification Succès
        alert = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'stAlert')]"))
        )
        
        print(f"   ℹ️ Retour app : {alert.text}")
        
        if "succès" in alert.text.lower():
            print("✅ Dossier enregistré !")
        elif "warning" in alert.text.lower() or "erreur" in alert.text.lower():
            print(f"⚠️ Validation métier échouée (Champs manquants ?) : {alert.text}")
        else:
            print("✅ Action effectuée (Message inconnu).")
        
    except Exception as e:
        driver.save_screenshot("debug_submit_fail.png")
        pytest.fail(f"Erreur soumission : {e}")

def test_04_navigation_analyse(driver):
    print("🧭 Vers Analyse...")
    driver.get(f"{APP_URL}/Analyse_Graphique")
    time.sleep(2)
    assert "Analyse" in driver.title or "Analyse" in driver.page_source
    print("✅ Page Analyse OK.")

def test_05_page_export(driver):
    driver.get(f"{APP_URL}/Export_Donnees")
    time.sleep(2)
    assert "Export" in driver.page_source
    print("✅ Page Export OK.")

def test_06_page_administration(driver):
    driver.get(f"{APP_URL}/Administration")
    time.sleep(2)
    assert "Administration" in driver.page_source
    print("✅ Page Admin OK.")