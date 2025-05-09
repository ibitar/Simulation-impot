import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Initialisation des variables dans session_state
if "simulation1" not in st.session_state:
    st.session_state["simulation1"] = None
if "simulation2" not in st.session_state:
    st.session_state["simulation2"] = None

# Fonction de calcul d'impôt
def calcul_impot(revenu_salarial, chiffre_affaire_autoentrepreneur, nombre_parts, reduction_forfaitaire=False, aide_familiale=0, frais_garde=0, est_couple=False):
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

# Sidebar pour navigation
page = st.sidebar.radio(
    "Choisissez une simulation :",
    ["Simulation 1", "Simulation 2", "Comparaison", "Page d'information"]
)

# Informations contextuelles sur les tranches et la décote (année 2025)
st.sidebar.markdown("### Informations fiscales 2025")

st.sidebar.markdown("**Tranches d'imposition (revenu net imposable annuel par part)** :")
st.sidebar.markdown("- Jusqu'à 11 497 € : 0%")
st.sidebar.markdown("- 11 497 € à 29 315 € : 11%")
st.sidebar.markdown("- 29 315 € à 83 823 € : 30%")
st.sidebar.markdown("- 83 823 € à 180 294 € : 41%")
st.sidebar.markdown("- Plus de 180 294 € : 45%")

st.sidebar.markdown("**Décote 2025** :")
st.sidebar.markdown("- **Personne seule** : si impôt < 1 965 €, alors décote = max(0, 889 - 45,25% de l’impôt)")
st.sidebar.markdown("- **Couple marié/pacsé** : si impôt < 3 249 €, alors décote = max(0, 1 470 - 45,25% de l’impôt)")

# Fonction pour afficher une page de simulation
def simulation_page(titre, key):
    st.title(titre)

    revenu_salarial = st.number_input("Revenu Salarial Annuel Net Imposable (€)", min_value=0.0, step=1000.0, key=f"{key}_revenu")
    chiffre_affaire_autoentrepreneur = st.number_input("Chiffre d'Affaires Auto-Entrepreneur Annuel (€)", min_value=0.0, step=1000.0, key=f"{key}_autoentrepreneur")
    nombre_parts = st.number_input("Nombre de Parts", min_value=1.0, step=0.5, key=f"{key}_parts")
    aide_familiale = st.number_input("Aide Familiale (€)", min_value=0.0, step=100.0, key=f"{key}_aide")
    frais_garde = st.number_input("Frais de Garde (€)", min_value=0.0, step=100.0, key=f"{key}_frais")

    reduction_forfaitaire = st.checkbox("Réduction Forfaitaire de 10% sur Revenu Salarial", key=f"{key}_reduction")
    est_couple = st.checkbox("Couple (Marié/Pacsé)", key=f"{key}_couple")

    if st.button("Calculer", key=f"{key}_calculer"):
        st.session_state[key] = calcul_impot(
            revenu_salarial,
            chiffre_affaire_autoentrepreneur,
            nombre_parts,
            reduction_forfaitaire,
            aide_familiale,
            frais_garde,
            est_couple
        )
        st.success(f"Simulation {titre} enregistrée avec succès.")

    if st.session_state[key]:
        result = st.session_state[key]
        with st.expander("Résumé des Résultats"):
            st.metric("Impôt Final Annuel à Payer (€)", f"{result['impot_final']:.2f}")
            st.metric("Revenu Net Mensuel (€)", f"{result['revenu_net_mensuel']:.2f}")
        
        with st.expander("Détails des Calculs"):
            for k, v in result['details'].items():
                st.write(f"**{k} :** {v:.2f} €")
        
        with st.expander("Détails des Tranches d'Imposition"):
            for tranche in result["details_tranches"]:
                st.write(tranche)

