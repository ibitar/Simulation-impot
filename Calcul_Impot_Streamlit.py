import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass
from datetime import datetime

# --- Pied de page / Informations version ---
st.set_page_config(page_title="Simulations financières 2025", layout="centered")

st.sidebar.markdown("---")
st.sidebar.caption("🛠️ Développé par **I. Bitar**")
st.sidebar.caption("📅 Dernière mise à jour : **9 mai 2025**")
st.sidebar.caption("🔢 Version : **v1.0.0**")

st.markdown("---")
st.caption("🛠️ Développé par **I. Bitar** · 📅 Dernière mise à jour : **9 mai 2025** · 🔢 Version : **v1.0.0**")

# ---------- PARAMÈTRES 2025 (Brut → Net cadre) ----------
PMSS = 3925.0           # Plafond Mensuel Sécurité sociale (PASS mensuel) 2025
PASS_ANNUEL = 47100.0   # PASS annuel 2025
AA_T2_MAX = 8 * PMSS    # Limite supérieure Agirc-Arrco Tranche 2 (8 PMSS)
APEC_PLAFOND = 4 * PMSS # Assiette max APEC (4 PMSS)

# Régime général - part SALARIÉE
TAUX_VIEIL_PLAF_SAL = 0.069   # 6,90% sur T1
TAUX_VIEIL_DEPLAF_SAL = 0.004 # 0,40% sur totalité
TAUX_MALADIE_SAL_AM = 0.013   # Maladie salariée Alsace-Moselle

# AGIRC-ARRCO (taux d'appel) - part SALARIÉE
TAUX_AA_T1_SAL  = 0.0315  # 3,15%
TAUX_AA_T2_SAL  = 0.0864  # 8,64%
TAUX_CEG_T1_SAL = 0.0086  # 0,86%
TAUX_CEG_T2_SAL = 0.0108  # 1,08%
TAUX_CET_SAL    = 0.0014  # 0,14% si brut > PMSS, assiette T1+T2
TAUX_APEC_SAL   = 0.00024 # 0,024% sur 0→4 PMSS (cadres)

# CSG/CRDS (assiette = 98,25% du brut)
ASSIETTE_CSG_ABATT = 0.9825
TAUX_CSG_DED   = 0.068  # 6,8% déductible
TAUX_CSG_NDED  = 0.024  # 2,4% non déductible
TAUX_CRDS      = 0.005  # 0,5%

# --------- PART EMPLOYEUR (paramétrable) ----------
TAUX_VIEIL_PLAF_EMP   = 0.0855  # 8,55% sur T1
TAUX_VIEIL_DEPLAF_EMP = 0.0202  # 2,02% sur totalité

# AGIRC-ARRCO (taux d'appel) - part EMPLOYEUR
TAUX_AA_T1_EMP  = 0.0472  # 4,72%
TAUX_AA_T2_EMP  = 0.1295  # 12,95%
TAUX_CEG_T1_EMP = 0.0129  # 1,29%
TAUX_CEG_T2_EMP = 0.0162  # 1,62%
TAUX_CET_EMP    = 0.0021  # 0,21%
TAUX_APEC_EMP   = 0.00036 # 0,036% (0→4 PMSS, cadres)

# Autres contributions employeur variables selon cas
TAUX_MALADIE_EMP_INF_2P5 = 0.07   # 7,0% si rémunération ≤ 2,5 SMIC
TAUX_MALADIE_EMP_SUP_2P5 = 0.13   # 13,0% si rémunération > 2,5 SMIC
TAUX_AF_EMP_INF_3P5      = 0.0345 # 3,45% si rémunération ≤ 3,5 SMIC
TAUX_AF_EMP_SUP_3P5      = 0.0525 # 5,25% si rémunération > 3,5 SMIC
TAUX_CHOMAGE_EMP_2025_MAI = 0.04  # 4,00% à compter du 01/05/2025 (hors modulation)
TAUX_CHOMAGE_EMP_AVANT_MAI = 0.0405
TAUX_AGS_EMP = 0.0025             # 0,25% en 2025
TAUX_FNAL_MOINS_50 = 0.001        # 0,10%
TAUX_FNAL_50_PLUS  = 0.005        # 0,50%
TAUX_CSA_EMP = 0.003              # Contribution solidarité autonomie 0,30%


