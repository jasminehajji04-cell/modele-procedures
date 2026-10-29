"""API de prédiction (Flask). Lancer : python api.py   (port défini dans info.json ou variable PORT)."""
import json
import os
from pathlib import Path

from flask import Flask, jsonify, request

try:                                    # import comme paquet (modeles.<nom>.api) ou comme script (python api.py)
    from . import preparation_modele as pm
except ImportError:
    import preparation_modele as pm

DOSSIER = Path(__file__).resolve().parent
INFO = json.loads((DOSSIER / "info.json").read_text(encoding="utf-8"))
b = pm.charger_modele(DOSSIER / "modele_final.joblib")
AVERTISSEMENT = "Estimation statistique, pas une recommandation clinique."

app = Flask(__name__)


@app.after_request
def autoriser_appels_navigateur(reponse):          # CORS ouvert : démonstration uniquement
    reponse.headers["Access-Control-Allow-Origin"] = "*"
    reponse.headers["Access-Control-Allow-Headers"] = "Content-Type"
    reponse.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return reponse


@app.get("/")
def accueil():
    return jsonify(message="API du modèle " + INFO["nom"], routes=["/health", "/info", "/predict", "/predict_batch"])


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/info")
def info():
    return jsonify(**INFO, mae_test=b["meta"]["mae_test"], date_entrainement=b["meta"]["date_entrainement"],
                   champs=b["colonnes_requises"], valeurs_par_defaut=b["defaults"], modalites=b["modalites"])


def _resultat(res):
    return {"cible": INFO["cible"], "prediction_brute": float(res["prediction_brute"]),
            "prediction_arrondie": int(res["prediction_arrondie"]),
            "erreur_typique_mae": round(b["meta"]["mae_test"], 3), "avertissement": AVERTISSEMENT}


@app.route("/predict", methods=["POST", "OPTIONS"])
def predict():
    if request.method == "OPTIONS":
        return "", 204
    corps = request.get_json(silent=True)
    if not isinstance(corps, dict) or not isinstance(corps.get("patient"), dict):
        return jsonify(erreur='Corps JSON attendu : {"patient": {...}}'), 400
    patient = {**b["defaults"], **corps["patient"]}          # champs absents = valeurs par défaut
    try:
        res = pm.predire(patient, b).iloc[0]
    except Exception as e:
        return jsonify(erreur=str(e)), 422
    return jsonify(_resultat(res))


@app.route("/predict_batch", methods=["POST", "OPTIONS"])
def predict_batch():
    if request.method == "OPTIONS":
        return "", 204
    corps = request.get_json(silent=True)
    if not isinstance(corps, dict) or not isinstance(corps.get("patients"), list):
        return jsonify(erreur='Corps JSON attendu : {"patients": [{...}, ...]}'), 400
    patients = [{**b["defaults"], **p} for p in corps["patients"]]
    try:
        res = pm.predire(patients, b)
    except Exception as e:
        return jsonify(erreur=str(e)), 422
    return jsonify(resultats=[_resultat(r) for _, r in res.iterrows()])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", INFO.get("port_api", 8001))))
