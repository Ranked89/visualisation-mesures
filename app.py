
# Importation des bibliothèques nécessaires
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO
import matplotlib.dates as mdates
from datetime import datetime

# Titre de l'application
st.title("Visualisation de données de datalogger")

# Interface de chargement de fichier CSV
uploaded_file = st.file_uploader("Choisissez un fichier CSV", type=["csv"])

# Interface de réglage du niveau de lissage (0 = brut, jusqu'à 10 = très lissé)
lissage = st.slider("Niveau de lissage (0 = aucun, max = 10)", 0, 10, 3)

# Si un fichier est fourni par l'utilisateur
if uploaded_file is not None:
    # Lecture du fichier CSV
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    df.columns = df.columns.str.strip()  # Nettoyage des noms de colonnes

    # Création d'une colonne datetime unique à partir de Date + Heure
    df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], errors="coerce", dayfirst=True)
    df.drop(columns=["Date", "Heure"], inplace=True)

    # Suppression des lignes sans timestamp
    df = df.dropna(subset=["Timestamp"])

    # Suppression des lignes totalement vides (hors timestamp)
    df = df.dropna(how='all', subset=df.columns.difference(['Timestamp']))

    # Vérification des timestamps valides
    if df["Timestamp"].empty:
        st.error("Aucune donnée horodatée détectée dans le fichier.")
        st.stop()

    # Conversion explicite des bornes horaires en datetime.datetime
    heure_min = df["Timestamp"].min().to_pydatetime()
    heure_max = df["Timestamp"].max().to_pydatetime()

    # Sélection de la plage horaire avec affichage des heures
    debut, fin = st.slider(
        "Sélectionnez une plage horaire à afficher",
        min_value=heure_min,
        max_value=heure_max,
        value=(heure_min, heure_max),
        format="HH:mm"
    )

    # Filtrage global du DataFrame en fonction de la plage choisie
    df = df[(df["Timestamp"] >= debut) & (df["Timestamp"] <= fin)]

    # Détection automatique des types de mesures à tracer
    colonnes_temp = [col for col in df.columns if "Temp" in col]
    colonnes_tension = [col for col in df.columns if "Tension" in col]
    colonnes_courant = [col for col in df.columns if "Courant" in col]

    # Création d'un buffer mémoire pour stocker le PDF
    buffer = BytesIO()

    # Création du fichier PDF contenant tous les graphes
    with PdfPages(buffer) as pdf:
        for col in colonnes_temp + colonnes_tension + colonnes_courant:
            data = df[["Timestamp", col]].copy()

            # Traitement spécifique pour les mesures rapides : groupement par seconde et lissage
            if col in colonnes_tension + colonnes_courant:
                data["Timestamp"] = data["Timestamp"].dt.floor("S")
                data = data.groupby("Timestamp")[col].mean().reset_index()

                # Application du lissage si demandé
                if lissage > 0:
                    data[col] = data[col].rolling(window=lissage, center=True).mean()

            # On ignore les courbes vides
            if data[col].dropna().empty:
                continue

            # Création du graphique
            plt.figure(figsize=(10, 4))
            ax = plt.gca()
            valid = data.dropna(subset=[col])
            ax.plot(valid["Timestamp"], valid[col], linestyle='-')  # Tracé de la courbe

            # Ajustement dynamique de l'axe X selon la durée des données
            min_time = valid["Timestamp"].min()
            max_time = valid["Timestamp"].max()
            duration = (max_time - min_time).total_seconds()
            ax.set_xlim([min_time, max_time])

            # Format d'affichage de l'axe X en fonction de la durée
            if duration <= 600:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax.xaxis.set_major_locator(mdates.SecondLocator(interval=30))
            elif duration <= 1800:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
            elif duration <= 3600:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
            elif duration <= 10800:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))

            # Mise en forme du graphique
            plt.xticks(rotation=45)
            plt.title(col, loc='left')
            plt.xlabel("Heure")
            plt.ylabel(col)
            ax.grid(True, which='major', linestyle='--', linewidth=0.5, alpha=0.7)
            plt.tight_layout()

            # Ajout du graphique au PDF et affichage dans Streamlit
            pdf.savefig()
            st.pyplot(plt.gcf())
            plt.close()

    # Retour au début du fichier PDF
    buffer.seek(0)

    # Bouton de téléchargement du PDF généré
    st.download_button(
        label="📥 Télécharger le PDF complet",
        data=buffer,
        file_name="graphiques_datalogger.pdf",
        mime="application/pdf"
    )
