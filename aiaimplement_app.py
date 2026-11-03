"""
AIAImplement.com - polished Streamlit website (hero, cards, live demos, pricing, contact).

Run:  streamlit run aiaimplement_app.py
Deps: pip install streamlit   (optional: ultralytics for real YOLOv8 detection)
"""
import json
import tempfile
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="AIAImplement | AI voor GWW", page_icon="🏗️", layout="wide")

# ---------------------------------------------------------------- style ----
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 1100px; padding-top: 1.5rem; }

.nav { display:flex; justify-content:space-between; align-items:center; padding:.5rem 0 1.5rem; }
.logo { font-size:1.4rem; font-weight:800; letter-spacing:-.02em; }
.logo span { color:#3B82F6; }
.badge { font-size:.75rem; padding:.3rem .8rem; border:1px solid #1E293B; border-radius:999px; color:#94A3B8; }

.hero { text-align:center; padding:3.5rem 1rem 3rem; border-radius:24px; margin-bottom:2rem;
        background: radial-gradient(circle at 50% 0%, rgba(59,130,246,.25), transparent 60%), #0B1222;
        border:1px solid #1E293B; }
.hero h1 { font-size:3rem; font-weight:800; line-height:1.1; letter-spacing:-.03em; margin:0 0 1rem; }
.hero h1 em { font-style:normal; background:linear-gradient(90deg,#60A5FA,#34D399);
              -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hero p { color:#94A3B8; font-size:1.1rem; max-width:620px; margin:0 auto; }

.stats { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin-bottom:2rem; }
.stat { text-align:center; padding:1.2rem; border-radius:16px; background:#0F172A; border:1px solid #1E293B; }
.stat b { display:block; font-size:1.8rem; color:#60A5FA; }
.stat span { color:#94A3B8; font-size:.85rem; }

.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1rem; margin:1rem 0 2rem; }
.card { padding:1.5rem; border-radius:18px; background:#0F172A; border:1px solid #1E293B;
        transition:transform .2s, border-color .2s; }
.card:hover { transform:translateY(-4px); border-color:#3B82F6; }
.card .ico { font-size:1.8rem; margin-bottom:.6rem; }
.card h3 { margin:0 0 .4rem; font-size:1.1rem; }
.card p, .card li { color:#94A3B8; font-size:.9rem; }
.card ul { padding-left:1.1rem; margin:.8rem 0 0; }
.card .price { font-size:2.2rem; font-weight:800; margin:.4rem 0 0; }
.card .unit { color:#64748B; font-size:.8rem; }
.card.hot { border-color:#3B82F6; box-shadow:0 0 40px rgba(59,130,246,.18); }
.tag { display:inline-block; font-size:.7rem; font-weight:600; padding:.2rem .6rem; margin-bottom:.6rem;
       border-radius:999px; background:#3B82F6; color:white; }

.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {
    border-radius:12px; font-weight:600; border:0; padding:.6rem 1.4rem;
    background:linear-gradient(90deg,#2563EB,#3B82F6); color:white; }
.stButton>button:hover, .stFormSubmitButton>button:hover { filter:brightness(1.1); }

.stTabs [data-baseweb="tab-list"] { gap:.5rem; border-bottom:1px solid #1E293B; }
.stTabs [data-baseweb="tab"] { padding:.7rem 1.2rem; color:#94A3B8; background:none; }
.stTabs [aria-selected="true"] { color:#F1F5F9; }
.stTabs [data-baseweb="tab-highlight"] { background:#3B82F6; }
.stTabs [data-baseweb="tab-border"] { background:#1E293B; }
[data-testid="stVerticalBlockBorderWrapper"] { background:#0B1222; border:1px solid #1E293B !important; border-radius:14px; }
[data-testid="stFileUploaderDropzone"] { border:1.5px dashed #334155; border-radius:12px; background:transparent; }
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stSelectbox [data-baseweb="select"] > div { background:#0F172A !important; border:1px solid #1E293B !important; border-radius:10px; }
.footer { text-align:center; color:#64748B; font-size:.8rem; padding:2rem 0 1rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def html(markup: str) -> None:
    """Render HTML; strip indentation so Markdown doesn't turn it into a code block."""
    st.markdown("\n".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


# ----------------------------------------------------------------- data ----
MODULES = [
    ("🛣️", "AI Weg- & Kade-Inspectie", "Drone- en dashcambeelden worden automatisch geanalyseerd op schade. Export naar GIS."),
    ("📚", "RAW & CROW Kennis-RAG", "Vraag het in gewoon Nederlands en krijg direct het juiste RAW-artikel."),
    ("📐", "Parametrische Bestek-Generator", "Ontwerpparameters erin, hoeveelhedenstaat en bestekregels eruit."),
]

PLANS = [
    ("Pay-Per-Scan", "€ 249", "per inspectierapport", False,
     ["Tot 25 km analyse", "YOLOv8 schadedetectie", "PDF & Shapefile export", "E-mail support"]),
    ("Professional Pro", "€ 890", "per maand (excl. btw)", True,
     ["Onbeperkt RAW & CROW zoeken", "Tot 250 km / maand", "5 gebruikerslicenties", "API & QGIS integratie", "SLA support"]),
    ("Enterprise Infra", "Op maat", "jaarlijks contract", False,
     ["Onbeperkte km & RAG", "Private cloud / on-premise", "Maatwerk modeltraining", "Dedicated account manager"]),
]

RAW_KB = {  # demo knowledge base: replace with a real vector store
    "asfalt": ("84.12.01", "Asfaltverharding: eisen aan samenstelling en verwerking."),
    "verdichting": ("84.12.05", "Verdichting asfaltmengsel: holle ruimte en walspatroon."),
    "fundering": ("83.05.00", "Funderingslagen van menggranulaat: laagdikte en draagkracht."),
    "kade": ("22.20.00", "Kademuren en damwanden: toleranties en inspectie-eisen."),
}


# ------------------------------------------------------------ functions ----
def roi(km: int, fte: int, rate: int, license_cost: int = 6000) -> tuple[int, int, int]:
    hours = round(km * 1.5 + fte * 30)
    savings = hours * rate
    return hours, savings, round(savings / license_cost * 100)


def euro(value: int) -> str:
    return f"€ {value:,}".replace(",", ".") + ",-"


@st.cache_resource(show_spinner="YOLOv8 model laden...")
def load_model():
    try:
        from ultralytics import YOLO
        return YOLO("yolov8n.pt")  # swap for your trained road-damage weights
    except Exception:
        return None


def detect(file, model) -> list[dict]:
    if model is None or file.type.startswith("video"):
        return [{"label": "Rafeling", "conf": 0.964, "raw": "84.12.01"}]
    with tempfile.NamedTemporaryFile(suffix=Path(file.name).suffix) as tmp:
        tmp.write(file.getvalue())
        tmp.flush()
        result = model(tmp.name, verbose=False)[0]
    return [{"label": result.names[int(b.cls)], "conf": float(b.conf), "raw": "84.12.01"}
            for b in result.boxes]


def to_geojson(detections: list[dict], lat: float, lon: float) -> str:
    features = [{"type": "Feature",
                 "geometry": {"type": "Point", "coordinates": [lon, lat]},
                 "properties": d} for d in detections]
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=2)


# ---------------------------------------------------------------- views ----
def section_header():
    html("""
    <div class="nav">
      <div class="logo">AIA<span>Implement</span></div>
      <div class="badge">RAW · CROW · NEN</div>
    </div>
    <div class="hero">
      <h1>AI voor <em>Grond-, Weg- en Waterbouw</em></h1>
      <p>Inspecteer sneller, zoek normen in seconden en genereer bestekken automatisch.</p>
    </div>
    <div class="stats">
      <div class="stat"><b>10x</b><span>snellere inspectie</span></div>
      <div class="stat"><b>96%</b><span>detectienauwkeurigheid</span></div>
      <div class="stat"><b>&lt; 2 uur</b><span>reactietijd demo</span></div>
    </div>
    """)


def tab_platform():
    cards = "".join(
        f'<div class="card"><div class="ico">{i}</div><h3>{t}</h3><p>{d}</p></div>'
        for i, t, d in MODULES)
    html(f'<div class="grid">{cards}</div>')

    st.markdown("#### Probeer het live")
    demo = st.radio("Module", [m[1] for m in MODULES], horizontal=True, label_visibility="collapsed")

    with st.container(border=True):
        if demo == MODULES[0][1]:
            file = st.file_uploader("Upload dashcam- of drone-beeld", type=["jpg", "jpeg", "png", "mp4"])
            c1, c2 = st.columns(2)
            lat = c1.number_input("Breedtegraad", value=52.37, format="%.5f")
            lon = c2.number_input("Lengtegraad", value=4.90, format="%.5f")
            if file:
                model = load_model()
                if model is None:
                    st.info("Demo-modus: installeer `ultralytics` voor echte detectie.")
                with st.spinner("Analyse uitgevoerd..."):
                    found = detect(file, model)
                st.success(f"{len(found)} schadepunt(en) gedetecteerd")
                st.dataframe(found, use_container_width=True)
                st.download_button("📥 Download GIS-rapport", to_geojson(found, lat, lon),
                                   file_name="inspectie.geojson", mime="application/geo+json")

        elif demo == MODULES[1][1]:
            query = st.text_input("Stel een vraag over bestek of norm", placeholder="bijv. verdichting asfalt")
            if query:
                hits = [v for k, v in RAW_KB.items() if k in query.lower()]
                for art, text in hits:
                    st.metric("RAW-artikel", art)
                    st.write(text)
                if not hits:
                    st.warning("Geen match in de demo-kennisbank.")

        else:
            c1, c2, c3 = st.columns(3)
            length = c1.number_input("Lengte (m)", 1, 100_000, 500)
            width = c2.number_input("Breedte (m)", 1.0, 50.0, 6.5)
            thick = c3.number_input("Laagdikte (mm)", 20, 300, 50)
            area = length * width
            tonnes = area * thick / 1000 * 2.4  # asfalt ≈ 2,4 t/m³
            m1, m2 = st.columns(2)
            m1.metric("Oppervlakte", f"{area:,.0f} m²")
            m2.metric("Asfalt (RAW 84.12.01)", f"{tonnes:,.0f} ton")


def tab_roi():
    st.markdown("#### Bereken uw besparing")
    c1, c2, c3 = st.columns(3)
    km = c1.slider("Kilometers per jaar", 10, 1000, 150)
    fte = c2.slider("Werkvoorbereiders (FTE)", 1, 50, 5)
    rate = c3.number_input("Uurtarief (€)", 1, 500, 85)
    hours, savings, pct = roi(km, fte, rate)
    html(f"""
    <div class="stats">
      <div class="stat"><b>{hours}</b><span>uur bespaard per jaar</span></div>
      <div class="stat"><b>{euro(savings)}</b><span>financiële besparing</span></div>
      <div class="stat"><b>{pct}%</b><span>ROI op licentie</span></div>
    </div>
    """)


def tab_pricing():
    cards = ""
    for name, price, unit, hot, features in PLANS:
        items = "".join(f"<li>{f}</li>" for f in features)
        tag = '<div class="tag">Meest gekozen</div>' if hot else ""
        cards += (f'<div class="card{" hot" if hot else ""}">{tag}<h3>{name}</h3>'
                  f'<div class="price">{price}</div><div class="unit">{unit}</div><ul>{items}</ul></div>')
    html(f'<div class="grid">{cards}</div>')


def tab_contact():
    st.markdown("#### Demo aanvragen of direct bestellen")
    with st.form("contact", clear_on_submit=True):
        c1, c2 = st.columns(2)
        company = c1.text_input("Bedrijfsnaam *")
        person = c2.text_input("Contactpersoon *")
        email = st.text_input("Zakelijk e-mailadres *")
        interest = st.selectbox("Interesse in", [p[0] for p in PLANS] + ["Alleen een demo"])
        note = st.text_area("Toelichting / vraag")
        if st.form_submit_button("Aanvraag versturen"):
            if not (company and person and "@" in email):
                st.error("Vul alle verplichte velden correct in.")
            else:
                # TODO: send to e-mail / CRM / database (use st.secrets for credentials)
                st.success("Aanvraag ontvangen! We nemen binnen 2 uur contact op.")


# ----------------------------------------------------------------- main ----
section_header()
tabs = st.tabs(["🚀 Platform", "💰 ROI Calculator", "📦 Pakketten", "✉️ Contact"])
for tab, view in zip(tabs, [tab_platform, tab_roi, tab_pricing, tab_contact]):
    with tab:
        view()
html('<div class="footer">© 2026 AIAImplement · AI-platform voor de GWW-sector</div>')
