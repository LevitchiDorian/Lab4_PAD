# load_balancer.py
from flask import Flask, request
import requests
from itertools import cycle
import os

app = Flask(__name__)

# BACKEND_SERVERS va fi un string de forma:
# "https://server1.up.railway.app,https://server2.up.railway.app"
servers_env = os.environ.get("BACKEND_SERVERS", "http://localhost:5001,http://localhost:5002")
SERVERS = [s.strip() for s in servers_env.split(",") if s.strip()]
server_pool = cycle(SERVERS)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_request(path):
    server_url = next(server_pool)
    print(f"Load Balancer -> Redirecționare către: {server_url}")
    try:
        resp = requests.request(
            method=request.method,
            url=f"{server_url}/{path}",
            headers={key: value for (key, value) in request.headers if key.lower() != 'host'},
            data=request.get_data(),
            params=request.args
        )
        return (resp.content, resp.status_code, resp.headers.items())
    except requests.exceptions.RequestException as e:
        return f"Service Unavailable: {e}", 503


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"--- Load Balancer pornește pe portul {port} ---")
    app.run(host="0.0.0.0", port=port)
