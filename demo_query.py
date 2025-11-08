"""
Simple demo script making HTTP requests to the running FastAPI server.
Run the server:
  uvicorn api.main:app --reload --port 8000
Then in another terminal:
  python demo_query.py
"""
import requests
import json

BASE = "http://localhost:8000"

def pretty(r):
    try:
        return json.dumps(r.json(), indent=2, ensure_ascii=False)
    except Exception:
        return str(r.text)

def run_demo():
    print("[1] Health check")
    r = requests.get(f"{BASE}/health")
    print(pretty(r))

    concept = "freedom"
    print(f"\n[2] Timeline for concept='{concept}'")
    r = requests.get(f"{BASE}/timeline", params={"concept": concept, "top_n": 5})
    print(pretty(r))

    era = "1900s"
    print(f"\n[3] Era-specific top for {concept} / {era}")
    r = requests.get(f"{BASE}/era", params={"concept": concept, "era": era, "top_n": 6})
    print(pretty(r))

    print("\n[4] Symbol pairs (example 'eye')")
    r = requests.get(f"{BASE}/symbol-pairs", params={"symbol": "eye"})
    print(pretty(r))

if __name__ == "__main__":
    run_demo()