@dataclass
class ResultatSalaire:
    brut_mensuel: float
    base_T1: float
    base_T2: float
    vieillesse_plafonnee: float
    vieillesse_deplafonnee: float
    maladie_salarie: float
    agirc_arrco_T1: float
    agirc_arrco_T2: float
    ceg_T1: float
    ceg_T2: float
    cet: float
    apec: float
    csg_deductible: float
    csg_non_deductible: float
    crds: float
    total_cot_sal_hors_csg: float
    total_csg_crds: float
    net_imposable: float
    net_a_payer: float
    maladie_employeur: float
    vieillesse_plaf_emp: float
    vieillesse_deplaf_emp: float
    aa_T1_emp: float
    aa_T2_emp: float
    ceg_T1_emp: float
    ceg_T2_emp: float
    cet_emp: float
    apec_emp: float
    allocations_familiales: float
    chomage: float
    ags: float
    fnal: float
    csa: float
    total_charges_employeur: float
    cout_total_employeur: float


def calcul_brut_net_mensuel(
    brut_mensuel: float,
    *,
    cadre: bool = True,
    alsace_moselle: bool = False,
    sup_2p5_smic: bool = True,
    sup_3p5_smic: bool = True,
    effectif_50plus: bool = True,
    chomage_apres_mai_2025: bool = True,
) -> ResultatSalaire:
    """Calcule les cotisations et nets mensuels pour un cadre."""

    base_T1 = min(brut_mensuel, PMSS)
    base_T2 = max(0.0, min(brut_mensuel, AA_T2_MAX) - PMSS)

    # Cotisations salariales
    vieill_plaf = TAUX_VIEIL_PLAF_SAL * base_T1
    vieill_depl = TAUX_VIEIL_DEPLAF_SAL * brut_mensuel
    maladie_sal = (TAUX_MALADIE_SAL_AM * brut_mensuel) if alsace_moselle else 0.0

    aa_T1_sal = TAUX_AA_T1_SAL * base_T1
    aa_T2_sal = TAUX_AA_T2_SAL * base_T2
    ceg_T1_sal = TAUX_CEG_T1_SAL * base_T1
    ceg_T2_sal = TAUX_CEG_T2_SAL * base_T2
    cet_sal = (TAUX_CET_SAL * (base_T1 + base_T2)) if brut_mensuel > PMSS else 0.0

    apec_base = min(brut_mensuel, APEC_PLAFOND) if cadre else 0.0
    apec_sal = TAUX_APEC_SAL * apec_base if cadre else 0.0

    assiette_csg = ASSIETTE_CSG_ABATT * brut_mensuel
    csg_ded = TAUX_CSG_DED * assiette_csg
    csg_nded = TAUX_CSG_NDED * assiette_csg
    crds = TAUX_CRDS * assiette_csg

    total_sal_hors_csg = (
        vieill_plaf
        + vieill_depl
        + maladie_sal
        + aa_T1_sal
        + aa_T2_sal
        + ceg_T1_sal
        + ceg_T2_sal
        + cet_sal
        + apec_sal
    )
    total_csg_crds = csg_ded + csg_nded + crds

    net_imposable = brut_mensuel - total_sal_hors_csg - csg_ded
    net_a_payer = brut_mensuel - total_sal_hors_csg - total_csg_crds

    # Cotisations employeur
    maladie_emp = (
        TAUX_MALADIE_EMP_SUP_2P5 if sup_2p5_smic else TAUX_MALADIE_EMP_INF_2P5
    ) * brut_mensuel
    vieill_plaf_emp = TAUX_VIEIL_PLAF_EMP * base_T1
    vieill_deplaf_emp = TAUX_VIEIL_DEPLAF_EMP * brut_mensuel
    aa_T1_emp = TAUX_AA_T1_EMP * base_T1
    aa_T2_emp = TAUX_AA_T2_EMP * base_T2
    ceg_T1_emp = TAUX_CEG_T1_EMP * base_T1
    ceg_T2_emp = TAUX_CEG_T2_EMP * base_T2
    cet_emp = (TAUX_CET_EMP * (base_T1 + base_T2)) if brut_mensuel > PMSS else 0.0
    apec_emp = (TAUX_APEC_EMP * apec_base) if cadre else 0.0
    af_emp = (
        TAUX_AF_EMP_SUP_3P5 if sup_3p5_smic else TAUX_AF_EMP_INF_3P5
    ) * brut_mensuel
    taux_chom = (
        TAUX_CHOMAGE_EMP_2025_MAI
        if chomage_apres_mai_2025
        else TAUX_CHOMAGE_EMP_AVANT_MAI
    )
    chomage_emp = taux_chom * brut_mensuel
    ags_emp = TAUX_AGS_EMP * brut_mensuel
    fnal_emp = (
        TAUX_FNAL_50_PLUS if effectif_50plus else TAUX_FNAL_MOINS_50
    ) * brut_mensuel
    csa_emp = TAUX_CSA_EMP * brut_mensuel

    total_emp = (
        maladie_emp
        + vieill_plaf_emp
        + vieill_deplaf_emp
        + aa_T1_emp
        + aa_T2_emp
        + ceg_T1_emp
        + ceg_T2_emp
        + cet_emp
        + apec_emp
        + af_emp
        + chomage_emp
        + ags_emp
        + fnal_emp
        + csa_emp
    )
    cout_total = brut_mensuel + total_emp

    return ResultatSalaire(
        brut_mensuel=brut_mensuel,
        base_T1=base_T1,
        base_T2=base_T2,
        vieillesse_plafonnee=vieill_plaf,
        vieillesse_deplafonnee=vieill_depl,
        maladie_salarie=maladie_sal,
        agirc_arrco_T1=aa_T1_sal,
        agirc_arrco_T2=aa_T2_sal,
        ceg_T1=ceg_T1_sal,
        ceg_T2=ceg_T2_sal,
        cet=cet_sal,
        apec=apec_sal,
        csg_deductible=csg_ded,
        csg_non_deductible=csg_nded,
        crds=crds,
        total_cot_sal_hors_csg=total_sal_hors_csg,
        total_csg_crds=total_csg_crds,
        net_imposable=net_imposable,
        net_a_payer=net_a_payer,
        maladie_employeur=maladie_emp,
        vieillesse_plaf_emp=vieill_plaf_emp,
        vieillesse_deplaf_emp=vieill_deplaf_emp,
        aa_T1_emp=aa_T1_emp,
        aa_T2_emp=aa_T2_emp,
        ceg_T1_emp=ceg_T1_emp,
        ceg_T2_emp=ceg_T2_emp,
        cet_emp=cet_emp,
        apec_emp=apec_emp,
        allocations_familiales=af_emp,
        chomage=chomage_emp,
        ags=ags_emp,
        fnal=fnal_emp,
        csa=csa_emp,
        total_charges_employeur=total_emp,
        cout_total_employeur=cout_total,
    )


