
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

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


# 11. Interactive Player Shot Map
st.subheader("Interactive Player Shot Map")

st.caption(
    "Explore where players attempted their shots during "
    "the 2015–16 La Liga season."
)

# Get all unique player names from the shots dataset
shot_players = sorted(shots["player"].dropna().unique())

# Create an interactive player selector
selected_player = st.selectbox(
    "Select a player",
    options=shot_players,
    index=shot_players.index("Lionel Messi")
    if "Lionel Messi" in shot_players else 0
)

# Filter the shots dataset for the selected player
player_shots = shots[
    shots["player"] == selected_player
].copy()


# Display shooting statistics for the selected player
shot_col1, shot_col2, shot_col3 = st.columns(3)

with shot_col1:
    st.metric(
        "Total Shots",
        len(player_shots)
    )

with shot_col2:
    st.metric(
        "Goals Scored",
        (player_shots["result"] == "Goal").sum()
    )

with shot_col3:
    st.metric(
        "Expected Goals (xG)",
        round(player_shots["xG"].sum(), 2)
    )




# 12. Interactive football shot map

import math
import plotly.graph_objects as go

# Convert Understat coordinates into pitch metres
# Flip the X coordinates so the attacking goal is on the left
player_shots["pitch_x"] = (1 - player_shots["X"]) * 105
player_shots["pitch_y"] = player_shots["Y"] * 68

# Separate goals and other shots
goals = player_shots[player_shots["result"] == "Goal"]
other_shots = player_shots[player_shots["result"] != "Goal"]

# Create the figure
shot_fig = go.Figure()

# Pitch boundaries
shot_fig.add_shape(
    type="rect",
    x0=0, y0=0, x1=52.5, y1=68,
    line=dict(color="white", width=2),
    fillcolor="#176b3a",
    layer="below"
)

# Penalty area
shot_fig.add_shape(
    type="rect",
    x0=0, y0=13.84,
    x1=16.5, y1=54.16,
    line=dict(color="white", width=2)
)

# Six-yard box
shot_fig.add_shape(
    type="rect",
    x0=0, y0=24.84,
    x1=5.5, y1=43.16,
    line=dict(color="white", width=2)
)

# Goal
shot_fig.add_shape(
    type="rect",
    x0=-2, y0=30.34,
    x1=0, y1=37.66,
    line=dict(color="white", width=2)
)

# Penalty spot
shot_fig.add_trace(
    go.Scatter(
        x=[11],
        y=[34],
        mode="markers",
        marker=dict(color="white", size=5),
        showlegend=False,
        hoverinfo="skip"
    )
)

# Penalty arc
arc_x = []
arc_y = []

for i in range(101):
    angle = (
        -math.acos(5.5 / 9.15)
        + i * (2 * math.acos(5.5 / 9.15) / 100)
    )

    arc_x.append(11 + 9.15 * math.cos(angle))
    arc_y.append(34 + 9.15 * math.sin(angle))

shot_fig.add_trace(
    go.Scatter(
        x=arc_x,
        y=arc_y,
        mode="lines",
        line=dict(color="white", width=2),
        showlegend=False,
        hoverinfo="skip"
    )
)

# Non-goal shots
shot_fig.add_trace(
    go.Scatter(
        x=other_shots["pitch_x"],
        y=other_shots["pitch_y"],
        mode="markers",
        name="Other Shots",
        marker=dict(
            size=other_shots["xG"] * 18 + 7,
            color="#ffa726",
            opacity=0.6
        ),
        customdata=other_shots[["result", "xG", "minute"]],
        hovertemplate=(
            "Result: %{customdata[0]}"
            "<br>xG: %{customdata[1]:.2f}"
            "<br>Minute: %{customdata[2]}"
            "<extra></extra>"
        )
    )
)

