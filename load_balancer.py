# load_balancer.py
from flask import Flask, request, send_from_directory
import requests
from itertools import cycle
import os

app = Flask(__name__)

# ------------------- CONFIG BACKEND-URI -------------------
servers_env = os.environ.get(
    "BACKEND_SERVERS",
    "https://server1-production-9ae3.up.railway.app,https://server2-production-00a0.up.railway.app"
)
SERVERS = [s.strip() for s in servers_env.split(",") if s.strip()]
server_pool = cycle(SERVERS)

# numele fișierului HTML (poți schimba în client_web.html dacă vrei)
HTML_FILE = os.environ.get("CLIENT_HTML_FILE", "client_web.html")

# la start, afișăm ce fișiere sunt lângă load_balancer.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("=== BASE_DIR pentru load_balancer.py ===")
print(BASE_DIR)
print("=== Fișiere în BASE_DIR ===")
print(os.listdir(BASE_DIR))
print("=== HTML_FILE așteptat:", HTML_FILE, "===")


# ------------------- PAGINA HTML -------------------
@app.route("/", methods=["GET"])
def index():
    html_path = os.path.join(BASE_DIR, HTML_FILE)

    # dacă fișierul NU există în container, întoarcem mesaj clar
    if not os.path.exists(html_path):
        msg = (
            f"[ERROR] Fișierul HTML '{HTML_FILE}' NU a fost găsit în {BASE_DIR}.\n"
            f"Fișiere găsite: {os.listdir(BASE_DIR)}"
        )
        print(msg)
        return (
            "<h1>Fișier HTML lipsă</h1>"
            "<p>Aplicatia rulează, dar nu găsește pagina client.</p>"
            f"<p>Caută: <b>{HTML_FILE}</b> în directorul <b>{BASE_DIR}</b>.</p>",
            500,
        )

    print(f"[INFO] Trimit fișierul HTML: {HTML_FILE}")
    return send_from_directory(BASE_DIR, HTML_FILE)


# ------------------- PROXY PENTRU API -------------------
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def route_request(path: str):
    server_url = next(server_pool)
    print(f"Load Balancer -> Redirecționare către: {server_url}")

    try:
        resp = requests.request(
            method=request.method,
            url=f"{server_url}/{path}",
            headers={k: v for (k, v) in request.headers if k.lower() != "host"},
            data=request.get_data(),
            params=request.args,
        )
        return resp.content, resp.status_code, resp.headers.items()
    except requests.exceptions.RequestException as e:
        print("[ERROR] Eroare la redirect:", e)
        return f"Service Unavailable: {e}", 503


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"--- Load Balancer pornește pe portul {port} (Railway/local) ---")
    app.run(host="0.0.0.0", port=port)