def page_brut_net():
    """Interface Streamlit pour le calcul brut → net cadre 2025."""

    st.title("Brut → Net (cadre, 2025) + part employeur")
    st.caption(
        "Les montants affichés sont mensuels. Utilisez l'option *Annuel* pour convertir"
        " automatiquement un salaire annuel brut."
    )

    colA, colB = st.columns(2)
    with colA:
        period = st.selectbox("Période", ["Mensuel", "Annuel"], index=0)
    with colB:
        brut_input = st.number_input(
            f"Salaire brut {period.lower()}",
            min_value=0.0,
            value=6000.0,
            step=100.0,
        )

    st.subheader("Options")
    c1, c2, c3 = st.columns(3)
    with c1:
        alsace_moselle = st.checkbox(
            "Alsace-Moselle (1,30% sal. maladie)", value=False
        )
        cadre = st.checkbox("Cadre (APEC/AGIRC-ARRCO)", value=True)
    with c2:
        sup_2p5 = st.checkbox(
            "Rémunération > 2,5 SMIC (maladie employeur 13%)", value=True
        )
        sup_3p5 = st.checkbox(
            "Rémunération > 3,5 SMIC (AF 5,25%)", value=True
        )
    with c3:
        effectif_50plus = st.checkbox("Effectif ≥ 50 (FNAL 0,50%)", value=True)
        chomage_mai = st.checkbox(
            "Taux chômage 4,00% (après 01/05/2025)", value=True
        )

    brut_mensuel = brut_input / 12.0 if period == "Annuel" else brut_input

    res = calcul_brut_net_mensuel(
        brut_mensuel,
        cadre=cadre,
        alsace_moselle=alsace_moselle,
        sup_2p5_smic=sup_2p5,
        sup_3p5_smic=sup_3p5,
        effectif_50plus=effectif_50plus,
        chomage_apres_mai_2025=chomage_mai,
    )

    st.markdown("### Résumé")
    resume = {
        "Brut mensuel": round(res.brut_mensuel, 2),
        "Net imposable": round(res.net_imposable, 2),
        "Net à payer": round(res.net_a_payer, 2),
        "Total cotisations salarié (hors CSG/CRDS)": round(
            res.total_cot_sal_hors_csg, 2
        ),
        "CSG déductible": round(res.csg_deductible, 2),
        "CSG non déductible": round(res.csg_non_deductible, 2),
        "CRDS": round(res.crds, 2),
        "Total charges employeur": round(res.total_charges_employeur, 2),
        "Coût total employeur": round(res.cout_total_employeur, 2),
    }
    resume_df = pd.DataFrame(resume, index=["Montant"]).T
    st.dataframe(resume_df)

    st.markdown("### Détail salarié")
    sal_df = pd.DataFrame(
        {
            "Poste": [
                "Vieillesse plafonnée (6,90% T1)",
                "Vieillesse déplafonnée (0,40%)",
                "Maladie Alsace-Moselle (1,30%)",
                "AGIRC-ARRCO T1 (3,15%)",
                "AGIRC-ARRCO T2 (8,64%)",
                "CEG T1 (0,86%)",
                "CEG T2 (1,08%)",
                "CET (0,14%)",
                "APEC (0,024% sur 0→4 PMSS)",
                "CSG déductible (6,8% sur 98,25%)",
                "CSG non déductible (2,4% sur 98,25%)",
                "CRDS (0,5% sur 98,25%)",
            ],
            "Montant €": [
                res.vieillesse_plafonnee,
                res.vieillesse_deplafonnee,
                res.maladie_salarie,
                res.agirc_arrco_T1,
                res.agirc_arrco_T2,
                res.ceg_T1,
                res.ceg_T2,
                res.cet,
                res.apec,
                res.csg_deductible,
                res.csg_non_deductible,
                res.crds,
            ],
        }
    )
    st.dataframe(sal_df.style.format({"Montant €": "{:,.2f}"}))

    st.markdown("### Détail employeur")
    emp_df = pd.DataFrame(
        {
            "Poste": [
                "Maladie (7% ou 13%)",
                "Vieillesse plafonnée (8,55% T1)",
                "Vieillesse déplafonnée (2,02%)",
                "AGIRC-ARRCO T1 (4,72%)",
                "AGIRC-ARRCO T2 (12,95%)",
                "CEG T1 (1,29%)",
                "CEG T2 (1,62%)",
                "CET (0,21%)",
                "APEC (0,036% sur 0→4 PMSS)",
                "Allocations familiales (3,45% ou 5,25%)",
                "Assurance chômage (4,00% ou 4,05%)",
                "AGS (0,25%)",
                "FNAL (0,10% ou 0,50%)",
                "CSA (0,30%)",
            ],
            "Montant €": [
                res.maladie_employeur,
                res.vieillesse_plaf_emp,
                res.vieillesse_deplaf_emp,
                res.aa_T1_emp,
                res.aa_T2_emp,
                res.ceg_T1_emp,
                res.ceg_T2_emp,
                res.cet_emp,
                res.apec_emp,
                res.allocations_familiales,
                res.chomage,
                res.ags,
                res.fnal,
                res.csa,
            ],
        }
    )
    st.dataframe(emp_df.style.format({"Montant €": "{:,.2f}"}))

    st.markdown("### Export")
    export_dict = {
        **resume,
        **{f"Salarié | {k}": v for k, v in zip(sal_df["Poste"], sal_df["Montant €"])},
        **{f"Employeur | {k}": v for k, v in zip(emp_df["Poste"], emp_df["Montant €"])},
        "Base T1": res.base_T1,
        "Base T2": res.base_T2,
    }
    csv_bytes = pd.Series(export_dict).to_csv(header=False).encode("utf-8")
    st.download_button(
        "Télécharger le breakdown en CSV",
        data=csv_bytes,
        file_name="breakdown_brut_net_2025.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("**Notes importantes**")
    st.markdown(
        """
- Ce simulateur couvre un **cadre** du secteur privé. Les cas particuliers (mutuelle,
  prévoyance, exonérations, accords d'entreprise…) ne sont pas intégrés.
- Les contributions **employeur** (maladie, AF, FNAL, chômage) dépendent de vos
  options (seuils en SMIC, effectif, date d'application). Ajustez les bascules pour
  refléter la situation réelle.
- L’assurance chômage est à la charge **exclusivement employeur** et passe à **4,00 %**
  au **1er mai 2025** (hors bonus-malus).
- L’AGIRC-ARRCO est limitée à **8 PMSS** (tranche 2), l’APEC à **4 PMSS**.
- La CSG/CRDS est calculée sur **98,25 %** du brut (6,8 % déductible, 2,4 % non
  déductible, 0,5 % CRDS).
"""
    )

    st.markdown("**Sources 2025**")
    st.caption(
        "PASS/PMSS 2025, taux AGIRC-ARRCO (T1/T2, CEG, CET, APEC), URSSAF (vieillesse,"
        " CSG/CRDS), taux maladie employeur, allocations familiales, FNAL, chômage"
        " (mai 2025), AGS et CSA."
    )

# --- Initialisation du state pour stocker le résultat de la simulation ---
if "simulation" not in st.session_state:
    st.session_state["simulation"] = None

# --- Fonction de calcul d'impôt (inchangée) ---
# Fonction de calcul d'impôt
def calcul_impot(revenu_salarial, chiffre_affaire_autoentrepreneur,
                 nombre_parts, reduction_forfaitaire=False,
                 aide_familiale=0, frais_garde=0, est_couple=False):
    if reduction_forfaitaire:
        revenu_salarial_apres_reduction = revenu_salarial * 0.90
        reduction_salariale = revenu_salarial - revenu_salarial_apres_reduction
    else:
        revenu_salarial_apres_reduction = revenu_salarial
        reduction_salariale = 0

    revenu_autoentrepreneur = chiffre_affaire_autoentrepreneur * 0.66
    reduction_autoentrepreneur = chiffre_affaire_autoentrepreneur * 0.34

    revenu_imposable = revenu_salarial_apres_reduction + revenu_autoentrepreneur
    revenu_imposable_apres_aide = revenu_imposable - aide_familiale
    quotient_familial = revenu_imposable_apres_aide / nombre_parts

    tranches = [
        (0, 11497, 0.00),
        (11497, 29315, 0.11),
        (29315, 83823, 0.30),
        (83823, 180294, 0.41),
        (180294, float('inf'), 0.45)
    ]

    impot_quotient = 0
    details_tranches = []
    for tranche in tranches:
        if quotient_familial > tranche[1]:
            impot_tranche = (tranche[1] - tranche[0]) * tranche[2]
            impot_quotient += impot_tranche
            details_tranches.append(f"Tranche {tranche[0]}€ à {tranche[1]}€ : {impot_tranche:.2f} €")
        else:
            impot_tranche = (quotient_familial - tranche[0]) * tranche[2]
            impot_quotient += impot_tranche
            details_tranches.append(f"Tranche {tranche[0]}€ à {quotient_familial:.2f}€ : {impot_tranche:.2f} €")
            break

    impot_total = impot_quotient * nombre_parts

    if est_couple:
        decote = max(0, 1470 - 0.4525 * impot_total)
    else:
        decote = max(0, 889 - 0.4525 * impot_total)

    impot_apres_decote = max(0, impot_total - decote)
    reduction_frais_garde = frais_garde * 0.50
    impot_final = max(0, impot_apres_decote - reduction_frais_garde)

    revenu_net_annuel = revenu_imposable_apres_aide - impot_final
    revenu_net_mensuel = revenu_net_annuel / 12

    return {
        "impot_final": impot_final,
        "revenu_net_mensuel": revenu_net_mensuel,
        "nombre_parts": nombre_parts,
        "details": {
            "Revenu salarial initial": revenu_salarial,
            "Réduction salariale forfaitaire (10%)": reduction_salariale,
            "Revenu (chiffre d'affaire) auto-entrepreneur ": chiffre_affaire_autoentrepreneur,
            "Réduction auto-entrepreneur (34%)": reduction_autoentrepreneur,
            "Revenu imposable annuel total": revenu_imposable,
            "Déduction pour aides et dons": aide_familiale,
            "Revenu imposable annuel après aides": revenu_imposable_apres_aide,
            "Impôt brut avant décote": impot_total,
            "Décote": decote,
            "Impôt après décote": impot_apres_decote,
            "Réduction frais de garde (50%)": reduction_frais_garde,
        },
        "details_tranches": details_tranches
    }

def generate_html_report(result_dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rapport Simulation Impôt</title>
</head>
<body>
    <h1>Rapport de Simulation d'Impôt</h1>
    <p><strong>Date de génération :</strong> {now}</p>
    <hr>
    <h2>Résumé</h2>
    <p><strong>Impôt Final (€):</strong> {result_dict['impot_final']:.2f}</p>
    <p><strong>Revenu Net Mensuel (€):</strong> {result_dict['revenu_net_mensuel']:.2f}</p>
    <h2>Détails</h2>
    <ul>
    """
    for k, v in result_dict["details"].items():
        html += f"<li><strong>{k}:</strong> {v:.2f} €</li>"
    html += """
    </ul>
    <h2>Détails des Tranches</h2>
    <ul>
    """
    for t in result_dict["details_tranches"]:
        html += f"<li>{t}</li>"
    html += """
    </ul>
</body>
</html>
"""
    return html.encode("utf-8")


# --- Fonction pour la page Simulation ---
def simulation_page():
    st.title("Simulation d'Impôt")

    # Inputs
    revenu_salarial = st.number_input("Revenu Salarial Annuel Net Imposable (€)", 0.0, step=1000.0, key="rev")
    ca_auto = st.number_input("Chiffre d'Affaires Auto-Entrepreneur Annuel (€)", 0.0, step=1000.0, key="ca")
    parts = st.number_input("Nombre de Parts", 1.0, step=0.5, key="parts")
    aide = st.number_input("Aide Familiale (€)", 0.0, step=100.0, key="aide")
    garde = st.number_input("Frais de Garde (€)", 0.0, step=100.0, key="garde")
    red = st.checkbox("Réduction Forfaitaire 10% sur Salaire", key="red")
    couple = st.checkbox("Couple (Marié/Pacsé)", key="couple")

    if st.button("Calculer"):
        st.session_state["simulation"] = calcul_impot(
            revenu_salarial, ca_auto, parts, red, aide, garde, couple
        )
        st.success("✅ Simulation enregistrée !")

    result = st.session_state.get("simulation")
    if result:
        with st.expander("Résumé", expanded=True):
            st.metric("Impôt Final (€)", f"{result['impot_final']:.2f}")
            st.metric("Revenu Net Mensuel (€)", f"{result['revenu_net_mensuel']:.2f}")

        with st.expander("Détails", expanded=True):
            for k, v in result["details"].items():
                st.write(f"**{k} :** {v:.2f} €")

        with st.expander("Tranches", expanded=True):
            for t in result["details_tranches"]:
                st.write(t)

        # Graphique circulaire
        with st.expander("Visualisation de la répartition", expanded=True):
            revenu_net = result["details"]["Revenu imposable annuel après aides"]
            impot_total = result["details"]["Impôt après décote"]

            fig, ax = plt.subplots()
            labels = ['Impôt payé', 'Revenu net après impôt']
            values = [impot_total, revenu_net - impot_total]
            colors = ['#ff6b6b', '#4ecdc4']
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
            ax.axis('equal')
            ax.set_title("Répartition de l'impôt sur le revenu net annuel")
            st.pyplot(fig)
            
        with st.expander("📄 Télécharger le rapport HTML", expanded=False):
            html_data = generate_html_report(result)
            st.download_button(
                label="📥 Télécharger le rapport",
                data=html_data,
                file_name=f"rapport_impot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )

# --- Fonction pour la page d’Information ---
def page_information():
    st.title("📊 Visualisation des taux 2025 selon votre situation simulée")

    sim = st.session_state.get("simulation")
    if not sim:
        st.warning("Aucune simulation enregistrée. Veuillez d'abord remplir la page de simulation.")
        return

    # --- Récupération des données de la simulation ---
    revenu_imposable_apres_aide = sim["details"]["Revenu imposable annuel après aides"]
    nombre_parts = sim["nombre_parts"]
    quotient_familial = revenu_imposable_apres_aide / nombre_parts
    quotient_mensuel = quotient_familial / 12

    # --- Barème d'imposition ---
    bareme = [
        (0, 11294, 0.00),
        (11294, 28797, 0.11),
        (28797, 82341, 0.30),
        (82341, 177106, 0.41),
        (177106, float('inf'), 0.45)
    ]

    # --- Fonctions de calcul ---
    def calc_imp(r):
        i, d = 0, []
        for bas, haut, tx in bareme:
            if r > bas:
                tr = min(haut, r) - bas
                m = tr * tx
                i += m
                d.append((bas, min(haut, r), tr, tx, m))
            else:
                break
        return i, d

    def tx_marg(r):
        for bas, _, tx in reversed(bareme):
            if r > bas:
                return tx
        return 0.0

    # --- Données pour les courbes ---
    revenus_bruts_m = np.linspace(1000, 15000, 500)
    revenus_bruts_a = revenus_bruts_m * 12
    revenus_nets_a = revenus_bruts_a * 0.77
    revenus_nets_m = revenus_nets_a / 12

    impots_a = np.array([calc_imp(r)[0] for r in revenus_nets_a])
    taux_eff = impots_a / revenus_nets_a
    taux_marg_arr = np.array([tx_marg(r) for r in revenus_nets_a])
    taux_nom = impots_a / revenus_bruts_a

    # --- Données ciblées à partir de la simulation ---
    impot_cible, details = calc_imp(quotient_familial)
    rba = quotient_familial / 0.77
    te_c = (impot_cible / quotient_familial) * 100
    tm_c = tx_marg(quotient_familial) * 100
    tn_c = (impot_cible / rba) * 100

    # --- Tracé des courbes ---
    fig, ax = plt.subplots(figsize=(10, 6))
    couleurs = ['#e0f7fa','#b2ebf2','#80deea','#4dd0e1','#26c6da']
    for (b, h, _), c in zip(bareme, couleurs):
        ax.axvspan(b / 12, h / 12, facecolor=c, alpha=0.3)

    ax.plot(revenus_nets_m, taux_eff * 100, label="Taux effectif", linewidth=2)
    ax.plot(revenus_nets_m, taux_marg_arr * 100, '--', label="Taux marginal")
    ax.plot(revenus_nets_m, taux_nom * 100, ':', label="Taux nominal")

    ax.axvline(x=quotient_mensuel, color='red', linestyle='--')
    ax.plot(quotient_mensuel, te_c, 'ro', label=f"Votre position ({quotient_mensuel:.0f} €)")

    ax.annotate(f"{te_c:.1f}%", 
                xy=(quotient_mensuel, te_c),
                xytext=(quotient_mensuel + 200, te_c + 2),
                arrowprops=dict(arrowstyle="->", color='red'),
                fontsize=10, color='red')

    ax.set_xlabel("Quotient familial mensuel (€)")
    ax.set_ylabel("Taux (%)")
    ax.set_title("Taux d'imposition 2025 selon votre quotient familial")
    ax.grid(True)
    ax.legend(loc="lower right")
    st.pyplot(fig)

    # --- Analyse texte ---
    st.markdown("---")
    st.subheader("🧮 Analyse de votre situation")
    st.markdown(f"""
- **Revenu imposable après aides** : {revenu_imposable_apres_aide:.0f} €
- **Nombre de parts** : {nombre_parts:.2f}
- **Quotient familial annuel** : {quotient_familial:.0f} €
- **Quotient familial mensuel** : {quotient_mensuel:.0f} €
- **Revenu brut estimé équivalent** : {rba:.0f} €
- **Impôt annuel (sur 1 part)** : {impot_cible:.0f} €
- **Taux effectif** : {te_c:.1f} %
- **Taux marginal** : {tm_c:.1f} %
- **Taux nominal** : {tn_c:.1f} %
""")

    with st.expander("📊 Détail par tranche appliquée à votre quotient familial"):
        for bas, haut, tr, tx, mnt in details:
            st.markdown(f"- De {bas:.0f} € à {haut:.0f} € : {tr:.0f} € × {int(tx*100)}% = {mnt:.0f} €")

def page_credit():
    st.title("🏠 Simulation Capacité d'Emprunt")

    # Récupération des données de la simulation
    sim = st.session_state.get("simulation")
    if sim:
        revenu_net_simulation = sim["revenu_net_mensuel"]
        st.success(
            f"✅ Salaire net mensuel récupéré depuis la simulation : "
            f"**{revenu_net_simulation:,.2f} €**"
        )
    else:
        st.info("Aucune simulation trouvée. Veuillez saisir votre salaire manuellement.")
        revenu_net_simulation = st.number_input(
            "Salaire net mensuel (€)",
            min_value=0.0,
            step=100.0
        )

    # Charges existantes
    st.header("Vos charges existantes")
    has_existing_loan = st.checkbox("Avez-vous déjà un prêt immobilier en cours ?")

    mensualite_existante = 0.0
    revenus_locatifs_net = 0.0
    txt_info_location = ""

    if has_existing_loan:
        mensualite_existante = st.number_input(
            "Montant mensuel du prêt existant (€)",
            min_value=0.0,
            step=50.0
        )

        # Option location du bien existant
        is_rented = st.checkbox("Ce bien est-il mis en location ?")

        if is_rented:
            loyer_brut = st.number_input(
                "Loyer mensuel brut perçu (€)",
                min_value=0.0,
                step=50.0
            )
            taux_integration = st.slider(
                "Taux d'intégration des loyers (%)",
                min_value=50,
                max_value=100,
                value=70,
                step=5,
                help="Les banques prennent souvent 70% à 80% du loyer pour le calcul de la capacité d'emprunt."
            )
            revenus_locatifs_net = loyer_brut * (taux_integration / 100)
            txt_info_location = (
                f"✅ Revenus locatifs intégrés à hauteur de {taux_integration}% : "
                f"**{revenus_locatifs_net:.2f} €**"
            )
            st.success(txt_info_location)

    # Revenu net total pris en compte
    revenu_total = revenu_net_simulation + revenus_locatifs_net

    st.header("Projet d'emprunt")
    taux_emprunt = st.number_input(
        "Taux d'intérêt nominal (%)",
        min_value=0.1, max_value=10.0,
        value=4.0, step=0.1
    )
    duree_annees = st.number_input(
        "Durée de l'emprunt (années)",
        min_value=5, max_value=30,
        value=20, step=1
    )

    if revenu_total > 0:
        taux_endettement_max = 0.35
        capacite_mensuelle = revenu_total * taux_endettement_max - mensualite_existante
        capacite_mensuelle = max(capacite_mensuelle, 0)

        nb_mois = duree_annees * 12
        taux_mensuel = taux_emprunt / 100 / 12

        if taux_mensuel > 0:
            capital_max = capacite_mensuelle * (1 - (1 + taux_mensuel) ** -nb_mois) / taux_mensuel
        else:
            capital_max = capacite_mensuelle * nb_mois

        st.subheader("💰 Résultats")
        st.metric("Capacité d'emprunt mensuelle (€)", f"{capacite_mensuelle:.2f}")
        st.metric("Montant du prêt maximal (€)", f"{capital_max:.2f}")

        # Récapitulatif clair de toutes les hypothèses
        st.markdown("### 🔎 Hypothèses prises en compte :")
        st.markdown(f"- **Revenu net mensuel (simulation)** : {revenu_net_simulation:.2f} €")
        if revenus_locatifs_net > 0:
            st.markdown(f"- **Revenus locatifs pris en compte** : {revenus_locatifs_net:.2f} €")
        st.markdown(f"- **Revenu total pris en compte** : {revenu_total:.2f} €")
        st.markdown(f"- **Mensualité existante** : {mensualite_existante:.2f} €")
        st.markdown(f"- **Taux d'endettement max** : 35 %")
        st.markdown(f"- **Taux nominal du prêt** : {taux_emprunt:.2f} %")
        st.markdown(f"- **Durée du prêt** : {duree_annees} ans")

        st.info(
            f"Pour un taux de **{taux_emprunt:.2f} %** sur **{duree_annees} ans**, "
            f"votre capacité d'emprunt est estimée à environ **{capital_max:,.0f} €** "
            f"avec une mensualité de **{capacite_mensuelle:,.0f} €**."
        )
    else:
        st.warning("Veuillez saisir vos revenus ou effectuer d'abord la simulation.")


# --- Barre latérale de navigation simplifiée ---
st.sidebar.title("Menu")
page = st.sidebar.radio(
    "",
    [
        "Simulation",
        "Page d'information",
        "Capacité d'emprunt",
        "Brut → Net cadre",
    ],
)

if page == "Simulation":
    simulation_page()
elif page == "Page d'information":
    page_information()
elif page == "Capacité d'emprunt":
    page_credit()
elif page == "Brut → Net cadre":
    page_brut_net()

