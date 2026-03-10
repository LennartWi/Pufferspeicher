import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Batteriespeicher als Pufferspeicher", layout="wide")

st.title("Batteriespeicher als Pufferspeicher")
st.markdown("Visualisierung wie ein Batteriespeicher hilft, Ladeinfrastruktur ohne Netzausbau zu betreiben.")

# Sidebar
st.sidebar.header("Parameter")
netzanschluss = st.sidebar.slider("Netzanschluss (kW)", 50, 500, 200, 25)
speicher_kapazitaet = st.sidebar.slider("Speicherkapazität (kWh)", 100, 1000, 400, 50)
lkw_ladeleistung = st.sidebar.slider("LKW Ladeleistung (kW)", 100, 500, 350, 25)
lkw_batteriegroesse = st.sidebar.slider("LKW Batteriegröße (kWh)", 100, 600, 300, 50)
anzahl_lkw = st.sidebar.slider("Anzahl gleichzeitiger LKW", 1, 4, 1)

# Simulation
zeitschritte = 480  # 8 Stunden in Minuten
t = np.arange(zeitschritte)

# Lastprofil erstellen
def erstelle_lastprofil(zeitschritte, lkw_ladeleistung, lkw_batteriegroesse, anzahl_lkw):
    lastprofil = np.zeros(zeitschritte)
    ladezeit = int((lkw_batteriegroesse / lkw_ladeleistung) * 60)
    starts = []
    if anzahl_lkw >= 1: starts.append(30)
    if anzahl_lkw >= 2: starts.append(30)
    if anzahl_lkw >= 3: starts.append(200)
    if anzahl_lkw >= 4: starts.append(200)
    for s in starts:
        lastprofil[s:min(s + ladezeit, zeitschritte)] += lkw_ladeleistung
    return lastprofil

lastprofil = erstelle_lastprofil(zeitschritte, lkw_ladeleistung, lkw_batteriegroesse, anzahl_lkw)

# Energiefluss berechnen
netz_lieferung = np.zeros(zeitschritte)
speicher_lieferung = np.zeros(zeitschritte)
engpass = np.zeros(zeitschritte)
speicher_stand = np.zeros(zeitschritte)
aktueller_stand = speicher_kapazitaet * 0.8

for i in range(zeitschritte):
    bedarf = lastprofil[i]
    if bedarf > 0:
        netz = min(bedarf, netzanschluss)
        fehlend = bedarf - netz
        speicher_beitrag = min(fehlend, aktueller_stand * 60)
        aktueller_stand = max(aktueller_stand - speicher_beitrag / 60, 0)
        engpass[i] = max(fehlend - speicher_beitrag, 0)
        netz_lieferung[i] = netz
        speicher_lieferung[i] = speicher_beitrag
    else:
        ladekapazitaet = min(netzanschluss * 0.6, (speicher_kapazitaet - aktueller_stand) * 60)
        aktueller_stand = min(aktueller_stand + ladekapazitaet / 60, speicher_kapazitaet)
        netz_lieferung[i] = ladekapazitaet
    speicher_stand[i] = aktueller_stand

# Zeitachse in Stunden
stunden = t / 60

# Plotly Animation bauen
# Frames alle 10 Minuten
frame_step = 10
frames = []