# Goals
shot_fig.add_trace(
    go.Scatter(
        x=goals["pitch_x"],
        y=goals["pitch_y"],
        mode="markers",
        name="Goals",
        marker=dict(
            size=goals["xG"] * 18 + 7,
            color="#44ff66",
            opacity=0.9,
            line=dict(color="white", width=1)
        ),
        customdata=goals[["xG", "minute"]],
        hovertemplate=(
            "GOAL!"
            "<br>xG: %{customdata[0]:.2f}"
            "<br>Minute: %{customdata[1]}"
            "<extra></extra>"
        )
    )
)

# Configure chart appearance
shot_fig.update_layout(
    height=750,
    plot_bgcolor="#176b3a",
    paper_bgcolor="rgba(0,0,0,0)",

    xaxis=dict(
        range=[-3, 55],
        visible=False,
        fixedrange=False
    ),
    yaxis=dict(
        range=[-2, 70],
        visible=False,
        fixedrange=False
    ),
    dragmode="zoom",
    margin=dict(l=10, r=10, t=10, b=45),
    legend=dict(
        orientation="h",
        x=0.5,
        xanchor="center",
        y=-0.05
    )
)

# Display the shot map in a centered column
left_space, pitch_column, right_space = st.columns([1, 3, 1])

with pitch_column:
    st.plotly_chart(shot_fig, width="stretch")



# 14. Attacking statistics correlation heatmap

st.subheader("How Are Attacking Statistics Connected?")

st.write(
    "This chart explores whether players who perform well "
    "in one attacking statistic also tend to perform well "
    "in another."
)

# Use clear names for the statistics
stat_names = {
    "goals": "Goals",
    "xG": "Expected Goals",
    "assists": "Assists",
    "xA": "Expected Assists",
    "shots": "Shots",
    "key_passes": "Key Passes"
}

# Include players with at least 900 minutes played
correlation_players = players[
    players["time"] >= 900
].copy()

# Calculate correlations between attacking statistics
correlation_matrix = correlation_players[
    list(stat_names.keys())
].corr()

# Rename the rows and columns
correlation_matrix = correlation_matrix.rename(
    index=stat_names,
    columns=stat_names
)

# Create the heatmap
heatmap_fig = px.imshow(
    correlation_matrix,
    text_auto=".2f",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    aspect="auto",
    labels={"color": "Correlation Strength"},
    title="Relationships Between Player Attacking Statistics"
)

heatmap_fig.update_layout(
    height=650,
    margin=dict(l=30, r=30, t=70, b=30),
    xaxis_title=None,
    yaxis_title=None,
    coloraxis_colorbar=dict(
        title="Correlation"
    )
)

st.plotly_chart(heatmap_fig, width="stretch")

# Explain how to interpret the heatmap
st.markdown(
    """
    **How to read this chart**

    - **+1.00:** Very strong positive relationship.
    - **0.00:** No linear relationship.
    - **-1.00:** Very strong negative relationship.

    Each square compares two attacking statistics.
    The diagonal is always 1.00 because each statistic
    is perfectly correlated with itself.
    """
)

# Identify the strongest relationship between different statistics
correlation_pairs = []

stat_columns = list(correlation_matrix.columns)

for i in range(len(stat_columns)):
    for j in range(i + 1, len(stat_columns)):
        stat1 = stat_columns[i]
        stat2 = stat_columns[j]

        correlation_value = correlation_matrix.loc[
            stat1, stat2
        ]

        correlation_pairs.append(
            (stat1, stat2, correlation_value)
        )

strongest_pair = max(
    correlation_pairs,
    key=lambda pair: abs(pair[2])
)

st.success(
    f"Strongest relationship: {strongest_pair[0]} "
    f"and {strongest_pair[1]} "
    f"(correlation: {strongest_pair[2]:.2f})."
)

st.caption(
    "Analysis includes players with at least 900 minutes played. "
    "These correlations use season totals, so playing time may "
    "influence the relationships. Correlation does not imply causation."
)
