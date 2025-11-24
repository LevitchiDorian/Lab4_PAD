# sync_service.py
import os
import json
import redis
import psycopg2


# Config pentru cele două baze de date
DB_CONFIGS = {
    "db1": {
        "host": os.environ.get("DB1_HOST", "localhost"),
        "port": os.environ.get("DB1_PORT", "5431"),
        "dbname": os.environ.get("DB1_NAME", "db1"),
        "user": os.environ.get("DB1_USER", "app_user"),
        "password": os.environ.get("DB1_PASSWORD", "app_password"),
    },
    "db2": {
        "host": os.environ.get("DB2_HOST", "localhost"),
        "port": os.environ.get("DB2_PORT", "5432"),
        "dbname": os.environ.get("DB2_NAME", "db2"),
        "user": os.environ.get("DB2_USER", "app_user"),
        "password": os.environ.get("DB2_PASSWORD", "app_password"),
    },
}

# Config pentru Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")  # poate fi None

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=0,
)


def synchronize_data(message):
    """
    Funcția care primește mesajul din Redis și îl aplică pe baza de date țintă.
    """
    try:
        # Mesajele de la pubsub au mai multe tipuri; noi vrem doar cele cu type='message'
        if message.get("type") != "message":
            return

        notification = json.loads(message["data"])

        operation = notification.get("operation")
        payload = notification.get("data")
        source_db = notification.get("source_db")

        if not operation or not payload or not source_db:
            print("[Sync Service] Mesaj incomplet, ignor...")
            return

        # Dacă vine de la db1 -> replicăm în db2
        # Dacă vine de la db2 -> replicăm în db1
        target_db_name = "db2" if source_db == "db1" else "db1"

        print(
            f"[Sync Service] Notificare '{operation}' de la '{source_db}'. "
            f"Replicare în '{target_db_name}'..."
        )

        db_config = DB_CONFIGS.get(target_db_name)
        if not db_config:
            print(f"[Sync Service] Config lipsă pentru {target_db_name}, ignor...")
            return

        with psycopg2.connect(**db_config) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                if operation == "insert":
                    sql = """
                        INSERT INTO employees (id, name, position)
                        VALUES (%(id)s, %(name)s, %(position)s)
                        ON CONFLICT (id) DO NOTHING
                    """
                    cursor.execute(sql, payload)
                    print(f"  -> Succes INSERT: ID {payload.get('id')} replicat.")

                elif operation == "update":
                    sql = """
                        UPDATE employees
                        SET name = %(name)s, position = %(position)s
                        WHERE id = %(id)s
                    """
                    cursor.execute(sql, payload)
                    print(f"  -> Succes UPDATE: ID {payload.get('id')} replicat.")

                elif operation == "delete":
                    sql = "DELETE FROM employees WHERE id = %(id)s"
                    cursor.execute(sql, payload)
                    print(f"  -> Succes DELETE: ID {payload.get('id')} replicat.")

                else:
                    print(f"[Sync Service] Operație necunoscută: {operation}")

    except Exception as e:
        print(f"EROARE în timpul sincronizării: {e}")


if __name__ == "__main__":
    print("--- Serviciul de sincronizare (CRUD Ready) a pornit ---")
    pubsub = redis_client.pubsub()
    pubsub.subscribe("db_sync_channel")
    for message in pubsub.listen():
        synchronize_data(message)
