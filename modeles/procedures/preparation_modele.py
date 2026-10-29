"""Module de déploiement : prépare les données brutes d'un séjour et prédit num_procedures."""
import joblib
import numpy as np
import pandas as pd
from scipy import stats


def icd9_group(code):
    """Regroupe un code ICD-9 en grande catégorie diagnostique."""
    if code == 'Missing':
        return 'Missing'
    if code.startswith(('V', 'E')):
        return 'Other'
    try:
        v = int(float(code))
    except ValueError:
        return 'Other'
    if v == 250:                                  return 'Diabetes'
    if 390 <= v <= 459 or v == 785:               return 'Circulatory'
    if 460 <= v <= 519 or v == 786:               return 'Respiratory'
    if 520 <= v <= 579 or v == 787:               return 'Digestive'
    if 580 <= v <= 629 or v == 788:               return 'Genitourinary'
    if 710 <= v <= 739:                           return 'Musculoskeletal'
    if 800 <= v <= 999:                           return 'Injury'
    if 140 <= v <= 239:                           return 'Neoplasms'
    return 'Other'


def charger_modele(chemin='modele_final.joblib'):
    """Charge le paquet (modèle + préparation) sauvegardé par le notebook."""
    return joblib.load(chemin)


def preparer_patients(patients, b):
    """Données brutes (dict, liste de dict ou DataFrame) -> variables sélectionnées, prêtes à être encodées."""
    if isinstance(patients, dict):
        d = pd.DataFrame([patients])
    else:
        d = pd.DataFrame(patients).copy()
    manquantes = [c for c in b['colonnes_requises'] if c not in d.columns]
    if manquantes:
        raise ValueError(f"Colonnes manquantes : {manquantes}")

    d = d[b['colonnes_requises']].replace('?', np.nan)          # 3.1.1 valeurs manquantes -> NaN
    for c in b['out_cols'] + b['code_cols']:
        d[c] = pd.to_numeric(d[c])
    d[b['out_cols']] = d[b['out_cols']].clip(                    # 3.1.4 capping P1-P99
        lower=b['bornes'].loc[0.01], upper=b['bornes'].loc[0.99], axis=1)
    d[b['cols_na']] = b['imputer'].transform(d[b['cols_na']])    # 3.1.5 imputation constante

    d['total_prior_visits'] = d[['number_outpatient', 'number_emergency', 'number_inpatient']].sum(axis=1)   # 3.2
    d['n_drugs_used'] = (d[b['drug_cols']] != 'No').sum(axis=1)
    d['n_drugs_changed'] = d[b['drug_cols']].isin(['Up', 'Down']).sum(axis=1)
    d['meds_per_day'] = d['num_medications'] / d['time_in_hospital']
    d['labs_per_day'] = d['num_lab_procedures'] / d['time_in_hospital']
    for k in (1, 2, 3):
        d[f'diag_{k}_group'] = d[f'diag_{k}'].astype(str).map(icd9_group)
    d = d.drop(columns=['diag_1', 'diag_2', 'diag_3'])
    for c in b['code_cols']:
        d[c] = d[c].astype(int).astype(str)
    return d[b['selected_features']]                              # 3.4 sélection


def predire(patients, b):
    """Retourne le nombre de procédures attendu (brut, borné à [0, 6], et arrondi)."""
    X = b['preprocessor'].transform(preparer_patients(patients, b))   # 3.5 encodage + échelle
    brut = np.clip(b['modele'].predict(X), 0, 6)
    return pd.DataFrame({'prediction_brute': brut.round(3), 'prediction_arrondie': np.rint(brut).astype(int)})


# ---------------- Suivi du modèle en production ----------------
def controle_performance(y_vrai, y_pred, mae_reference, facteur=1.2):
    """Alerte si le MAE observé dépasse facteur x MAE de référence (celui mesuré sur le jeu de test)."""
    mae = float(np.mean(np.abs(np.asarray(y_vrai) - np.asarray(y_pred))))
    seuil = facteur * mae_reference
    return {'MAE observé': round(mae, 3), 'seuil d\'alerte': round(seuil, 3), 'alerte': mae > seuil}


def controle_derive(nouveaux, reference, colonnes, seuil_ks=0.1):
    """Compare la distribution de chaque variable aux données d'entraînement (test de Kolmogorov-Smirnov)."""
    lignes = []
    for c in colonnes:
        ks = stats.ks_2samp(reference[c], nouveaux[c])
        lignes.append({'variable': c, 'statistique KS': round(ks.statistic, 3), 'p-value': ks.pvalue,
                       'moyenne référence': round(reference[c].mean(), 2), 'moyenne nouvelles': round(nouveaux[c].mean(), 2),
                       'alerte': ks.statistic > seuil_ks})
    return pd.DataFrame(lignes).set_index('variable')
