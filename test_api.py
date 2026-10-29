"""Teste l'API : lancer d'abord `python api.py` dans modeles/<nom>/, puis `python test_api.py [url]`."""
import json
import sys
from pathlib import Path

import requests

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
exemple = json.loads((Path(__file__).parent / "exemple_requete.json").read_text(encoding="utf-8"))

print("GET /health        ->", requests.get(f"{URL}/health", timeout=10).json())
i = requests.get(f"{URL}/info", timeout=10).json()
print("GET /info          ->", i["nom"], "| cible :", i["cible"], "| MAE test :", i["mae_test"])
r = requests.post(f"{URL}/predict", json=exemple, timeout=30)
print("POST /predict      ->", r.status_code, r.json())
r = requests.post(f"{URL}/predict", json={"patient": {"num_medications": "abc"}}, timeout=30)
print("POST /predict (erreur volontaire) ->", r.status_code, r.json())
