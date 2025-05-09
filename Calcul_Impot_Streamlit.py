import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Pied de page / Informations version ---
st.sidebar.markdown("---")
st.sidebar.caption("🛠️ Développé par **I. Bitar**")
st.sidebar.caption("📅 Dernière mise à jour : **9 mai 2025**")
st.sidebar.caption("🔢 Version : **v1.0.0**")

st.markdown("---")
st.caption("🛠️ Développé par **I. Bitar** · 📅 Dernière mise à jour : **9 mai 2025** · 🔢 Version : **v1.0.0**")

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

    # Affichage du résultat
    result = st.session_state["simulation"]
    if result:
        with st.expander("Résumé"):
            st.metric("Impôt Final (€)", f"{result['impot_final']:.2f}")
            st.metric("Revenu Net Mensuel (€)", f"{result['revenu_net_mensuel']:.2f}")
        with st.expander("Détails"):
            for k, v in result["details"].items():
                st.write(f"**{k} :** {v:.2f} €")
        with st.expander("Tranches"):
            for t in result["details_tranches"]:
                st.write(t)

# --- Fonction pour la page d’Information ---
def page_information():
    st.title("📊 Visualisation des taux 2025")

    # On récupère la valeur par défaut de la simulation si elle existe
    default = 3000
    sim = st.session_state.get("simulation")
    if sim:
        default = sim["revenu_net_mensuel"]

    salaire = st.slider(
        "Salaire net mensuel avant impôt (€)", 
        1000, 15000, 
        value=int(default), 
        step=100, 
        help="Par défaut, votre dernier résultat de simulation"
    )

    # --- Calculs et tracés (identiques à ton code) ---
    revenus_bruts_m = np.linspace(1000, 15000, 500)
    revenus_bruts_a = revenus_bruts_m * 12
    revenus_nets_a = revenus_bruts_a * 0.77
    revenus_nets_m = revenus_nets_a / 12

    bareme = [
        (0, 11294, 0.00),
        (11294, 28797, 0.11),
        (28797, 82341, 0.30),
        (82341, 177106, 0.41),
        (177106, float('inf'), 0.45)
    ]
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
            if r > bas: return tx
        return 0.0

    impots_a = np.array([calc_imp(r)[0] for r in revenus_nets_a])
    taux_eff = impots_a / revenus_nets_a
    taux_marg_arr = np.array([tx_marg(r) for r in revenus_nets_a])
    taux_nom = impots_a / revenus_bruts_a

    # Valeurs ciblées
    rna = salaire * 12
    rba = rna / 0.77
    _, details = calc_imp(rna)
    ie = impots_a
    te_c = (calc_imp(rna)[0] / rna) * 100
    tm_c = tx_marg(rna) * 100
    tn_c = (calc_imp(rna)[0] / rba) * 100

    # Tracé
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#e0f7fa','#b2ebf2','#80deea','#4dd0e1','#26c6da']
    for (b, h, _), c in zip(bareme, colors):
        ax.axvspan(b/12, h/12, facecolor=c, alpha=0.4)
    ax.plot(revenus_nets_m, taux_eff*100, label="Taux effectif", lw=2)
    ax.plot(revenus_nets_m, taux_marg_arr*100, '--', label="Taux marginal")
    ax.plot(revenus_nets_m, taux_nom*100, ':', label="Taux nominal")
    ax.axvline(salaire, color='red', ls='--')
    ax.plot(salaire, te_c, 'ro')
    ax.annotate(f"{te_c:.1f}%", (salaire, te_c),
                xytext=(salaire+200, te_c+2),
                arrowprops=dict(arrowstyle="->", color='red'),
                color='red')
    ax.set_xlabel("Salaire net mensuel (€)")
    ax.set_ylabel("Taux (%)")
    ax.set_title("Taux d'imposition 2025")
    ax.grid(True); ax.legend()
    st.pyplot(fig)

    # Analyse
    st.markdown("---")
    st.subheader("🧮 Analyse")
    st.markdown(f"""
- **Revenu net annuel** : {rna:.0f} €
- **Revenu brut estimé** : {rba:.0f} €
- **Impôt annuel** : {calc_imp(rna)[0]:.0f} €
- **Taux effectif** : {te_c:.1f} %
- **Taux marginal** : {tm_c:.1f} %
- **Taux nominal** : {tn_c:.1f} %
""")
    with st.expander("📊 Détail par tranche"):
        for bas, haut, tr, tx, mnt in details:
            st.markdown(f"- {bas:.0f}→{haut:.0f} : {tr:.0f}×{int(tx*100)}% = {mnt:.0f} €")


# --- Barre latérale de navigation simplifiée ---
st.sidebar.title("Menu")
page = st.sidebar.radio("", ["Simulation", "Page d'information"])

if page == "Simulation":
    simulation_page()
else:
    page_information()