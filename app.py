
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.title("Visualisation interactive de données (version Plotly)")

uploaded_file = st.file_uploader("Choisissez un fichier CSV", type=["csv"])
lissage = st.slider("Niveau de lissage (0 = brut, max = 10)", 0, 10, 3)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
    df.columns = df.columns.str.strip()

    df["Timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], errors="coerce", dayfirst=True)
    df.drop(columns=["Date", "Heure"], inplace=True)
    df = df.dropna(subset=["Timestamp"])
    df = df.dropna(how='all', subset=df.columns.difference(['Timestamp']))

    if df["Timestamp"].empty:
        st.error("Aucune donnée horodatée détectée dans le fichier.")
        st.stop()

    heure_min = df["Timestamp"].min().to_pydatetime()
    heure_max = df["Timestamp"].max().to_pydatetime()

    debut, fin = st.slider(
        "Sélectionnez une plage horaire à afficher",
        min_value=heure_min,
        max_value=heure_max,
        value=(heure_min, heure_max),
        format="HH:mm"
    )

    df = df[(df["Timestamp"] >= debut) & (df["Timestamp"] <= fin)]

    colonnes_temp = [col for col in df.columns if "Temp" in col]
    colonnes_tension = [col for col in df.columns if "Tension" in col]
    colonnes_courant = [col for col in df.columns if "Courant" in col]

    colonnes_a_afficher = colonnes_temp + colonnes_tension + colonnes_courant

    mesure_choisie = st.selectbox("Choisissez une mesure à afficher", colonnes_a_afficher)

    data = df[["Timestamp", mesure_choisie]].copy()

    if mesure_choisie in colonnes_tension + colonnes_courant:
        data["Timestamp"] = data["Timestamp"].dt.floor("S")
        data = data.groupby("Timestamp")[mesure_choisie].mean().reset_index()

        if lissage > 0:
            data[mesure_choisie] = data[mesure_choisie].rolling(window=lissage, center=True).mean()

    if data[mesure_choisie].dropna().empty:
        st.warning("Pas de données valides à afficher pour cette mesure.")
    else:
        fig = px.line(
            data.dropna(),
            x="Timestamp",
            y=mesure_choisie,
            title=f"Courbe interactive : {mesure_choisie}",
            labels={"Timestamp": "Heure", mesure_choisie: mesure_choisie}
        )
        fig.update_layout(xaxis_title="Heure", yaxis_title=mesure_choisie, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