for f in range(frame_step, zeitschritte + 1, frame_step):
    idx = f - 1
    frame_data = [
        # Gestapeltes Balkendiagramm: Netz
        go.Bar(
            x=["Energiefluss"],
            y=[netz_lieferung[idx]],
            name="Netz",
            marker_color="#2196F3",
            text=[f"{netz_lieferung[idx]:.0f} kW"],
            textposition="inside",
        ),
        # Speicher Beitrag
        go.Bar(
            x=["Energiefluss"],
            y=[speicher_lieferung[idx]],
            name="Batteriespeicher",
            marker_color="#4CAF50",
            text=[f"{speicher_lieferung[idx]:.0f} kW"],
            textposition="inside",
        ),
        # Engpass
        go.Bar(
            x=["Energiefluss"],
            y=[engpass[idx]],
            name="Engpass (nicht gedeckt)",
            marker_color="#f44336",
            text=[f"{engpass[idx]:.0f} kW"] if engpass[idx] > 0 else [""],
            textposition="inside",
        ),
        # Ladebedarf Linie
        go.Bar(
            x=["Ladebedarf LKW"],
            y=[lastprofil[idx]],
            name="LKW Bedarf",
            marker_color="#FF9800",
            text=[f"{lastprofil[idx]:.0f} kW"],
            textposition="inside",
        ),
        # Speicherstand
        go.Bar(
            x=["Speicherstand"],
            y=[speicher_stand[idx]],
            name="Speicher (kWh)",
            marker_color="#4CAF50",
            text=[f"{speicher_stand[idx]:.0f} kWh"],
            textposition="inside",
        ),
    ]
    frames.append(go.Frame(
        data=frame_data,
        name=str(f),
        layout=go.Layout(title_text=f"Zeit: {f//60:02d}:{f%60:02d} Uhr  |  Speicherstand: {speicher_stand[idx]:.0f} / {speicher_kapazitaet} kWh  |  LKW Bedarf: {lastprofil[idx]:.0f} kW")
    ))

# Initiale Daten (Frame 0)
fig = go.Figure(
    data=[
        go.Bar(x=["Energiefluss"], y=[netz_lieferung[0]], name="Netz", marker_color="#2196F3"),
        go.Bar(x=["Energiefluss"], y=[speicher_lieferung[0]], name="Batteriespeicher", marker_color="#4CAF50"),
        go.Bar(x=["Energiefluss"], y=[engpass[0]], name="Engpass (nicht gedeckt)", marker_color="#f44336"),
        go.Bar(x=["Ladebedarf LKW"], y=[lastprofil[0]], name="LKW Bedarf", marker_color="#FF9800"),
        go.Bar(x=["Speicherstand"], y=[speicher_stand[0]], name="Speicher (kWh)", marker_color="#4CAF50"),
    ],
    frames=frames,
    layout=go.Layout(
        title="Batteriespeicher als Puffer: Energiefluss über Zeit",
        barmode="stack",
        yaxis=dict(
            title="Leistung (kW) / Energie (kWh)",
            range=[0, max(max(lastprofil) * 1.2, speicher_kapazitaet * 1.1, netzanschluss * 1.2)]
        ),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                y=1.15,
                x=0.5,
                xanchor="center",
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[None, {"frame": {"duration": 100, "redraw": True}, "fromcurrent": True, "transition": {"duration": 50}}]
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}]
                    )
                ]
            )
        ],
        sliders=[dict(
            steps=[
                dict(method="animate", args=[[str(f)], {"mode": "immediate", "frame": {"duration": 100, "redraw": True}, "transition": {"duration": 50}}], label=f"{f//60:02d}:{f%60:02d}")
                for f in range(frame_step, zeitschritte + 1, frame_step)
            ],
            transition={"duration": 50},
            x=0, y=0,
            currentvalue={"prefix": "Zeit: ", "visible": True, "xanchor": "center"},
            len=1.0
        )],
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
)

st.plotly_chart(fig, use_container_width=True)

# Erklaerung
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Netzanschluss", f"{netzanschluss} kW")
    st.caption("Maximale Leistung aus dem Netz")
with col2:
    st.metric("LKW Ladebedarf", f"{lkw_ladeleistung * anzahl_lkw} kW")
    st.caption("Gesamtbedarf aller LKW gleichzeitig")
with col3:
    fehlende_leistung = max(lkw_ladeleistung * anzahl_lkw - netzanschluss, 0)
    st.metric("Speicher muss puffern", f"{fehlende_leistung} kW", delta="Differenz Netz zu Bedarf", delta_color="inverse")
    st.caption("Leistung die der Speicher liefern muss")

st.markdown("---")
st.markdown("""
**So funktioniert der Pufferspeicher:**
- **Blau (Netz):** Der Netzanschluss liefert konstant bis zur maximalen Kapazität
- **Grün (Batteriespeicher):** Der Speicher liefert die fehlende Leistung beim Ladevorgang und laedt sich in Pausen wieder auf
- **Orange (LKW Bedarf):** Der tatsaechliche Strombedarf des LKW
- **Rot (Engpass):** Leistung die weder Netz noch Speicher liefern koennen
""")
