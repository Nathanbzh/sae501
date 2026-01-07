import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# --- CONFIGURATION ---
DB_HOST = "localhost"
DB_PORT = "5437"           # Vérifiez votre port (5432 ou 5437)
DB_USER = "pgis"
DB_PASS = "pgis"
DB_NAME = "DB_MaisonDuDroit"
CSV_PATH = r"H:/Projetdroit/tentative.csv" # Chemin de votre fichier

def reset_and_import():
    print(f"🔌 Connexion au serveur sur le port {DB_PORT}...")
    
    # 1. CRÉATION DE LA BASE (Si elle n'existe pas)
    try:
        conn_sys = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        conn_sys.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur_sys = conn_sys.cursor()
        
        cur_sys.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_NAME,))
        if not cur_sys.fetchone():
            cur_sys.execute(f"CREATE DATABASE \"{DB_NAME}\"")
            print(f"✅ Base de données '{DB_NAME}' créée.")
        
        cur_sys.close()
        conn_sys.close()
    except Exception as e:
        print(f"❌ Erreur connexion serveur : {e}")
        return

    # 2. CRÉATION DE LA TABLE ENTRETIEN (VOTRE DDL)
    print(f"🚀 Connexion à '{DB_NAME}'...")
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()

        print("🧹 Suppression de l'ancienne table...")
        cur.execute("DROP TABLE IF EXISTS ENTRETIEN CASCADE;")
        conn.commit()

        print("🔨 Création de la table ENTRETIEN...")
        # J'ai ajouté DEFAULT CURRENT_DATE pour DATE_ENT car elle n'est pas dans votre CSV
        create_table_sql = """
            CREATE TABLE ENTRETIEN(
               NUM SERIAL,
               DATE_ENT DATE DEFAULT CURRENT_DATE,
               MODE SMALLINT,
               DUREE SMALLINT,
               SEXE SMALLINT,
               AGE SMALLINT,
               VIENT_PR SMALLINT,
               SIT_FAM VARCHAR(2),
               ENFANT SMALLINT,
               MODELE_FAM SMALLINT,
               PROFESSION SMALLINT,
               RESS SMALLINT,
               ORIGINE VARCHAR(2),
               COMMUNE VARCHAR(50),
               PARTENAIRE VARCHAR(50),
               PRIMARY KEY(NUM)
            );
            
            COMMENT ON TABLE ENTRETIEN IS 'Table de stockage des données';
            COMMENT ON COLUMN ENTRETIEN.MODE IS '1:RDV; 2:Sans RDV...';
            -- (Les commentaires sont facultatifs pour le fonctionnement mais utiles)
        """
        cur.execute(create_table_sql)
        conn.commit()

        # 3. IMPORTATION DU CSV
        print(f"📝 Importation du fichier : {CSV_PATH}")
        
        # Commande COPY adaptée à votre liste de colonnes CSV
        sql_copy = """
            COPY ENTRETIEN (NUM, MODE, DUREE, SEXE, AGE, VIENT_PR, SIT_FAM, ENFANT, MODELE_FAM, PROFESSION, RESS, ORIGINE, COMMUNE, PARTENAIRE)
            FROM STDIN
            WITH (
                FORMAT CSV, 
                DELIMITER ';', 
                HEADER true, 
                ENCODING 'WIN1252'
            )
        """
        
        try:
            with open(CSV_PATH, 'rb') as f:
                cur.copy_expert(sql_copy, f)
                conn.commit()
                print("✅ Importation terminée avec succès !")
                
                # Petit check de contrôle
                cur.execute("SELECT COUNT(*) FROM ENTRETIEN")
                count = cur.fetchone()[0]
                print(f"📊 Nombre de lignes en base : {count}")
                
        except FileNotFoundError:
            print(f"❌ ERREUR : Fichier introuvable : {CSV_PATH}")
        except psycopg2.DataError as e:
            print(f"❌ ERREUR DE DONNÉES : {e}")
            print("💡 Conseil : Vérifiez que votre CSV contient bien des CHIFFRES pour les colonnes SMALLINT (Mode, Duree, etc.) et pas du texte.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Erreur générale : {e}")

if __name__ == "__main__":
    reset_and_import()