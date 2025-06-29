import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

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

import math

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
    ["Simulation", "Page d'information", "Capacité d'emprunt"]
)

if page == "Simulation":
    simulation_page()
elif page == "Page d'information":
    page_information()
elif page == "Capacité d'emprunt":
    page_credit()

