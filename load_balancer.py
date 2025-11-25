# load_balancer.py
from flask import Flask, request, send_from_directory
import requests
from itertools import cycle
import os

app = Flask(__name__)

# === CONFIG BACKEND SERVERS (Railway URLs) ===
servers_env = os.environ.get(
    "BACKEND_SERVERS",
    "https://server1-production-9ae3.up.railway.app,https://server2-production-00a0.up.railway.app",
)
SERVERS = [s.strip() for s in servers_env.split(",") if s.strip()]
server_pool = cycle(SERVERS)

# === CONFIG PENTRU HTML ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = "client_web.html"

print("=== BASE_DIR pentru load_balancer.py ===")
print(BASE_DIR)
print("=== Fișiere în BASE_DIR ===")
print(os.listdir(BASE_DIR))
print(f"=== HTML_FILE așteptat: {HTML_FILE} ===")


@app.route("/", methods=["GET"])
def index():
    """
    Returnează pagina HTML client_web.html din același director
    cu load_balancer.py.
    """
    print("[INFO] Trimit fișierul HTML:", HTML_FILE)
    return send_from_directory(BASE_DIR, HTML_FILE)


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def route_request(path):
    """
    Orice altă rută /employees, /employee/1 etc merge la unul din servere.
    """
    server_url = next(server_pool)
    print(f"Load Balancer -> Redirecționare către: {server_url}")

    try:
        resp = requests.request(
            method=request.method,
            url=f"{server_url}/{path}",
            headers={
                key: value
                for (key, value) in request.headers
                if key.lower() != "host"
            },
            data=request.get_data(),
            params=request.args,
        )
        return resp.content, resp.status_code, resp.headers.items()
    except requests.exceptions.RequestException as e:
        return f"Service Unavailable: {e}", 503


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"--- Load Balancer pornește pe portul {port} (Railway/local) ---")
    app.run(host="0.0.0.0", port=port)
