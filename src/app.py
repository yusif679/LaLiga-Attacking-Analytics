
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

# Create a list of available teams
teams = sorted(forwards["team_title"].unique())

# Add "All Teams" as the first option
team_options = ["All Teams"] + teams

# Create the team selection dropdown
selected_team = st.selectbox(
    "Select a team",
    options=team_options
)

# Filter players if a specific team is selected
if selected_team != "All Teams":
    forwards = forwards[
        forwards["team_title"] == selected_team
    ].copy()



# Allow users to choose the minimum playing time
min_minutes = st.slider(
    "Minimum minutes played",
    min_value=0,
    max_value=3000,
    value=900,
    step=100
)

# Filter forwards based on the selected value
forwards = forwards[
    (forwards["time"] >= min_minutes) &
    (forwards["time"] > 0)
].copy()


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


# 10. Goals vs Expected Goals scatter plot
st.subheader("Goals vs Expected Goals (xG)")

scatter_fig = px.scatter(
    forwards,
    x="xG",
    y="goals",
    color="team_title",
    size="shots",
    hover_name="player_name",
    hover_data={
        "team_title": True,
        "goals": True,
        "xG": ":.2f",
        "shots": True,
        "assists": True,
        "time": True,
        "goals_per_90": ":.2f"},
    labels={
        "xG": "Expected Goals (xG)",
        "goals": "Actual Goals",
        "team_title": "Team",
        "shots": "Shots"
    },
    title="Attacking Finishing Performance"
)

# Draw a reference line where actual goals equal xG
max_value = max(
    forwards["xG"].max(),
    forwards["goals"].max(),
    1
)

scatter_fig.add_shape(
    type="line",
    x0=0,
    y0=0,
    x1=max_value,
    y1=max_value,
    line=dict(color="gray", dash="dash")
)

scatter_fig.update_layout(
    height=600,
    xaxis_range=[0, max_value + 2],
    yaxis_range=[0, max_value + 2]
)

st.plotly_chart(scatter_fig, use_container_width=True)


st.info(
    "Analytical insight: This chart helps identify players "
    "who scored more or fewer goals than expected based on "
    "the quality of their shooting opportunities. "
    "Performance above xG may indicate strong finishing, "
    "although it can also reflect short-term variation."
)


st.caption(
    "Each bubble represents a player. "
    "Bubble size indicates the number of shots. "
    "Players above the dashed line scored more goals than expected, "
    "while players below it scored fewer."
)
