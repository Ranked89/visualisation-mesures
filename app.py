import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import io

st.title("📊 Visualisation de mesures CSV")

uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    df.columns = df.columns.str.strip()
    df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], errors="coerce", dayfirst=True)
    df.drop(columns=["Date", "Heure"], inplace=True)
    df = df.dropna(subset=["Timestamp"])
    df = df.dropna(how='all', subset=df.columns.difference(['Timestamp']))

    colonnes_temp = [col for col in df.columns if "Temp" in col]
    colonnes_tension = [col for col in df.columns if "Tension" in col]
    colonnes_courant = [col for col in df.columns if "Courant" in col]

    pdf_buffer = io.BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        for col in colonnes_temp + colonnes_tension + colonnes_courant:
            data = df[["Timestamp", col]].dropna()
            if col in colonnes_tension + colonnes_courant:
                data["Seconde"] = data["Timestamp"].dt.floor("S")
                data = data.groupby("Seconde")[col].mean().reset_index()
                data[col] = data[col].rolling(window=5, center=True).mean()
                temps = data["Seconde"]
            else:
                temps = data["Timestamp"]

            plt.figure()
            plt.plot(temps, data[col], marker='o')
            plt.title(col)
            plt.xlabel("Temps")
            plt.ylabel(col)
            plt.xticks(rotation=45)
            if not data.empty:
                date_affichee = data.iloc[0]['Seconde'] if "Seconde" in data else data.iloc[0]['Timestamp']
                plt.figtext(0.01, 0.01, f"Date: {date_affichee.strftime('%d/%m/%Y')}", ha="left", fontsize=9)
            plt.tight_layout()
            pdf.savefig()
            plt.close()

    st.success("✅ PDF généré avec succès !")
    st.download_button("📥 Télécharger le PDF", data=pdf_buffer.getvalue(),
                       file_name="mesures_plots.pdf", mime="application/pdf")
