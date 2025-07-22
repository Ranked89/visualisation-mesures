
import pandas as pd
import matplotlib.pyplot as plt
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path

# --- Étape 1 : Sélection du fichier CSV ---
Tk().withdraw()
filepath = askopenfilename(title="Choisir un fichier CSV", filetypes=[("CSV files", "*.csv")])
if not filepath:
    print("Aucun fichier sélectionné.")
    exit()

# --- Étape 2 : Chargement des données ---
df = pd.read_csv(filepath, sep=';', encoding='utf-8')
df.columns = df.columns.str.strip()

df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], errors="coerce", dayfirst=True)
df.drop(columns=["Date", "Heure"], inplace=True)
df = df.dropna(subset=["Timestamp"])
df = df.dropna(how='all', subset=df.columns.difference(['Timestamp']))

# --- Étape 3 : Identifier les types de colonnes ---
colonnes_temp = [col for col in df.columns if "Temp" in col]
colonnes_tension = [col for col in df.columns if "Tension" in col]
colonnes_courant = [col for col in df.columns if "Courant" in col]

# --- Étape 4 : Nom du fichier PDF basé sur le nom du fichier CSV ---
nom_fichier = Path(filepath).stem
output_pdf = f"{nom_fichier}_plots.pdf"

with PdfPages(output_pdf) as pdf:
    for col in colonnes_temp + colonnes_tension + colonnes_courant:
        data = df[["Timestamp", col]].dropna()
        if col in colonnes_tension + colonnes_courant:
            data["Seconde"] = data["Timestamp"].dt.floor("S")
            data = data.groupby("Seconde")[col].mean().reset_index()
            data[col] = data[col].rolling(window=5, center=True).mean()
            temps = data["Seconde"]
        else:
            temps = data["Timestamp"]

        # Tracer
        plt.figure()
        plt.plot(temps, data[col], marker='o')
        plt.title(col, loc='left')
        plt.xlabel("Temps")
        plt.ylabel(col)
        plt.xticks(rotation=45)

        if not data.empty:
            date_affichee = data.iloc[0]['Seconde'] if "Seconde" in data else data.iloc[0]['Timestamp']
            plt.figtext(0.01, 0.01, f"Date: {date_affichee.strftime('%d/%m/%Y')}", ha="left", fontsize=9)

        plt.tight_layout()
        pdf.savefig()
        plt.close()

print(f"✅ PDF généré : {output_pdf}")
