"""
AImplement.com - AI platform for the GWW sector (civil & infrastructure).

Run:  streamlit run aimplement_app.py
Deps: pip install streamlit        (core app)
      pip install ultralytics      (optional: real YOLOv8 detection)
"""
import json
import tempfile
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="AImplement GWW Portal", page_icon="🏗️", layout="wide")

# ----------------------------------------------------------------- data ----
MODULES = {
    "AI Weg- & Kade-Inspectie": "Upload drone- of dashcambeelden; schade wordt gedetecteerd en als GIS-bestand geëxporteerd.",
    "RAW & CROW Kennis-RAG": "Zoek in bestekken en normen en vind direct het juiste RAW-artikel.",
    "Parametrische Bestek-Generator": "Ontwerpparameters in, hoeveelhedenstaat en bestekregels uit.",
}

PLANS = [
    {"name": "Pay-Per-Scan", "price": "€ 249", "unit": "per inspectierapport",
     "features": ["Tot 25 km weg-/kade-analyse", "YOLOv8 schadedetectie",
                  "PDF & Shapefile export", "E-mail support binnen 24 uur"]},
    {"name": "Professional Pro", "price": "€ 890", "unit": "per maand (excl. btw)", "highlight": True,
     "features": ["Onbeperkte RAW & CROW zoekopdrachten", "Tot 250 km inspectie / maand",
                  "5 gebruikerslicenties", "API & QGIS integratie", "Telefonische support & SLA"]},
    {"name": "Enterprise Infra", "price": "Op maat", "unit": "jaarlijks contract",
     "features": ["Onbeperkte km & RAG-toegang", "Private cloud / on-premise",
                  "Maatwerk modeltraining", "Dedicated account manager"]},
]

# Small demo knowledge base; replace with a real vector store / RAG backend.
RAW_KB = {
    "asfalt": ("84.12.01", "Asfaltverharding: eisen aan samenstelling en verwerking."),
    "verdichting": ("84.12.05", "Verdichting asfaltmengsel: minimale holle ruimte en walspatroon."),
    "fundering": ("83.05.00", "Funderingslagen van menggranulaat: laagdikte en draagkracht."),
    "kade": ("22.20.00", "Kademuren en damwanden: toleranties en inspectie-eisen."),
}


# ------------------------------------------------------------ functions ----
def roi(km: int, fte: int, rate: int, license_cost: int = 6000) -> tuple[int, int, int]:
    """Return (hours saved, euro savings, ROI %) - same model as the website."""
    hours = round(km * 1.5 + fte * 30)
    savings = hours * rate
    return hours, savings, round(savings / license_cost * 100)


def euro(value: int) -> str:
    return f"€ {value:,}".replace(",", ".") + ",-"


@st.cache_resource(show_spinner="YOLOv8 model laden...")
def load_model():
    """Load YOLOv8 once; return None when ultralytics/weights are unavailable."""
    try:
        from ultralytics import YOLO
        return YOLO("yolov8n.pt")  # swap for your trained road-damage weights
    except Exception:
        return None


def detect(file, model) -> list[dict]:
    """Run detection on an image; fall back to one demo detection without a model."""
    if model is None or file.type.startswith("video"):
        return [{"label": "Rafeling", "conf": 0.964, "raw": "84.12.01"}]
    with tempfile.NamedTemporaryFile(suffix=Path(file.name).suffix) as tmp:
        tmp.write(file.getvalue())
        tmp.flush()
        result = model(tmp.name, verbose=False)[0]
    return [{"label": result.names[int(b.cls)], "conf": float(b.conf), "raw": "84.12.01"}
            for b in result.boxes]


def to_geojson(detections: list[dict], lat: float, lon: float) -> str:
    features = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": d,
    } for d in detections]
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2)


# ---------------------------------------------------------------- views ----
def view_inspection():
    st.subheader("AI Weg- & Kade-Inspectie")
    file = st.file_uploader("Upload dashcam- of drone-beeld", type=["jpg", "jpeg", "png", "mp4"])
    c1, c2 = st.columns(2)
    lat = c1.number_input("Breedtegraad", value=52.37, format="%.5f")
    lon = c2.number_input("Lengtegraad", value=4.90, format="%.5f")
    if not file:
        return
    model = load_model()
    if model is None:
        st.info("Demo-modus: installeer `ultralytics` voor echte detectie.")
    with st.spinner("Analyse uitgevoerd..."):
        found = detect(file, model)
    st.success(f"{len(found)} schadepunt(en) gedetecteerd")
    st.dataframe(found, use_container_width=True)
    st.download_button("📥 Download GIS-rapport (GeoJSON)", to_geojson(found, lat, lon),
                       file_name="aimplement_inspectie.geojson", mime="application/geo+json")


