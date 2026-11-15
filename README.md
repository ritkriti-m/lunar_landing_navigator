# LUNAR NAV

Welcome to LUNAR NAV by team Mission M²RS, a group of four year 12 students. Created for the Lunar Landing Site Navigator challenge, this project is a professional Mission Control dashboard built to help mission planners, educators, and students evaluate lunar south pole landing sites for Artemis IV.

## Key Features

* An interactive south pole orbital map showing target landing locations such as Haworth Crater with precise latitude, longitude, and illumination percentages.
* A lunar day progression timeline slider spanning 0 to 29.5 Earth days.
* Live telemetry tracking cards computing solar and Earth elevation angles instantly from a persistent SQLite database.
* Dynamic Plotly ephemeris line charts visualising terrain horizons and elevation angles over elapsed lunar days, featuring full zoom, pan, and image export capabilities.

## Tools and Technologies

* Programming Languages: Python, HTML, and CSS
* Data and Backend: SQLite, pandas, and custom CSV data tables
* Visualisation and UI: Figma, Streamlit, Plotly, and PIL
* Development and Deployment: VS Code, Git version control, and Streamlit Community Cloud

## How to Run Locally

1. Clone this repository to your local machine.
2. Install the required Python packages using your terminal:
   ```bash
   pip install streamlit pandas plotly pillow
