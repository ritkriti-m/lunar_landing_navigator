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
      [data-testid="stHeader"] { background: transparent !important; }
      [data-testid="stToolbar"] { right: 2rem; }
      .block-container { max-width: none; padding: 0 1.5rem 1.5rem; }
      [data-testid="stSidebar"] { width: 350px !important; background: #101313; border-right: 1px solid #2b3030; }
      [data-testid="stSidebar"] > div:first-child { padding: 0 1.35rem 1.2rem; }
      h1, h2, h3, p { color: #edf0e9 !important; }
      .stButton > button {
          background-color: #151919 !important;
          color: #dff86f !important;
          border: 1px solid #39413f !important;
          font-family: 'DM Mono', monospace !important;
          font-weight: 500;
          transition: all 0.2s ease;
      }
      .stButton > button:hover {
          border-color: #dff86f !important;
          background-color: rgba(223,248,111,0.1) !important;
      }
      .brandbar { height: 72px; display: flex; align-items: center; justify-content: space-between; margin: 0 -1.5rem 1.2rem; padding: 0 1.5rem; border-bottom: 1px solid #2b3030; background: #0a0c0c; }
      .brand { font: 500 17px 'DM Mono', monospace; letter-spacing: .06em; color: #edf0e9; }
      .brand b { color: #dff86f; font-weight: 500; }
      .brand em { color: #68706f; font-style: normal; }
      .telemetry { color: #9da6a3; font: 500 9px 'DM Mono', monospace; letter-spacing: .14em; }
      .telemetry i { display: inline-block; width: 6px; height: 6px; margin-right: 8px; border-radius: 50%; background: #dff86f; box-shadow: 0 0 12px #dff86f; }
      .side-head { padding: 1.5rem 0 .65rem; }
      .kicker, .metric-label { color: #78817f; font: 500 9px 'DM Mono', monospace; letter-spacing: .15em; text-transform: uppercase; }
      .side-head h1 { margin: .45rem 0 0; font-size: 25px; font-weight: 500; color: #edf0e9 !important; }
      .site-card { margin: .85rem 0; padding: 1rem; border: 1px solid #39413f; background: linear-gradient(90deg, rgba(223,248,111,.07), #151919 60%); border-left: 2px solid #dff86f; }
      .site-card h3 { margin: 0 0 .35rem; font-size: 13px; font-weight: 600; color: #edf0e9 !important; }
      .site-card p { margin: 0; color: #9da6a3; font: 8px 'DM Mono', monospace; }
      .detail { display: grid; grid-template-columns: minmax(280px, 2fr) repeat(2, minmax(140px, 1fr)); margin-top: .8rem; border: 1px solid #303634; background: #111515; }
      .detail > div { padding: 1rem; }
      .detail > div + div { border-left: 1px solid #303634; }
      .detail h2 { margin: .25rem 0; font-size: 18px; font-weight: 500; color: #edf0e9 !important; }
      .detail p { margin: 0; color: #9da6a3; font-size: 9px; line-height: 1.5; }
      .detail strong { display: block; margin-top: .4rem; font: 500 15px 'DM Mono', monospace; color: #edf0e9; }
      .profile-head { display: flex; align-items: end; justify-content: space-between; padding: 1.5rem 0 1.2rem; border-bottom: 1px solid #303634; margin-bottom: 1.5rem; }
      .profile-head h1 { margin: .35rem 0 .25rem; font-size: clamp(28px, 4vw, 48px); font-weight: 500; letter-spacing: -.045em; color: #edf0e9 !important; }
      .profile-coords { color: #9da6a3; font: 10px 'DM Mono', monospace; }
      .profile-panel { border: 1px solid #303634; background: #111515; }
      .profile-panel > div { padding: 1.15rem; }
      .profile-panel > div + div { border-top: 1px solid #303634; }
      .profile-panel h3 { margin: .35rem 0 .45rem; font-size: 14px; font-weight: 600; color: #edf0e9 !important; }
      .profile-panel p { margin: 0; color: #a3ad9d; font-size: 11px; line-height: 1.65; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- DATABASE CONNECTION & AUTO-BUILD LOGIC ---
def initialize_database():
    db_path = os.path.join('data', 'haworth.db')
    if os.path.exists(db_path):
        return
    
    os.makedirs('data', exist_ok=True)
    sun_path = os.path.join('data', 'HW10_sunlight_visibility.csv')
    earth_path = os.path.join('data', 'HW10_earth_visibility.csv')
    
    if os.path.exists(sun_path) and os.path.exists(earth_path):
        sun_df = pd.read_csv(sun_path)
        earth_df = pd.read_csv(earth_path)
        merged_ephem = pd.merge(
            sun_df[['UTC', 'Solar elevation (degrees)', 'Terrain horizon (degrees)']].rename(columns={
                'UTC': 'timestamp',
                'Solar elevation (degrees)': 'sun_elevation',
                'Terrain horizon (degrees)': 'terrain_horizon_sun'
            }),
            earth_df[['UTC', 'Earth elevation (degrees)', 'Terrain horizon (degrees)']].rename(columns={
                'UTC': 'timestamp',
                'Earth elevation (degrees)': 'earth_elevation',
                'Terrain horizon (degrees)': 'terrain_horizon_earth'
            }),
            on='timestamp'
        )
    else:
        merged_ephem = pd.DataFrame(columns=['timestamp', 'sun_elevation', 'terrain_horizon_sun', 'earth_elevation', 'terrain_horizon_earth'])

    # Add relative lunar day index (0.0 to ~29.5 Earth days across rows)
    total_rows = len(merged_ephem)
    if total_rows > 0:
        merged_ephem['lunar_day'] = [round((i / max(1, total_rows - 1)) * 29.53, 2) for i in range(total_rows)]
    else:
        merged_ephem['lunar_day'] = []

    topo_data = [
        {"site": "HW01", "latitude": -86.768, "longitude": -20.514, "elevation": 990.0, "illumination": 42.10},
        {"site": "HW02", "latitude": -86.808, "longitude": -21.719, "elevation": 990.0, "illumination": 38.50},
        {"site": "HW03", "latitude": -86.860, "longitude": -19.893, "elevation": 990.0, "illumination": 41.20},
        {"site": "HW04", "latitude": -86.568, "longitude": -21.473, "elevation": 990.0, "illumination": 39.00},
        {"site": "HW05", "latitude": -86.662, "longitude": -30.548, "elevation": 990.0, "illumination": 45.30},
        {"site": "HW06", "latitude": -87.050, "longitude": -24.240, "elevation": 990.0, "illumination": 37.80},
        {"site": "HW07", "latitude": -86.932, "longitude": -23.020, "elevation": 990.0, "illumination": 40.40},
        {"site": "HW08", "latitude": -86.924, "longitude": -25.809, "elevation": 990.0, "illumination": 36.90},
        {"site": "HW09", "latitude": -86.623, "longitude": -26.075, "elevation": 990.0, "illumination": 43.70},
        {"site": "HW10", "latitude": -86.527, "longitude": -14.876, "elevation": 990.0, "illumination": 34.86},
        {"site": "HW_K2023", "latitude": -86.990, "longitude": -24.254, "elevation": 990.0, "illumination": 44.20}
    ]
    topo_df = pd.DataFrame(topo_data)

    conn = sqlite3.connect(db_path)
    merged_ephem.to_sql('ephemeris', conn, if_exists='replace', index=False)
    topo_df.to_sql('topography', conn, if_exists='replace', index=False)
    conn.close()

@st.cache_data
def get_ephemeris_data():
    initialize_database()
    db_path = os.path.join('data', 'haworth.db')
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM ephemeris", conn)
    conn.close()
    return df

@st.cache_data
def get_topography_data():
    initialize_database()
    db_path = os.path.join('data', 'haworth.db')
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM topography", conn)
    conn.close()
    return df


# --- SITE DATA ---
SITES = {
    "Haworth Crater (HW10)": {
        "subtitle": "South Pole",
        "coords": "86.527° S  14.876° W",
        "elevation": "990.0 m",
        "illumination": 34.86,
        "accent": "#ff4b4b",
        "brief": "Deep permanently shadowed region containing high concentrations of volatile water ice, making it a prime Artemis III candidate despite extreme lighting constraints.",
        "terrain": "Steep crater walls leading down into a permanently shadowed floor.",
        "science": "Volatile water ice extraction, extreme thermal environment studies",
        "hazards": "Near-absolute zero temperatures, zero direct solar illumination in deep crater",
        "comms": "Requires lunar relay satellite due to lack of direct Earth line-of-sight from the floor",
    },
    "Shackleton Ridge": {
        "subtitle": "South Pole",
        "coords": "89.90° S  0.00° E",
        "elevation": "990.0 m",
        "illumination": 82.0,
        "accent": "#dff86f",
        "brief": "High-illumination ridge with direct line of sight to Earth and nearby permanently shadowed regions.",
        "terrain": "Narrow elevated ridge bordering the 21 km-wide Shackleton crater.",
        "science": "Volatile deposits, regolith maturity, solar wind exposure",
        "hazards": "Steep crater-facing slopes and persistent low-angle illumination",
        "comms": "Direct Earth visibility for approximately 82% of the local cycle",
    },
}

# --- ROUTING LOGIC ---
site_lookup = {name.lower().replace(" ", "-"): name for name in SITES}
raw_site_slug = st.query_params.get("site", "")
if isinstance(raw_site_slug, list) and len(raw_site_slug) > 0:
    raw_site_slug = raw_site_slug[0]

detail_name = site_lookup.get(raw_site_slug)
initial_name = detail_name or next(iter(SITES))

# --- PERSISTENT SIDEBAR ---
with st.sidebar:
    st.markdown(
        """
        <div class="side-head">
          <span style="font: 500 13px 'DM Mono', monospace; color: #dff86f; letter-spacing: .08em;"><b>◐</b>&nbsp; LUNAR NAV</span>
          <h1 style="margin-top: 0.35rem;">Landing locations</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_name = st.selectbox("ACTIVE LANDING LOCATION", list(SITES.keys()), index=list(SITES).index(initial_name))
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

    st.caption("Select a location, then scrub the timeline to visualize projected ephemeris data across the lunar cycle.")

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
                <div style="padding: 1rem; border-right: 1px solid #303634;">
                  <span class="metric-label">ELEVATION</span>
                  <strong style="color:#edf0e9; font-size:14px; font-family:'DM Mono', monospace; display:block; margin-top:4px;">{detail_site['elevation']}</strong>
                </div>
                <div style="padding: 1rem;">
                  <span class="metric-label">ILLUMINATION</span>
                  <strong style="color:#edf0e9; font-size:14px; font-family:'DM Mono', monospace; display:block; margin-top:4px;">{detail_site['illumination']}%</strong>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    with col2:
        st.markdown("<span class='metric-label' style='margin-bottom: 0.5rem; display: block;'>SUN, EARTH AND TERRAIN HORIZON OVER ELAPSED LUNAR DAYS</span>", unsafe_allow_html=True)
        df_ephem = get_ephemeris_data()
        if df_ephem is not None and not df_ephem.empty:
            plot_x_col = 'lunar_day' if 'lunar_day' in df_ephem.columns else 'timestamp'
            plot_cols = ['sun_elevation', 'earth_elevation']
            color_seq = ['#2b8cbe', '#ff9800']
            if 'terrain_horizon_sun' in df_ephem.columns and 'terrain_horizon_earth' in df_ephem.columns:
                plot_cols = ['sun_elevation', 'earth_elevation', 'terrain_horizon_sun', 'terrain_horizon_earth']
                color_seq = ['#2b8cbe', '#ff9800', '#2ca02c', '#d62728']

            fig_line = px.line(
                df_ephem, x=plot_x_col, y=plot_cols,
                labels={'value': 'Elevation angle (degrees)', plot_x_col: 'Elapsed Lunar Day (Earth Days)', 'variable': 'Parameter'},
                color_discrete_sequence=color_seq
            )
            fig_line.add_hline(y=0, line_dash="dashdot", line_color="#9da6a3", annotation_text="Local horizontal", annotation_position="bottom right")
            fig_line.update_layout(
                template="plotly_dark", paper_bgcolor="#111515", plot_bgcolor="#111515",
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="v", yanchor="top", y=0.98, xanchor="right", x=0.98, title=""),
                height=480,
                xaxis=dict(title="Elapsed Lunar Day (Earth Days)", gridcolor="#303635", zeroline=False),
                yaxis=dict(title="Elevation angle (degrees)", gridcolor="#303635", zeroline=False)
            )
            st.plotly_chart(fig_line, use_container_width=True)
    st.stop()


# --- MAP EXPLORATION PAGE ---
solar_time = st.slider(
    "LUNAR DAY PROGRESSION (EARTH DAYS)",
    min_value=0.0, max_value=29.5, value=7.25, step=0.25, format="Day %0.2f",
)

df_ephem = get_ephemeris_data()
dynamic_sun_elev = "--"
dynamic_earth_elev = "--"
display_time = f"Day {solar_time:.2f} of Lunar Cycle"
row_idx = 0

if df_ephem is not None and not df_ephem.empty:
    row_idx = int((solar_time / 29.5) * (len(df_ephem) - 1))
    row_idx = max(0, min(row_idx, len(df_ephem) - 1))
    db_row = df_ephem.iloc[row_idx]
    sun_val = float(db_row['sun_elevation'])
    earth_val = float(db_row['earth_elevation'])
    dynamic_sun_elev = f"{sun_val:.2f}°"
    dynamic_earth_elev = f"{earth_val:.2f}°"
    if 'lunar_day' in db_row:
        display_time = f"Lunar Day {float(db_row['lunar_day']):.2f}"

# --- RESPONSIVE TELEMETRY CARDS ---
st.markdown(
    f"""
    <div style="display: grid; grid-template-columns: 1.5fr 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
      <div style="background: #111515; border: 1px solid #303634; padding: 0.85rem 1rem;">
        <span class="metric-label">SIMULATION PROGRESS</span>
        <div style="font-family: 'DM Mono', monospace; font-size: clamp(14px, 1.4vw, 20px); font-weight: 500; color: #edf0e9; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{display_time}</div>
      </div>
      <div style="background: #111515; border: 1px solid #303634; padding: 0.85rem 1rem;">
        <span class="metric-label">SOLAR ELEV (SQLITE)</span>
        <div style="font-family: 'DM Mono', monospace; font-size: clamp(14px, 1.4vw, 20px); font-weight: 500; color: #dff86f; margin-top: 4px;">{dynamic_sun_elev}</div>
      </div>
      <div style="background: #111515; border: 1px solid #303634; padding: 0.85rem 1rem;">
        <span class="metric-label">EARTH ELEV (SQLITE)</span>
        <div style="font-family: 'DM Mono', monospace; font-size: clamp(14px, 1.4vw, 20px); font-weight: 500; color: #a7e7ff; margin-top: 4px;">{dynamic_earth_elev}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

df_topo = get_topography_data()

if df_topo is not None and not df_topo.empty:
    st.markdown("### 🗺️ Target Landing Locations")
    
    fig = px.scatter(
        df_topo,
        x='longitude', y='latitude',
        hover_name='site',
        color_discrete_sequence=['#dff86f'],
        custom_data=['illumination'], 
    )
    
    fig.update_traces(
        marker=dict(size=14, opacity=0.9, line=dict(width=1, color='#111515')),
        hovertemplate="<b>%{hovertext}</b><br>Longitude: %{x}°<br>Latitude: %{y}°<br>Illumination: %{customdata[0]:.1f}%<extra></extra>"
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
        height=550,
    )
    
    img_path = os.path.join("assets", "haworth_map.png")
    if os.path.exists(img_path):
        img = Image.open(img_path)
        fig.add_layout_image(dict(
            source=img, xref="x", yref="y", x=-33.0, y=-86.4, sizex=21.0, sizey=0.8, 
            sizing="stretch", opacity=0.85, layer="below"
        ))
    
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
            target_key = next((key for key in SITES.keys() if clicked_site_id in key), None)
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
        <span class="metric-label">SELECTED LANDING LOCATION</span>
        <h2>{html.escape(selected_name)}</h2>
        <p>{selected['brief']}</p>
      </div>
      <div><span class="metric-label">ELEVATION</span>
        <strong>{selected['elevation']}</strong></div>
      <div><span class="metric-label">ILLUMINATION</span>
        <strong>{selected['illumination']}%</strong></div>
    </section>
    """,
    unsafe_allow_html=True,
)