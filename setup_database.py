# setup_databases.py
import psycopg2
import time
import os

ADMIN_CONFIGS = {
    "db1": {
        "host": os.environ.get("DB1_ADMIN_HOST", "localhost"),
        "port": os.environ.get("DB1_ADMIN_PORT", "5431"),
        "dbname": os.environ.get("DB1_ADMIN_NAME", "db1"),
        "user": os.environ.get("DB1_ADMIN_USER", "postgres_admin"),
        "password": os.environ.get("DB1_ADMIN_PASSWORD", "admin_password"),
    },
    "db2": {
        "host": os.environ.get("DB2_ADMIN_HOST", "localhost"),
        "port": os.environ.get("DB2_ADMIN_PORT", "5432"),
        "dbname": os.environ.get("DB2_ADMIN_NAME", "db2"),
        "user": os.environ.get("DB2_ADMIN_USER", "postgres_admin"),
        "password": os.environ.get("DB2_ADMIN_PASSWORD", "admin_password"),
    },
}

APP_USER = os.environ.get("APP_USER", "app_user")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "app_password")


def wait_for_db(config, db_label):
    for i in range(10):
        try:
            psycopg2.connect(**config)
            print(f" Conexiune reușită la baza de date '{db_label}'.")
            return True
        except psycopg2.OperationalError:
            print(f" Aștept baza de date '{db_label}'... ({i+1}/10)")
            time.sleep(3)
    return False


def setup_databases():
    for db_label, admin_config in ADMIN_CONFIGS.items():
        print(f"\n--- Procesare bază de date '{db_label}' ---")
        if not wait_for_db(admin_config, db_label):
            print(f" EROARE: Nu s-a putut stabili conexiunea cu '{db_label}'. Abort.")
            continue

        with psycopg2.connect(**admin_config) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname='{APP_USER}'")
                if not cursor.fetchone():
                    print(f"  - Creare utilizator '{APP_USER}'...")
                    cursor.execute(f"CREATE USER {APP_USER} WITH PASSWORD '{APP_PASSWORD}';")
                else:
                    print(f"  - Utilizatorul '{APP_USER}' deja există.")

                cursor.execute(
                    f"GRANT ALL PRIVILEGES ON DATABASE {admin_config['dbname']} TO {APP_USER};"
                )
                print(f"  - Privilegii acordate pentru '{APP_USER}'.")

                print(f"  - Creare tabelă 'employees'...")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS employees (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        position VARCHAR(100)
                    );
                """
                )
                cursor.execute(
                    f"GRANT ALL PRIVILEGES ON TABLE employees TO {APP_USER};"
                )
                cursor.execute(
                    "SELECT 1 FROM pg_class WHERE relname='employees_id_seq';"
                )
                cursor.execute(
                    f"GRANT USAGE, SELECT ON SEQUENCE employees_id_seq TO {APP_USER};"
                )
    print("\n Setup-ul bazelor de date a fost finalizat cu succes!")


if __name__ == "__main__":
    setup_databases()
