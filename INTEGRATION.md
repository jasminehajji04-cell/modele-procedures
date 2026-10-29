# Intégration du modèle « procedures » dans la plateforme

Auteur : À compléter · Cible : `num_procedures` · Algorithme : gradient boosting · MAE de test : 0.948

Le paquet contient le modèle, son API HTTP et une page Streamlit. Au choix : **A. appeler l'API** (fonctionne avec n'importe quel site) ou **B. intégrer le code Python** (site en Streamlit).

## Contenu
```
modeles/procedures/api.py                    API Flask
modeles/procedures/preparation_modele.py     préparation des données + prédiction
modeles/procedures/modele_final.joblib       modèle et pipeline
modeles/procedures/info.json                 fiche du modèle (nom, cible, métrique, auteur)
pages/1_*.py                              page Streamlit (option B)
test_api.py, exemple_requete.json         test de l'API
requirements.txt                          versions des bibliothèques
render.yaml, requirements-api.txt, Procfile   déploiement en ligne sur Render (voir la section dédiée)
```

## Option A : appeler l'API
1. `pip install -r requirements.txt`
2. Depuis le dossier `modeles/procedures/` : `python api.py` (port 8001, modifiable avec la variable d'environnement `PORT`).
3. Tester : `python test_api.py` (depuis la racine du paquet).

| Route | Méthode | Rôle |
|---|---|---|
| `/health` | GET | vérifier que l'API tourne |
| `/info` | GET | fiche du modèle, liste des champs, valeurs par défaut et modalités possibles (utile pour construire un formulaire) |
| `/predict` | POST | une prédiction ; corps `{"patient": {...}}` |
| `/predict_batch` | POST | plusieurs prédictions ; corps `{"patients": [{...}, ...]}` |

Les champs non envoyés prennent leur valeur la plus courante. Champs utiles : `num_medications`, `time_in_hospital`, `num_lab_procedures`, `number_diagnoses`, `age`, `admission_type_id`, `admission_source_id`, `discharge_disposition_id`, `medical_specialty`, `diag_1` (liste complète dans `/info`, champ `champs`).

Réponse de `/predict` :
```json
{"cible": "num_procedures", "prediction_brute": 3.26, "prediction_arrondie": 3,
 "erreur_typique_mae": 0.948, "avertissement": "Estimation statistique, pas une recommandation clinique."}
```
Erreurs : 400 (corps JSON mal formé), 422 (valeur invalide, message dans `erreur`).

Exemple en ligne de commande :
```
curl -X POST http://127.0.0.1:8001/predict -H "Content-Type: application/json" -d @exemple_requete.json
```
Exemple en JavaScript :
```js
const rep = await fetch("http://127.0.0.1:8001/predict", {
  method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify({patient: {num_medications: 30, time_in_hospital: 10}})
});
const res = await rep.json();   // res.prediction_arrondie, res.erreur_typique_mae
```
L'API autorise les appels depuis un navigateur (CORS ouvert) : suffisant pour une démonstration, à restreindre en production.

## Option B : site en Streamlit
1. Copier le dossier `modeles/procedures/` dans le dossier `modeles/` du site (avec `modeles/__init__.py` s'il n'existe pas).
2. Copier `pages/1_*.py` dans le dossier `pages/` du site et le renommer pour fixer l'ordre du menu. Ne pas appeler `st.set_page_config` dans une page.
3. Fusionner `requirements.txt` avec celui du site.
4. La page d'accueil peut lire `modeles/*/info.json` pour lister les modèles.

## Points d'attention
* **Versions** : le fichier `.joblib` doit être rechargé avec la même version de scikit-learn (voir `requirements.txt`). En cas d'erreur de chargement, contacter l'auteur pour réentraîner le modèle.
* **Un port par modèle** si plusieurs API tournent en même temps.
* **Usage** : estimation statistique à but pédagogique ; le modèle sous-estime les séjours avec beaucoup de procédures. Pas de recommandation clinique.
* **Données** : aucune donnée brute dans ce paquet (seulement un échantillon de référence pour le suivi de dérive).
* **Environnement d'entraînement** : Python 3.12, scikit-learn 1.8.0, pandas 3.0.2, numpy 2.4.4 (voir `requirements.txt`). Utiliser les mêmes versions pour charger `modele_final.joblib`.
* **Auteur** : renseigner son nom dans `modeles/procedures/info.json` (champ `auteur`).

## Déploiement en ligne sur Render (API publique, non locale)

Fichiers ajoutés pour cela : `render.yaml`, `requirements-api.txt` (sans Streamlit, build plus rapide), `Procfile`, `.python-version`. `gunicorn` est ajouté aux dépendances.

**Méthode 1 : Blueprint (la plus simple)**
1. Mettre le contenu du dossier `paquet_procedures/` à la **racine** d'un dépôt GitHub (le fichier `render.yaml` doit être à la racine).
2. Sur https://render.com : **New > Blueprint**, choisir le dépôt, valider. Render lit `render.yaml` et crée le service.
3. Attendre la fin du build (quelques minutes). Render donne une URL du type `https://modele-procedures-api.onrender.com`.

**Méthode 2 : manuelle** (New > Web Service > dépôt GitHub)
* Runtime : Python 3, variable d'environnement `PYTHON_VERSION` = `3.12.3`
* Build Command : `pip install -r requirements-api.txt`
* Start Command : `gunicorn --chdir modeles/procedures --bind 0.0.0.0:$PORT --workers 1 --timeout 120 api:app`
* Health Check Path : `/health`

**Vérifier que c'est en ligne**
* Ouvrir `https://<url>/health` : doit afficher `{"status":"ok"}`.
* Depuis le dossier du paquet : `python test_api.py https://<url>`

**Utiliser l'API depuis le site** : remplacer `http://127.0.0.1:8001` par l'URL Render dans les appels (voir les exemples curl et JavaScript plus haut), par exemple `POST https://<url>/predict`.

**Attention**
* Offre gratuite : le service s'endort après environ 15 min d'inactivité ; la première requête suivante peut prendre 30 à 60 secondes. Pour une démonstration, ouvrir `/health` quelques minutes avant.
* Garder les versions de `requirements-api.txt` (le `.joblib` en dépend) et Python 3.12.
* CORS est ouvert à tous les sites (démonstration uniquement).
