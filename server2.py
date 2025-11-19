from flask import Flask, request, jsonify, make_response
import psycopg2
import redis
import json
import os

SERVER_PORT = int(os.environ.get("PORT", 5002))
DB_NAME = os.environ.get("DB_NAME", "db2")
app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": DB_NAME,
    "user": os.environ.get("DB_USER", "app_user"),
    "password": os.environ.get("DB_PASSWORD", "app_password"),
}

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")

redis_cache = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=0,
    decode_responses=True,
)

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def create_response(data, status_code):
    response = make_response(jsonify(data), status_code)
    response.headers["X-Database-Info"] = f"Operat pe DB: {DB_NAME} (Server Port: {SERVER_PORT})"
    return response


@app.route("/employee/<int:employee_id>", methods=["GET"])
def get_employee(employee_id):
    cache_key = f"employee:{employee_id}"
    if cached_data := redis_cache.get(cache_key):
        return create_response(json.loads(cached_data), 200)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, position FROM employees WHERE id = %s",
                (employee_id,),
            )
            employee = cursor.fetchone()

    if employee:
        data = {"id": employee[0], "name": employee[1], "position": employee[2]}
        redis_cache.setex(cache_key, 3600, json.dumps(data))
        return create_response(data, 200)
    return create_response({"error": "Employee not found"}, 404)


@app.route("/employees", methods=["GET"])
def get_all_employees():
    employees_list = []
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, position FROM employees ORDER BY id")
            for row in cursor.fetchall():
                employees_list.append(
                    {"id": row[0], "name": row[1], "position": row[2]}
                )
    return create_response(employees_list, 200)


@app.route("/employee", methods=["POST"])
def add_employee():
    data = request.get_json()
    employee_id = redis_cache.incr("employee_id_counter")

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO employees (id, name, position) VALUES (%s, %s, %s)",
                (employee_id, data["name"], data["position"]),
            )

    new_data = {"id": employee_id, "name": data["name"], "position": data["position"]}
    notification = {
        "operation": "insert",
        "data": new_data,
        "source_db": DB_NAME,
    }
    redis_cache.publish("db_sync_channel", json.dumps(notification))
    return create_response(new_data, 201)


@app.route("/employee/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):
    data = request.get_json()

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE employees SET name = %s, position = %s WHERE id = %s",
                (data["name"], data["position"], employee_id),
            )
            if cursor.rowcount == 0:
                return create_response(
                    {"error": "Employee not found to update"}, 404
                )

    updated_data = {
        "id": employee_id,
        "name": data["name"],
        "position": data["position"],
    }
    notification = {
        "operation": "update",
        "data": updated_data,
        "source_db": DB_NAME,
    }
    redis_cache.publish("db_sync_channel", json.dumps(notification))
    redis_cache.delete(f"employee:{employee_id}")
    return create_response(updated_data, 200)


@app.route("/employee/<int:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
            if cursor.rowcount == 0:
                return create_response(
                    {"error": "Employee not found to delete"}, 404
                )

    notification = {
        "operation": "delete",
        "data": {"id": employee_id},
        "source_db": DB_NAME,
    }
    redis_cache.publish("db_sync_channel", json.dumps(notification))
    redis_cache.delete(f"employee:{employee_id}")
    return create_response({"success": True, "deleted_id": employee_id}, 200)


if __name__ == "__main__":
    print(f"--- Server 1 pornește pe portul {SERVER_PORT} ---")
    app.run(host="0.0.0.0", port=SERVER_PORT)