def view_rag():
    st.subheader("RAW & CROW Kennis-RAG")
    query = st.text_input("Stel een vraag over bestek of norm", placeholder="bijv. verdichting asfalt")
    if query:
        hits = [(k, v) for k, v in RAW_KB.items() if k in query.lower()]
        for _, (art, text) in hits:
            st.metric("RAW-artikel", art)
            st.write(text)
        if not hits:
            st.warning("Geen match in de demo-kennisbank.")


def view_spec():
    st.subheader("Parametrische Bestek-Generator")
    c1, c2, c3 = st.columns(3)
    length = c1.number_input("Lengte (m)", 1, 100_000, 500)
    width = c2.number_input("Breedte (m)", 1.0, 50.0, 6.5)
    thick = c3.number_input("Laagdikte (mm)", 20, 300, 50)
    area = length * width
    tonnes = area * thick / 1000 * 2.4  # asfalt ~2,4 t/m³
    st.table({
        "Post": ["Asfaltverharding (RAW 84.12.01)", "Oppervlakte", "Gewicht asfalt"],
        "Hoeveelheid": ["", f"{area:,.0f} m²", f"{tonnes:,.0f} ton"],
    })


def view_roi():
    st.subheader("Bereken uw besparing")
    c1, c2, c3 = st.columns(3)
    km = c1.slider("Kilometers per jaar", 10, 1000, 150)
    fte = c2.slider("Werkvoorbereiders (FTE)", 1, 50, 5)
    rate = c3.number_input("Uurtarief (€)", 1, 500, 85)
    hours, savings, pct = roi(km, fte, rate)
    m1, m2, m3 = st.columns(3)
    m1.metric("Bespaarde uren", f"{hours} uur/jaar")
    m2.metric("Financiële besparing", euro(savings))
    m3.metric("ROI op licentie", f"{pct}%")


def view_pricing():
    st.subheader("Pakketten & Tarieven")
    for col, plan in zip(st.columns(len(PLANS)), PLANS):
        with col.container(border=True):
            st.markdown(f"### {plan['name']}" + (" ⭐" if plan.get("highlight") else ""))
            st.markdown(f"## {plan['price']}")
            st.caption(plan["unit"])
            for f in plan["features"]:
                st.markdown(f"✅ {f}")
            if st.button("Selecteer", key=plan["name"], use_container_width=True):
                st.session_state["plan"] = plan["name"]
    st.divider()
    contact_form()


def contact_form():
    st.subheader("Demo aanvragen of direct bestellen")
    with st.form("contact", clear_on_submit=True):
        c1, c2 = st.columns(2)
        company = c1.text_input("Bedrijfsnaam *")
        person = c2.text_input("Contactpersoon *")
        email = st.text_input("Zakelijk e-mailadres *")
        interest = st.selectbox("Interesse in module", [*MODULES, "Volledig AImplement platform"])
        note = st.text_area("Toelichting / vraag")
        if st.form_submit_button("Aanvraag versturen"):
            if not (company and person and "@" in email):
                st.error("Vul alle verplichte velden correct in.")
            else:
                # TODO: send to CRM / e-mail / database
                st.success("Aanvraag ontvangen! We nemen binnen 2 uur contact op.")


# ----------------------------------------------------------------- main ----
st.title("🏗️ AImplement.com")
st.caption("AI-platform voor Grond-, Weg- en Waterbouw · Voldoet aan RAW, CROW & NEN")

if plan := st.session_state.get("plan"):
    st.info(f"Licentie '{plan}' geselecteerd - vul onderaan het formulier in om te activeren.")

with st.sidebar:
    st.header("Navigatie")
    page = st.radio("Pagina", ["Platform", "ROI Calculator", "Pakketten & Tarieven"],
                    label_visibility="collapsed")
    if page == "Platform":
        module = st.selectbox("Kies AI-module", list(MODULES))
        st.caption(MODULES[module])

if page == "Platform":
    {"AI Weg- & Kade-Inspectie": view_inspection,
     "RAW & CROW Kennis-RAG": view_rag,
     "Parametrische Bestek-Generator": view_spec}[module]()
elif page == "ROI Calculator":
    view_roi()
else:
    view_pricing()
