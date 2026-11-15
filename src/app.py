"""Interactive attacking-performance dashboard for La Liga 2015–16.

The sidebar controls which analysis is shown. Each page keeps its own
filters and explanations, while both datasets are loaded only once per run.
"""

from pathlib import Path
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# Resolve paths relative to this file rather than the terminal's folder.
# This also works when Streamlit is launched from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

st.set_page_config(
    page_title="La Liga Attacking Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Streamlit reruns this script when a widget changes. Caching avoids
# reading the same CSV files from disk on every interaction.
@st.cache_data
def load_data():
    players_df = pd.read_csv(DATA_DIR / "players.csv")
    shots_df = pd.read_csv(DATA_DIR / "shots.csv")
    return players_df, shots_df


players, shots = load_data()

# Only navigation stays in the sidebar. The selected page renders its
# own title, filters, chart and notes in the main content area.
st.sidebar.title("⚽ La Liga Analytics")
st.sidebar.caption("2015–16 Season")
st.sidebar.divider()
page = st.sidebar.radio(
    "Explore",
    ["Overview", "Goals per 90", "Goals vs xG", "Player Shot Map", "Correlations"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.caption("Attacking Performance Analytics")


def get_filtered_forwards():
    """Apply the same team and minutes filters on the first two charts."""
    # The position field can contain multiple positions. Checking for "F"
    # includes anyone listed as a forward, even if they also play elsewhere.
    forwards = players[
        players["position"].str.contains("F")
    ].copy()

    # Sorting keeps the team menu predictable when we switch pages.
    teams = sorted(forwards["team_title"].unique())

    team_options = ["All Teams"] + teams

    selected_team = st.selectbox(
        "Select a team",
        options=team_options
    )

    # Only narrow the dataset when a club is selected. The original
    # players dataframe stays unchanged for the other dashboard pages.
    if selected_team != "All Teams":
        forwards = forwards[
            forwards["team_title"] == selected_team
        ].copy()



    min_minutes = st.slider(
        "Minimum minutes played",
        min_value=0,
        max_value=3000,
        value=900,
        step=100
    )

    # Exclude zero-minute records: dividing by zero would make the
    # goals-per-90 calculation invalid. .copy() gives us a safe dataframe
    # to add calculated columns without modifying the source data.
    forwards = forwards[
        (forwards["time"] >= min_minutes) &
        (forwards["time"] > 0)
    ].copy()


    # Normalizing to 90 minutes makes players with different playing
    # times easier to compare than using their season goal totals alone.
    forwards["goals_per_90"] = (
        forwards["goals"] / forwards["time"] * 90
    )

    return forwards


if page == "Overview":
    st.title("⚽ La Liga Attacking Analytics")
    st.write("Explore attacking player performance during the 2015–16 La Liga season.")
    st.subheader("Dataset Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Players", len(players))
    with col2:
        st.metric("Total Shots", len(shots))
    with col3:
        st.metric("Total Goals", players["goals"].sum())

    st.divider()
    st.subheader("Explore the season")
    st.write(
        "Use the sidebar to compare forwards' scoring rates, examine goals "
        "against expected goals, inspect individual shot locations, or "
        "explore correlations between attacking statistics."
    )

elif page == "Goals per 90":
    st.title("Goals per 90")
    st.write("Compare forwards' scoring rates with team and playing-time filters.")
    forwards = get_filtered_forwards()
    # nlargest chooses the ten highest scoring rates after filters.
    top_10 = forwards.nlargest(10, "goals_per_90")

    st.subheader("Top 10 Forwards by Goals per 90")

    # A horizontal bar chart leaves room for longer player names.
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

    st.plotly_chart(fig, use_container_width=True)

elif page == "Goals vs xG":
    st.title("Goals vs Expected Goals")
    st.write("Compare actual goals with the quality of players' chances.")
    forwards = get_filtered_forwards()
    st.subheader("Goals vs Expected Goals (xG)")

    # Each point is one forward; bubble area reflects shot volume,
    # and team colors make it easier to compare players from the same club.
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

    # The dashed diagonal represents goals == xG. Players above it
    # outscored their expected goals; players below it underperformed xG.
    # Using the larger axis maximum keeps the whole line in view.
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

elif page == "Player Shot Map":
    st.title("Player Shot Map")
    st.subheader("Interactive Player Shot Map")

    st.caption(
        "Explore where players attempted their shots during "
        "the 2015–16 La Liga season."
    )

    # The selector searches actual names found in the shots file.
    shot_players = sorted(shots["player"].dropna().unique())

    selected_player = st.selectbox(
        "Select a player",
        options=shot_players,
        index=shot_players.index("Lionel Messi")
        if "Lionel Messi" in shot_players else 0
    )

    # Work on a copy because we add pitch coordinates below.
    player_shots = shots[
        shots["player"] == selected_player
    ].copy()


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






    # Understat stores shot locations as fractions of pitch dimensions.
    # Convert to metres and flip X so the goal is on the left.
    # We keep the original X and Y columns intact in the CSV.
    player_shots["pitch_x"] = (1 - player_shots["X"]) * 105
    player_shots["pitch_y"] = player_shots["Y"] * 68

    # Goals are plotted separately so they can use a different color.
    goals = player_shots[player_shots["result"] == "Goal"]
    other_shots = player_shots[player_shots["result"] != "Goal"]

    # Plotly shapes draw the pitch; scatter traces draw the shots.
    shot_fig = go.Figure()

    shot_fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=52.5, y1=68,
        line=dict(color="white", width=2),
        fillcolor="#176b3a",
        layer="below"
    )

    shot_fig.add_shape(
        type="rect",
        x0=0, y0=13.84,
        x1=16.5, y1=54.16,
        line=dict(color="white", width=2)
    )

    shot_fig.add_shape(
        type="rect",
        x0=0, y0=24.84,
        x1=5.5, y1=43.16,
        line=dict(color="white", width=2)
    )

    shot_fig.add_shape(
        type="rect",
        x0=-2, y0=30.34,
        x1=0, y1=37.66,
        line=dict(color="white", width=2)
    )

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

    arc_x = []
    arc_y = []

    # Approximate the curved penalty arc using 101 points on a circle.
    # The radius (9.15 m) matches the required distance from the spot.
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

    shot_fig.add_trace(
        go.Scatter(
            x=other_shots["pitch_x"],
            y=other_shots["pitch_y"],
            mode="markers",
            name="Other Shots",
            marker=dict(
                # Higher-xG chances appear as larger circles; +7 keeps
                # low-xG attempts visible on the pitch.
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

    # Keep both axes free to zoom independently. Locking their scale
    # would force Plotly to enlarge small rectangular zoom selections.
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

    left_space, pitch_column, right_space = st.columns([1, 3, 1])

    with pitch_column:
        st.plotly_chart(shot_fig, width="stretch")

elif page == "Correlations":
    st.title("Attacking Statistics Correlations")
    st.subheader("How Are Attacking Statistics Connected?")

    st.write(
        "This chart explores whether players who perform well "
        "in one attacking statistic also tend to perform well "
        "in another."
    )

    stat_names = {
        "goals": "Goals",
        "xG": "Expected Goals",
        "assists": "Assists",
        "xA": "Expected Assists",
        "shots": "Shots",
        "key_passes": "Key Passes"
    }

    # Require 900 minutes to reduce the influence of very limited
    # appearances. These are still season totals, not per-90 figures.
    correlation_players = players[
        players["time"] >= 900
    ].copy()

    # Pandas corr() computes Pearson correlations for each pair
    # of columns. Values range from -1 to +1; they are not probabilities.
    correlation_matrix = correlation_players[
        list(stat_names.keys())
    ].corr()

    correlation_matrix = correlation_matrix.rename(
        index=stat_names,
        columns=stat_names
    )

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

    correlation_pairs = []

    stat_columns = list(correlation_matrix.columns)

    # Check each unique pair once. Skip the diagonal (always 1)
    # and the duplicate pairs on the other side of the matrix.
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

    # Absolute value also allows a strong negative relationship to win.
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
