import pandas as pd
from datetime import date
from exportation_base import export_entretien


def test_export_entretien_ok(mocker, tmp_path):
    # 🔹 Mock de la connexion PostgreSQL
    mock_conn = mocker.Mock()
    mocker.patch("psycopg2.connect", return_value=mock_conn)

    # 🔹 Faux DataFrame retourné par pandas.read_sql
    fake_df = pd.DataFrame({
        "id": [1, 2, 3],
        "date_ent": [
            "2024-01-01",
            "2024-04-05",
            "2024-03-10"
        ]
    })

    mocker.patch("pandas.read_sql", return_value=fake_df)

    # 🔹 Fichier temporaire pour l’export
    output_file = tmp_path / "entretien.csv"

    # 🔹 Paramètres de connexion (FAKE)
    conn_params = {
        "host": "localhost",
        "database": "test_db",
        "user": "test_user",
        "password": "test_password",
        "port": 5432
    }

    # ▶️ Exécution de la fonction testée
    result = export_entretien(
        conn_params=conn_params,
        date_debut=date(2024, 1, 1),
        date_fin=date(2024, 12, 31),
        colonne_date="date_ent",
        fichier_csv=str(output_file)
    )

    # ✅ Assertions
    assert result == 3                    # nombre de lignes exportées
    assert output_file.exists()           # fichier CSV créé
    mock_conn.close.assert_called_once()  # connexion fermée
