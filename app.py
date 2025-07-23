# Importation des bibliothèques nécessaires
import streamlit as st  # Pour créer une interface web interactive
import pandas as pd  # Pour manipuler les données du fichier CSV
import matplotlib.pyplot as plt  # Pour créer les graphiques
from matplotlib.backends.backend_pdf import PdfPages  # Pour générer un fichier PDF contenant les figures
import io  # Pour créer un fichier PDF en mémoire (sans l'enregistrer sur le disque)

# Titre principal de l'application
st.title("📊 Visualisation de mesures CSV")

# Interface pour importer un fichier CSV depuis l'ordinateur de l'utilisateur
uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")

# Si un fichier a été sélectionné :
if uploaded_file:
    # Lecture du fichier CSV avec séparateur ";" et encodage UTF-8
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')

    # Suppression des éventuels espaces autour des noms de colonnes
    df.columns = df.columns.str.strip()

    # Création d'une colonne datetime unique à partir des colonnes "Date" et "Heure"
    df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], errors="coerce", dayfirst=True)

    # Suppression des colonnes "Date" et "Heure" devenues inutiles
    df.drop(columns=["Date", "Heure"], inplace=True)

    # Suppression des lignes dont le timestamp est invalide (non interprétable)
    df = df.dropna(subset=["Timestamp"])

    # Suppression des lignes vides (sauf la colonne Timestamp)
    df = df.dropna(how='all', subset=df.columns.difference(['Timestamp']))

    # Détection des colonnes par type (Température, Tension, Courant)
    colonnes_temp = [col for col in df.columns if "Temp" in col]
    colonnes_tension = [col for col in df.columns if "Tension" in col]
    colonnes_courant = [col for col in df.columns if "Courant" in col]

    # Création d'un fichier PDF en mémoire (pas encore téléchargé)
    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        # Boucle sur toutes les colonnes sélectionnées
        for col in colonnes_temp + colonnes_tension + colonnes_courant:
            # On récupère la colonne de mesure + timestamp, et on enlève les lignes vides
            data = df[["Timestamp", col]].dropna()

            # Si la colonne est une tension ou un courant (mesure à haute fréquence)
            if col in colonnes_tension + colonnes_courant:
                # On arrondit les timestamps à la seconde près
                data["Seconde"] = data["Timestamp"].dt.floor("S")

                # On fait la moyenne des valeurs par seconde
                data = data.groupby("Seconde")[col].mean().reset_index()

                # On applique une moyenne glissante (rolling mean) pour lisser les données
                data[col] = data[col].rolling(window=5, center=True).mean()

                # On utilisera les secondes comme axe x
                temps = data["Seconde"]
            else:
                # Pour les températures (1 point par minute), on garde les timestamps d’origine
                temps = data["Timestamp"]

            # Création du graphique
            plt.figure()
            plt.plot(temps, data[col], marker='o')  # Courbe avec points visibles
            plt.title(col)  # Titre = nom de la mesure
            plt.xlabel("Temps")  # Légende de l’axe des x
            plt.ylabel(col)  # Légende de l’axe des y
            plt.xticks(rotation=45)  # Rotation des dates sur l’axe x

            # On affiche la date dans le coin inférieur gauche (hors de l’axe)
            if not data.empty:
                date_affichee = data.iloc[0]['Seconde'] if "Seconde" in data else data.iloc[0]['Timestamp']
                plt.figtext(0.01, 0.01, f"Date: {date_affichee.strftime('%d/%m/%Y')}", ha="left", fontsize=9)

            plt.tight_layout()  # Ajustement automatique pour éviter les chevauchements
            pdf.savefig()  # Ajout du graphique au PDF
            plt.close()  # Fermeture de la figure (bonne pratique pour libérer de la mémoire)

    # Message de succès dans l’interface utilisateur
    st.success("✅ PDF généré avec succès !")

    # Bouton de téléchargement du fichier PDF généré
    st.download_button("📥 Télécharger le PDF", data=pdf_buffer.getvalue(),
                       file_name="mesures_plots.pdf", mime="application/pdf")
