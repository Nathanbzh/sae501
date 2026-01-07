import psycopg2

# --- CONFIGURATION (La même que celle qui a fonctionné) ---
DB_HOST = "localhost"
DB_PORT = "5437"           # Port 5437 validé
DB_USER = "pgis"       
DB_PASS = "pgis"   
DB_NAME = "DB_MaisonDuDroit"  # On se connecte DIRECTEMENT à la base créée

def verifier_donnees():
    print(f"🕵️‍♂️ Vérification des données dans '{DB_NAME}' sur le port {DB_PORT}...")
    
    conn = None
    try:
        # Connexion à la base spécifique
        conn = psycopg2.connect(
            dbname=DB_NAME, 
            user=DB_USER, 
            password=DB_PASS, 
            host=DB_HOST, 
            port=DB_PORT 
        )
        cur = conn.cursor()

        # 1. COMPTER LE NOMBRE TOTAL DE LIGNES
        cur.execute("SELECT COUNT(*) FROM ENTRETIEN")
        total_count = cur.fetchone()[0]
        print(f"\n📊 NOMBRE TOTAL DE LIGNES IMPORTÉES : {total_count}")
        print("-" * 50)

        # 2. AFFICHER UN ÉCHANTILLON (SELECT * LIMIT 5)
        # On limite à 5 pour ne pas inonder votre terminal
        cur.execute("SELECT * FROM ENTRETIEN LIMIT 5")
        rows = cur.fetchall()
        
        # Récupérer les noms des colonnes pour un affichage propre
        colnames = [desc[0] for desc in cur.description]
        print(f"| {' | '.join(colnames)} |") # Affiche l'entête
        print("-" * 50)

        for row in rows:
            # Convertit chaque élément en string pour l'affichage
            row_str = " | ".join(map(str, row))
            print(f"| {row_str} |")

        print("-" * 50)
        print("✅ Vérification terminée.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Erreur lors de la lecture : {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verifier_donnees()