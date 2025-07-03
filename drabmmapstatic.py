import streamlit as st
from maplibre import Map, MapOptions
from maplibre.basemaps import Carto
from maplibre.controls import NavigationControl
from maplibre.streamlit import st_maplibre
import pandas as pd

# Load CSV data
csv_url = "https://raw.githubusercontent.com/musamibrahim/DRABMTestMap/refs/heads/main/DailyAverageBuoyData.csv"
df = pd.read_csv(csv_url)

# Ensure column names are stripped of whitespace
df.columns = df.columns.str.strip()

# Date filter
if "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"])
    min_Date, max_Date = df["Date"].min(), df["Date"].max()
    selected_Date = st.date_input("Select Date", min_value=min_Date.date(), max_value=max_Date.date(), value=min_Date.date())
    df = df[df["Date"].dt.date == selected_Date]

# Appr_depth filter: only offer 0, 1, 4, and 7
if "Appr_depth" in df.columns:
    appr_depth_options = [0, 1, 4, 7]
    available_options = [v for v in appr_depth_options if v in df["Appr_depth"].unique()]
    available_options = ["All"] + available_options  # Add "All" option
    selected_Appr_depth = st.selectbox("Select Appr_depth", available_options, index=0)
    if selected_Appr_depth != "All":
        df = df[df["Appr_depth"] == selected_Appr_depth]

def create_layer(cell_size: int = 200) -> dict:
    # Convert Timestamp columns to string for JSON serialization
    df_serializable = df.copy()
    for col in df_serializable.select_dtypes(include=["datetime64[ns]"]).columns:
        df_serializable[col] = df_serializable[col].astype(str)
    return {
        "@@type": "GridLayer",
        "id": "GridLayer",
        "data": df_serializable.to_dict(orient="records"),
        "extruded": True,
        "getPosition": "@@=[Longitude, Latitude]",
        "getColorWeight": "@@=Temp",
        "getElevationWeight": "@@=Appr_depth",
        "elevationScale": 4,
        "cellSize": cell_size,
        "pickable": True,
    }

# Add getPosition property for Deck.gl
if "Longitude" in df.columns and "Latitude" in df.columns:
    data = df.copy()
    data["getPosition"] = data[["Longitude", "Latitude"]].values.tolist()
    data = data.to_dict(orient="records")
else:
    data = []
    data["getPosition"] = data[["Longitude", "Latitude"]].values.tolist()
    data = data.to_dict(orient="records")

map_options = MapOptions(
    style=Carto.POSITRON,
    center=(-95.3678, 38.9219),
    zoom=12,
    hash=True,
    pitch=40,
)
# Calculate average temperature for tooltip
if "Temp" in df.columns and not df.empty:
    avg_temp = df["Temp"].mean()
    tooltip_text = f"Average Temp: {avg_temp:.2f}°C"
else:
    tooltip_text = "No data for selected filters"

st.title("Clinton Lake Data Visualization")

cell_size = st.slider("cell size", 100, 600, value=200, step=5)

m = Map(map_options)
m.add_control(NavigationControl())
m.add_deck_layers([create_layer(cell_size)], tooltip=tooltip_text)

st_maplibre(m)