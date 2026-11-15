
import pandas as pd

# 1. Configure how Pandas displays tables
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

# 2. Load our datasets
players = pd.read_csv("../data/players.csv")
shots = pd.read_csv("../data/shots.csv")

# 3. Preview the datasets
print("\nPLAYERS DATASET")
print(players.head())

print("\nSHOTS DATASET")
print(shots.head())

# 4. Check dataset dimensions
print("\nDATASET DIMENSIONS")
print("Players:", players.shape)
print("Shots:", shots.shape)

# 5. Check missing values
print("\nMISSING VALUES IN PLAYERS DATASET")
print(players.isnull().sum())

print("\nMISSING VALUES IN SHOTS DATASET")
print(shots.isnull().sum())

# 6. Examine player positions
print("\nPLAYER POSITIONS")
print(players["position"].value_counts())


# 7. Filter players who have played as forwards
forwards = players[players["position"].str.contains("F")].copy()

print("\nNUMBER OF FORWARDS")
print(len(forwards))

print("\nFIRST 10 FORWARDS")
print(forwards[["player_name", "team_title", "position", "goals", "assists"]].head(10))


# 8. Calculate attacking performance metrics

forwards["goals_per_90"] = (
    forwards["goals"] / forwards["time"] * 90
)

forwards["goals_minus_xg"] = (
    forwards["goals"] - forwards["xG"]
)

# 9. Display the results
print("\nATTACKING PERFORMANCE METRICS")

print(
    forwards[
        ["player_name", "goals", "time", "goals_per_90", "goals_minus_xg"]
    ].head(10).round(2)
)


# 10. Keep forwards with at least 900 minutes played
qualified_forwards = forwards[forwards["time"] >= 900].copy()

print("\nQUALIFIED FORWARDS")
print("Number of qualified forwards:", len(qualified_forwards))

# 11. Rank forwards by goals per 90 minutes
top_scorers_per_90 = qualified_forwards.sort_values(
    by="goals_per_90",
    ascending=False
)

print("\nTOP 10 FORWARDS BY GOALS PER 90")
print(
    top_scorers_per_90[
        ["player_name", "team_title", "goals", "time", "goals_per_90"]
    ].head(10).round(2).to_string(index=False)
)
