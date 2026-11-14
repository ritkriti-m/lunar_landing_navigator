"""Streamlit edition of the Lunar Landing Site Navigator."""

from __future__ import annotations

import html
import os
import sqlite3
import pandas as pd
from PIL import Image
import plotly.express as px

import streamlit as st

# --- PAGE CONFIGURATION & THEME ---
st.set_page_config(
    page_title="Lunar/Nav · Python",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Manrope:wght@400;500;600;700&display=swap');
      :root { color-scheme: dark; }
      html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
      .stApp { background: #0b0e0e; color: #edf0e9; }
      .block-container { max-width: none; padding: 0 1.5rem 1.5rem; }
      [data-testid="stSidebar"] { width: 350px !important; background: #101313; border-right: 1px solid #2b3030; }
      [data-testid="stSidebar"] > div:first-child { padding: 0 1.35rem 1.2rem; }
      h1, h2, h3, p { color: #edf0e9; }
      .brandbar { height: 72px; display: flex; align-items: center; justify-content: space-between; margin: 0 -1.5rem 1.2rem; padding: 0 1.5rem; border-bottom: 1px solid #2b3030; background: #0a0c0c; }
      .brand { font: 500 17px 'DM Mono', monospace; letter-spacing: .06em; }
      .brand b { color: #dff86f; font-weight: 500; }
      .brand em { color: #68706f; font-style: normal; }
      .telemetry { color: #9da6a3; font: 500 9px 'DM Mono', monospace; letter-spacing: .14em; }
      .telemetry i { display: inline-block; width: 6px; height: 6px; margin-right: 8px; border-radius: 50%; background: #dff86f; box-shadow: 0 0 12px #dff86f; }
      .side-head { padding: 1.5rem 0 .65rem; }
      .kicker, .metric-label { color: #78817f; font: 500 9px 'DM Mono', monospace; letter-spacing: .15em; text-transform: uppercase; }
      .side-head h1 { margin: .45rem 0 0; font-size: 25px; font-weight: 500; }
      .site-card { margin: .85rem 0; padding: 1rem; border: 1px solid #39413f; background: linear-gradient(90deg, rgba(223,248,111,.07), #151919 60%); border-left: 2px solid #dff86f; }
      .site-card h3 { margin: 0 0 .35rem; font-size: 13px; font-weight: 600; }
      .site-card p { margin: 0; color: #747d7a; font: 8px 'DM Mono', monospace; }
      .detail { display: grid; grid-template-columns: minmax(230px, 1.5fr) repeat(4, minmax(90px, .5fr)); margin-top: .8rem; border: 1px solid #303634; background: #111515; }
      .detail > div { padding: 1rem; }
      .detail > div + div { border-left: 1px solid #303634; }
      .detail h2 { margin: .25rem 0; font-size: 18px; font-weight: 500; }
      .detail p { margin: 0; color: #7f8985; font-size: 9px; line-height: 1.5; }
      .detail strong { display: block; margin-top: .4rem; font: 500 15px 'DM Mono', monospace; }
      .detail .score { color: #dff86f; font-size: 22px; }
      .profile-head { display: flex; align-items: end; justify-content: space-between; padding: 1.5rem 0 1.2rem; border-bottom: 1px solid #303634; margin-bottom: 1.5rem; }
      .profile-head h1 { margin: .35rem 0 .25rem; font-size: clamp(28px, 4vw, 48px); font-weight: 500; letter-spacing: -.045em; }
      .profile-coords { color: #7d8783; font: 10px 'DM Mono', monospace; }
      .profile-score { text-align: right; }
      .profile-score strong { display: block; color: #dff86f; font: 400 44px 'DM Mono', monospace; }
      .profile-panel { border: 1px solid #303634; background: #111515; }
      .profile-panel > div { padding: 1.15rem; }
      .profile-panel > div + div { border-top: 1px solid #303634; }
      .profile-panel h3 { margin: .35rem 0 .45rem; font-size: 14px; font-weight: 600; }
      .profile-panel p { margin: 0; color: #8b9591; font-size: 11px; line-height: 1.65; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- DATABASE CONNECTION & LOGIC ---
@st.cache_data
def get_ephemeris_data():
    db_path = os.path.join('data', 'haworth.db')
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM ephemeris", conn)
    conn.close()
    return df

@st.cache_data
def get_topography_data():
    db_path = os.path.join('data', 'haworth.db')
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM topography", conn)
    conn.close()
    return df

def calculate_viability(sun_elev: float, earth_elev: float) -> tuple[int, str]:
    score = 100
    warnings = []

    if sun_elev <= 0:
        score -= 50
        warnings.append("CRITICAL: Loss of Solar Power")
    elif sun_elev < 2:
        score -= 10
        warnings.append("Warning: Low Solar Incidence")

    if earth_elev <= 5:
        score -= 40
        warnings.append("CRITICAL: Loss of Direct-to-Earth Comms")

    score = max(0, score)
    status_message = " | ".join(warnings) if warnings else "All Systems Nominal"
    return score, status_message


# --- DESIGNER SITE DATA + HAWORTH CRATER ---
SITES = {
    "Haworth Crater (HW10)": {
        "subtitle": "South Pole",
        "coords": "86.527° S  14.876° W",
        "elevation": "-4.1 km",
        "illumination": 34.86,
        "temperature": "-230°C",
        "score": 98,
        "accent": "#ff4b4b",
        "brief": "Deep permanently shadowed region containing high concentrations of volatile water ice, making it a prime Artemis III candidate despite extreme lighting constraints.",
        "terrain": "Steep crater walls leading down into a permanently shadowed floor.",
        "science": "Volatile water ice extraction, extreme thermal environment studies",
        "hazards": "Near-absolute zero temperatures, zero direct solar illumination in deep crater",
        "comms": "Requires lunar relay satellite due to lack of direct Earth line-of-sight from the floor",
        "window": "2026 Q3 · Artemis III Target",
    },
    "Shackleton Ridge": {
        "subtitle": "South Pole",
        "coords": "89.90° S  0.00° E",
        "elevation": "-1.3 km",
        "illumination": 82.0,
        "temperature": "-48°C",
        "score": 94,
        "accent": "#dff86f",
        "brief": "High-illumination ridge with direct line of sight to Earth and nearby permanently shadowed regions.",
        "terrain": "Narrow elevated ridge bordering the 21 km-wide Shackleton crater.",
        "science": "Volatile deposits, regolith maturity, solar wind exposure",
        "hazards": "Steep crater-facing slopes and persistent low-angle illumination",
        "comms": "Direct Earth visibility for approximately 82% of the local cycle",
        "window": "2030 Q3 · 6.2 Earth days",
    },
}

# --- ROUTING LOGIC ---
site_lookup = {name.lower().replace(" ", "-"): name for name in SITES}

raw_site_slug = st.query_params.get("site", "")
if isinstance(raw_site_slug, list) and len(raw_site_slug) > 0:
    raw_site_slug = raw_site_slug[0]

detail_name = site_lookup.get(raw_site_slug)
initial_name = detail_name or next(iter(SITES))

# --- PERSISTENT SIDEBAR WITH LUNAR NAV TITLE ---
with st.sidebar:
    st.markdown(
        """
        <div class="side-head">
          <span style="font: 500 13px 'DM Mono', monospace; color: #dff86f; letter-spacing: .08em;"><b>◐</b>&nbsp; LUNAR NAV</span>
          <h1 style="margin-top: 0.35rem;">Landing sites</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_name = st.selectbox("ACTIVE LANDING ZONE", list(SITES.keys()), index=list(SITES).index(initial_name))
    selected = SITES[selected_name]
    st.markdown(
        f"""
        <div class="site-card" style="border-left-color:{selected['accent']}">
          <h3>{html.escape(selected_name)}</h3>
          <p>{selected['subtitle']} · {selected['coords']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if st.button(f"View Full Profile: {html.escape(selected_name)}", use_container_width=True):
        slug = selected_name.lower().replace(" ", "-") 
        st.query_params["site"] = slug
        if "map_plot" in st.session_state:
            del st.session_state["map_plot"]
        st.rerun()

    st.caption("Select a site, then scrub the UTC timeline to visualize projected surface conditions.")

# --- TOP BRAND BAR ---
st.markdown(
    """
    <div class="brandbar">
      <span class="brand"><b>◐</b>&nbsp; LUNAR<em>/NAV</em></span>
      <span class="telemetry"><i></i>LIVE SIMULATION &nbsp;&nbsp; ARTEMIS III</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- DETAIL PROFILE PAGE ---
if detail_name:
    detail_site = SITES[detail_name]
    if st.button("← BACK TO MAP", type="primary"):
        st.query_params.clear()
        if "map_plot" in st.session_state:
            del st.session_state["map_plot"]
        st.rerun()
        
    st.markdown(
        f"""
        <header class="profile-head">
          <div>
            <span class="kicker">LUNAR LANDING ZONE · MISSION PROFILE</span>
            <h1>{html.escape(detail_name)}</h1>
            <span class="profile-coords">{detail_site['subtitle']} · {detail_site['coords']}</span>
          </div>
          <div class="profile-score">
            <span class="metric-label">SITE VIABILITY</span>
            <strong style="color: {detail_site['accent']}">{detail_site['score']}%</strong>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns([1.2, 2])
    
    with col1:
        st.markdown(
            f"""
            <div class="profile-panel">
              <div>
                <span class="metric-label">MISSION ASSESSMENT</span>
                <h3>Site overview</h3>
                <p>{detail_site['brief']}</p>
              </div>
              <div>
                <span class="metric-label">TERRAIN CHARACTER</span>
                <h3>Surface and approach</h3>
                <p>{detail_site['terrain']}</p>
              </div>
              <div>
                <span class="metric-label">PRIMARY SCIENCE TARGETS</span>
                <h3>Research opportunity</h3>
                <p>{detail_site['science']}</p>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; margin-top: 1rem; border-top: 1px solid #303634;">
                <div style="padding: 1rem; border-right: 1px solid #303634; border-bottom: 1px solid #303634;">
                  <span class="metric-label">ELEVATION</span>
                  <strong style="color:#edf0e9; font-size:14px; font-family:'DM Mono', monospace; display:block; margin-top:4px;">{detail_site['elevation']}</strong>
                </div>
                <div style="padding: 1rem; border-bottom: 1px solid #303634;">
                  <span class="metric-label">ILLUMINATION</span>
                  <strong style="color:#edf0e9; font-size:14px; font-family:'DM Mono', monospace; display:block; margin-top:4px;">{detail_site['illumination']}%</strong>
                </div>
                <div style="padding: 1rem; border-right: 1px solid #303634;">
                  <span class="metric-label">SURFACE TEMP.</span>
                  <strong style="color:#edf0e9; font-size:14px; font-family:'DM Mono', monospace; display:block; margin-top:4px;">{detail_site['temperature']}</strong>
                </div>
                <div style="padding: 1rem;">
                  <span class="metric-label">WINDOW</span>
                  <strong style="color:#edf0e9; font-size:14px; font-family:'DM Mono', monospace; display:block; margin-top:4px;">{detail_site['window'].split('·')[0]}</strong>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    with col2:
        st.markdown("<span class='metric-label' style='margin-bottom: 0.5rem; display: block;'>SUN, EARTH AND TERRAIN HORIZON AT HW10 OVER ONE LUNAR DAY</span>", unsafe_allow_html=True)
        df_ephem = get_ephemeris_data()
        
        if df_ephem is not None and not df_ephem.empty:
            df_ephem['timestamp'] = pd.to_datetime(df_ephem['timestamp'])
            
            plot_cols = ['sun_elevation', 'earth_elevation']
            color_seq = ['#2b8cbe', '#ff9800']
            if 'terrain_horizon_sun' in df_ephem.columns and 'terrain_horizon_earth' in df_ephem.columns:
                plot_cols = ['sun_elevation', 'earth_elevation', 'terrain_horizon_sun', 'terrain_horizon_earth']
                color_seq = ['#2b8cbe', '#ff9800', '#2ca02c', '#d62728']

            fig_line = px.line(
                df_ephem, 
                x='timestamp', 
                y=plot_cols,
                labels={'value': 'Elevation angle (degrees)', 'timestamp': 'Time (UTC)', 'variable': 'Parameter'},
                color_discrete_sequence=color_seq
            )
            
            fig_line.add_hline(y=0, line_dash="dashdot", line_color="#9da6a3", annotation_text="Local horizontal", annotation_position="bottom right")
            
            fig_line.update_layout(
                template="plotly_dark",
                paper_bgcolor="#111515", 
                plot_bgcolor="#111515",
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="v", yanchor="top", y=0.98, xanchor="right", x=0.98, title=""),
                height=480,
                xaxis=dict(title="Time (UTC)", gridcolor="#303635", zeroline=False),
                yaxis=dict(title="Elevation angle (degrees)", gridcolor="#303635", zeroline=False)
            )
            st.plotly_chart(fig_line, use_container_width=True)

    st.stop()


# --- MAP EXPLORATION PAGE ---
solar_time = st.slider(
    "SHADOW SIMULATION · UTC",
    min_value=0.0,
    max_value=24.0,
    value=14.5,
    step=0.25,
    format="%0.2f",
)

df_ephem = get_ephemeris_data()
dynamic_sun_elev = "--"
dynamic_earth_elev = "--"
dynamic_score = selected['score']
status_warning = selected['brief']
display_time = f"{int(solar_time):02d}:{round((solar_time % 1) * 60):02d} UTC"

if selected_name == "Haworth Crater (HW10)" and df_ephem is not None and not df_ephem.empty:
    row_idx = int((solar_time / 24) * (len(df_ephem) - 1))
    db_row = df_ephem.iloc[row_idx]
    
    sun_val = float(db_row['sun_elevation'])
    earth_val = float(db_row['earth_elevation'])
    
    dynamic_sun_elev = f"{sun_val:.2f}°"
    dynamic_earth_elev = f"{earth_val:.2f}°"
    display_time = str(db_row['timestamp'])
    
    dynamic_score, status_warning = calculate_viability(sun_val, earth_val)

time_col, azimuth_col, illumination_col = st.columns([1, 1, 1])
time_col.metric("SIMULATION TIME", display_time)
azimuth_col.metric("SOLAR ELEV (SQLITE)", dynamic_sun_elev)
illumination_col.metric("EARTH ELEV (SQLITE)", dynamic_earth_elev)

df_topo = get_topography_data()

if df_topo is not None and not df_topo.empty:
    st.markdown("### 🗺️ Target Landing Zones")
    
    fig = px.scatter(
        df_topo,
        x='longitude',
        y='latitude',
        hover_name='site',
        custom_data=['illumination'], 
        color_discrete_sequence=['#dff86f'], 
    )
    
    fig.update_traces(
        marker=dict(size=12, opacity=0.9, line=dict(width=1, color='#111515')),
        hovertemplate="<b>%{hovertext}</b><br>Longitude: %{x}°<br>Latitude: %{y}°<br>Sunlight: %{customdata[0]}%<extra></extra>"
    )
    
    layout_args = dict(
        template="plotly_dark",
        margin=dict(l=10, r=10, b=10, t=10),
        paper_bgcolor="#171b1b",
        plot_bgcolor="#171b1b",
        xaxis=dict(title="Longitude", gridcolor="#303635", zeroline=False),
        yaxis=dict(title="Latitude", gridcolor="#303635", zeroline=False), 
        hovermode="closest",
        dragmode="pan",
        height=550 
    )
    
    img_path = os.path.join("assets", "haworth_map.png")
    if os.path.exists(img_path):
        img = Image.open(img_path)
        fig.add_layout_image(dict(source=img, xref="x", yref="y", x=-33.0, y=-86.4, sizex=21.0, sizey=0.8, sizing="stretch", opacity=0.7, layer="below"))
    
    fig.update_layout(**layout_args)
    
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points", key="map_plot")
    
    points = []
    if isinstance(event, dict) and "selection" in event:
        points = event["selection"].get("points", [])
    elif hasattr(event, "selection") and hasattr(event.selection, "points"):
        points = event.selection.points

    if len(points) > 0:
        point_data = points[0]
        point_idx = point_data.get("point_index") if isinstance(point_data, dict) else getattr(point_data, "point_index", -1)
        
        if point_idx is not None and 0 <= point_idx < len(df_topo):
            clicked_site_id = df_topo.iloc[point_idx]['site'] 
            
            target_key = None
            for key in SITES.keys():
                if clicked_site_id in key:
                    target_key = key
                    break
            
            if target_key:
                slug = target_key.lower().replace(" ", "-")
                if st.query_params.get("site") != slug:
                    st.query_params["site"] = slug
                    if "map_plot" in st.session_state:
                        del st.session_state["map_plot"]
                    st.rerun()

st.markdown(
    f"""
    <section class="detail">
      <div>
        <span class="metric-label">SELECTED LANDING ZONE</span>
        <h2>{html.escape(selected_name)}</h2>
        <p>{status_warning}</p>
      </div>
      <div><span class="metric-label">VIABILITY</span>
        <strong class="score" style="color: {selected['accent']}">{dynamic_score}%</strong></div>
      <div><span class="metric-label">ELEVATION</span>
        <strong>{selected['elevation']}</strong></div>
      <div><span class="metric-label">ILLUMINATION</span>
        <strong>{selected['illumination']}%</strong></div>
      <div><span class="metric-label">SURFACE TEMP.</span>
        <strong>{selected['temperature']}</strong></div>
    </section>
    """,
    unsafe_allow_html=True,
)