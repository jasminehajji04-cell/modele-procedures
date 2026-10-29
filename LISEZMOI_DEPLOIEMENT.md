# Déploiement du modèle « Procédures » sur Render

**But** : héberger l'API en ligne pour obtenir une URL publique, utilisable depuis le site (au lieu de `127.0.0.1`).

## Étapes rapides
1. Créer un dépôt GitHub et y mettre **tout le contenu** de ce dossier à la racine (`render.yaml` doit être visible à la racine du dépôt).
2. Sur render.com : **New > Blueprint** > choisir le dépôt > valider.
3. Attendre le build. Récupérer l'URL (`https://....onrender.com`).
4. Tester : ouvrir `https://<url>/health` (réponse attendue : `{"status":"ok"}`), puis `python test_api.py https://<url>`.
5. Dans le site, appeler `POST https://<url>/predict` avec `{"patient": {...}}` (exemple : `exemple_requete.json`).

## Fichiers utiles pour l'hébergement
| Fichier | Rôle |
|---|---|
| `render.yaml` | Configuration automatique du service Render (build, démarrage, version de Python). |
| `requirements-api.txt` | Bibliothèques de l'API, versions exactes, avec gunicorn. |
| `Procfile`, `.python-version` | Mêmes réglages pour les autres hébergeurs (Railway, Heroku…). |
| `modeles/procedures/` | Modèle + API : doit rester complet. |
| `INTEGRATION.md` | Détail des routes et exemples. |

## Contexte pour Claude (si besoin d'aide)
> Aide-moi à déployer sur Render une API Flask (gunicorn, Python 3.12.3) qui sert un modèle scikit-learn 1.8.0. Commande de démarrage : `gunicorn --chdir modeles/procedures --bind 0.0.0.0:$PORT --workers 1 --timeout 120 api:app`. Routes : /health, /info, /predict, /predict_batch. Le dépôt contient render.yaml, requirements-api.txt et le dossier modeles/procedures/ (api.py, preparation_modele.py, modele_final.joblib, info.json).

Prérequis : les versions de bibliothèques ne doivent pas être changées, sinon `modele_final.joblib` peut ne pas se charger.
