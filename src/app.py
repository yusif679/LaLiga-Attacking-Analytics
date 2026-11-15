
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

# 1. Find our project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# 2. Configure the dashboard
st.set_page_config(
    page_title="La Liga Attacking Analytics",
    page_icon="⚽",
    layout="wide"
)

# 3. Load the datasets
players = pd.read_csv(DATA_DIR / "players.csv")
shots = pd.read_csv(DATA_DIR / "shots.csv")

# 4. Display the dashboard title
st.title("⚽ La Liga Attacking Analytics")

st.write(
    "Explore attacking player performance during "
    "the 2015–16 La Liga season."
)

# 5. Display basic dataset statistics
st.subheader("Dataset Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Players", len(players))

with col2:
    st.metric("Total Shots", len(shots))

with col3:
    st.metric("Total Goals", players["goals"].sum())


# 6. Prepare attacking player data
forwards = players[
    players["position"].str.contains("F")
].copy()

# Keep forwards with at least 900 minutes
forwards = forwards[forwards["time"] >= 900].copy()

# Calculate goals per 90 minutes
forwards["goals_per_90"] = (
    forwards["goals"] / forwards["time"] * 90
)

# 7. Select the top 10 forwards
top_10 = forwards.nlargest(10, "goals_per_90")

# 8. Create the Plotly chart
st.subheader("Top 10 Forwards by Goals per 90")

fig = px.bar(
    top_10,
    x="goals_per_90",
    y="player_name",
    orientation="h",
    labels={
        "goals_per_90": "Goals per 90 Minutes",
        "player_name": "Player"
    },
    hover_data=["team_title", "goals", "time"]
)

fig.update_traces(
    texttemplate="%{x:.2f}",
    textposition="outside"
)

fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=550
)

# 9. Display the chart inside Streamlit
st.plotly_chart(fig, use_container_width=True)
