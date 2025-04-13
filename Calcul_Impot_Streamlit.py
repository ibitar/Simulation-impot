import streamlit as st

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
st.sidebar.title("Navigation")
page = st.sidebar.radio("Choisissez une simulation :", ["Simulation 1", "Simulation 2", "Comparaison"])

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
    else:
        st.warning("Veuillez compléter les deux simulations avant de comparer.")
