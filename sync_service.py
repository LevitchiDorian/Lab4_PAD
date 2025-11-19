# sync_service.py
import redis
import json
import psycopg2
import os

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

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=0,
)


def synchronize_data(message):
    try:
        notification = json.loads(message["data"])
        operation = notification.get("operation")
        payload = notification.get("data")
        source_db = notification.get("source_db")
        target_db_name = "db2" if source_db == "db1" else "db1"

        print(
            f"[Sync Service] Notificare '{operation}' de la '{source_db}'. Replicare în '{target_db_name}'..."
        )

        with psycopg2.connect(**DB_CONFIGS[target_db_name]) as conn:
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

    except Exception as e:
        print(f"EROARE în timpul sincronizării: {e}")


if __name__ == "__main__":
    pubsub = redis_client.pubsub()
    pubsub.subscribe("db_sync_channel")
    print("--- Serviciul de sincronizare (CRUD Ready) a pornit ---")
    for message in pubsub.listen():
        if message["type"] == "message":
            synchronize_data(message)
