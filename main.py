
import os
from load_balancer import app  

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"--- Load Balancer pornește pe portul {port} (Railway) ---")
    app.run(host="0.0.0.0", port=port)