def page_information():
    st.title("📊 Visualisation des taux d'imposition 2025")

    salaire = st.slider("Sélectionnez votre salaire net mensuel avant impôt (€)", 1000, 15000, 3000, step=100)

    fig, ax = plt.subplots(figsize=(12, 7))

    # Données
    revenus_bruts_mensuels = np.linspace(1000, 15000, 500)
    revenus_bruts_annuels = revenus_bruts_mensuels * 12
    revenus_nets_annuels = revenus_bruts_annuels * 0.77
    revenus_nets_mensuels = revenus_nets_annuels / 12

    # Barème
    bareme = [
        (0, 11294, 0.00),
        (11294, 28797, 0.11),
        (28797, 82341, 0.30),
        (82341, 177106, 0.41),
        (177106, float('inf'), 0.45)
    ]

    def calcul_impot(r):
        i, d = 0, []
        for bas, haut, taux in bareme:
            if r > bas:
                tr = min(haut, r) - bas
                m = tr * taux
                i += m
                d.append((bas, min(haut, r), tr, taux, m))
            else:
                break
        return i, d

    def taux_marginal(r):
        for bas, _, taux in reversed(bareme):
            if r > bas:
                return taux
        return 0.0

    impots_annuels = np.array([calcul_impot(r)[0] for r in revenus_nets_annuels])
    taux_eff = impots_annuels / revenus_nets_annuels
    taux_marg = np.array([taux_marginal(r) for r in revenus_nets_annuels])
    taux_nom = impots_annuels / revenus_bruts_annuels

    # Valeurs cibles
    revenu_net_annuel = salaire * 12
    revenu_brut_annuel = revenu_net_annuel / 0.77
    revenu_brut_mensuel = revenu_brut_annuel / 12
    impot, details = calcul_impot(revenu_net_annuel)
    taux_eff_cible = impot / revenu_net_annuel * 100
    taux_marg_cible = taux_marginal(revenu_net_annuel) * 100
    taux_nom_cible = impot / revenu_brut_annuel * 100

    # Tracés
    couleurs = ['#e0f7fa', '#b2ebf2', '#80deea', '#4dd0e1', '#26c6da']
    for (bas, haut, _), c in zip(bareme, couleurs):
        ax.axvspan(bas / 12, haut / 12, facecolor=c, alpha=0.4)

    ax.plot(revenus_nets_mensuels, taux_eff * 100, label="Taux effectif", linewidth=2)
    ax.plot(revenus_nets_mensuels, taux_marg * 100, '--', label="Taux marginal")
    ax.plot(revenus_nets_mensuels, taux_nom * 100, ':', label="Taux nominal")

    ax.axvline(salaire, color='red', linestyle='--')
    ax.plot(salaire, taux_eff_cible, 'ro', label=f"Vous ({salaire} €)")
    ax.annotate(f"{taux_eff_cible:.1f}%", 
                xy=(salaire, taux_eff_cible), 
                xytext=(salaire + 200, taux_eff_cible + 2),
                arrowprops=dict(arrowstyle="->", color='red'),
                fontsize=10, color='red')

    ax.set_xlabel("Salaire net mensuel (€)")
    ax.set_ylabel("Taux (%)")
    ax.set_title("Taux d'imposition 2025 en fonction du salaire net mensuel")
    ax.set_xticks(np.arange(0, 15001, 1000))
    ax.set_yticks(np.arange(0, 51, 5))
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    # Analyse textuelle
    st.markdown("---")
    st.subheader("🧮 Analyse pour votre salaire sélectionné")
    st.markdown(f"""
- **Revenu net annuel** : {revenu_net_annuel:.0f} €
- **Revenu brut estimé** : {revenu_brut_annuel:.0f} €
- **Impôt annuel** : {impot:.0f} €
- **Taux effectif** : {taux_eff_cible:.1f} %
- **Taux marginal** : {taux_marg_cible:.1f} %
- **Taux nominal** : {taux_nom_cible:.1f} %
""")
    with st.expander("📊 Détail par tranche"):
        for bas, haut, tr, tx, mnt in details:
            st.markdown(f"- {bas:.0f} € → {haut:.0f} € : {tr:.0f} € × {int(tx * 100)}% = {mnt:.0f} €")


# Comparaison des deux simulations
if page == "Simulation 1":
    simulation_page("Simulation 1", "simulation1")
elif page == "Simulation 2":
    simulation_page("Simulation 2", "simulation2")
elif page == "Comparaison":
    st.title("Comparaison des Simulations")
    if st.session_state["simulation1"] and st.session_state["simulation2"]:
        sim1 = st.session_state["simulation1"]
        sim2 = st.session_state["simulation2"]

        st.subheader("Résumé des Résultats")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Simulation 1**")
            st.metric("Impôt Final (€)", f"{sim1['impot_final']:.2f}")
            st.metric("Revenu Net Mensuel (€)", f"{sim1['revenu_net_mensuel']:.2f}")
        with col2:
            st.write("**Simulation 2**")
            st.metric("Impôt Final (€)", f"{sim2['impot_final']:.2f}")
            st.metric("Revenu Net Mensuel (€)", f"{sim2['revenu_net_mensuel']:.2f}")

        st.subheader("Récapitulatif des Hypothèses")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Simulation 1**")
            st.write(f"- Nombre de Parts : {sim1['nombre_parts']:.2f}")
            for k, v in sim1["details"].items():
                st.write(f"- **{k} :** {v:.2f} €")
        with col2:
            st.write("**Simulation 2**")
            st.write(f"- Nombre de Parts : {sim2['nombre_parts']:.2f}")
            for k, v in sim2["details"].items():
                st.write(f"- **{k} :** {v:.2f} €")
    elif page == "Page d'information":
        page_information()
        
    else:
        st.warning("Veuillez compléter les deux simulations avant de comparer.")
