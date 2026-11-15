
import pandas as pd
import plotly.express as px

# 1. Load player data
players = pd.read_csv("../data/players.csv")

# 2. Select forwards
forwards = players[
    players["position"].str.contains("F")
].copy()

# 3. Keep players with at least 900 minutes
forwards = forwards[forwards["time"] >= 900].copy()

# 4. Calculate goals per 90 minutes
forwards["goals_per_90"] = (
    forwards["goals"] / forwards["time"] * 90
)

# 5. Select the top 10 forwards
top_10 = forwards.nlargest(10, "goals_per_90")

# 6. Create an interactive horizontal bar chart
fig = px.bar(
    top_10,
    x="goals_per_90",
    y="player_name",
    orientation="h",
    title="Top 10 La Liga Forwards by Goals per 90 (2015–16)",
    labels={
        "goals_per_90": "Goals per 90 Minutes",
        "player_name": "Player"
    },
    hover_data=["team_title", "goals", "time"]
)

# 7. Display the highest-ranked player at the top

fig.update_traces(
    texttemplate="%{x:.2f}",
    textposition="outside"
)

fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    xaxis_range=[0, 1.35],
    height=550
)


# 8. Open the chart
fig.show()
