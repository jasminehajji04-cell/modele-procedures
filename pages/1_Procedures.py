import sys
from pathlib import Path

import streamlit as st

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from modeles.procedures import preparation_modele as pm

DOSSIER = RACINE / "modeles" / "procedures"


@st.cache_resource
def charger():
    return pm.charger_modele(DOSSIER / "modele_final.joblib")


b = charger()
d0, mod = b['defaults'], b['modalites']
AGES = ['[0-10)', '[10-20)', '[20-30)', '[30-40)', '[40-50)', '[50-60)', '[60-70)', '[70-80)', '[80-90)', '[90-100)']

st.title("Nombre de procédures attendu pour un séjour")
st.caption("Modèle de gradient boosting · cible : num_procedures")

patient = dict(d0)                      # valeurs par défaut pour tous les champs non affichés
c1, c2 = st.columns(2)
with c1:
    patient['num_medications'] = st.slider("Nombre de médicaments", 1, 81, int(d0['num_medications']))
    patient['time_in_hospital'] = st.slider("Durée du séjour (jours)", 1, 14, int(d0['time_in_hospital']))
    patient['num_lab_procedures'] = st.slider("Nombre de tests de laboratoire", 1, 132, int(d0['num_lab_procedures']))
    patient['number_diagnoses'] = st.slider("Nombre de diagnostics", 1, 16, int(d0['number_diagnoses']))
    patient['age'] = st.selectbox("Tranche d'âge", AGES, index=AGES.index(d0['age']))
with c2:
    for var, libelle in [('admission_type_id', "Type d'admission (code)"),
                         ('admission_source_id', "Source d'admission (code)"),
                         ('discharge_disposition_id', "Destination à la sortie (code)"),
                         ('medical_specialty', "Spécialité médicale")]:
        options = mod[var]
        patient[var] = st.selectbox(libelle, options, index=options.index(d0[var]) if d0[var] in options else 0)
    patient['diag_1'] = st.text_input("Diagnostic primaire (code ICD-9)", str(d0['diag_1']))

if st.button("Prédire", type="primary"):
    res = pm.predire(patient, b).iloc[0]
    st.metric("Valeur attendue (arrondie)", int(res['prediction_arrondie']))
    st.write(f"Valeur brute du modèle : **{res['prediction_brute']:.2f}**")
    st.info(f"Erreur typique du modèle sur le jeu de test : environ ±{b['meta']['mae_test']:.1f} (MAE).")
    st.warning("Ce résultat est un ordre de grandeur statistique, pas une recommandation clinique.")
