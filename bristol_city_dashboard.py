import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
from matplotlib.patches import Circle, Rectangle, Arc
import matplotlib.pyplot as plt
from plotly import graph_objects as go

from PIL import Image
import os

# Function to load player images
def get_player_image(player_id, image_dir="Bristol_City_Player_Pics"):
    """
    Retrieve player image based on player_id.
    If the image is not found, return a placeholder.
    """
    image_path = os.path.join(image_dir, f"{player_id}.jpg")
    if os.path.exists(image_path):
        return Image.open(image_path)
    else:
        # Return a placeholder image if the player's image is missing
        return Image.open("placeholder.jpg")  # Ensure "placeholder.jpg" exists 

# Load Data
starting_11 = pd.read_csv("bristol_city_starting_11.csv")
bench = pd.read_csv("bristol_city_bench.csv")

# Merge datasets with an indicator for group
starting_11['status'] = 'Starting 11'
bench['status'] = 'Bench'
players_data = pd.concat([starting_11, bench], ignore_index=True)

# Sidebar Filters
st.sidebar.image("Bristol_City_Logo.png")
st.sidebar.title("Bristol City FC Dashboard")
selected_status = st.sidebar.multiselect(
    "Select Group", 
    players_data["status"].unique(), 
    default=players_data["status"].unique()
)
selected_position = st.sidebar.multiselect(
    "Select Position(s)", 
    players_data["general_position"].unique(),
    default=players_data["general_position"].unique()
)
selected_nationality = st.sidebar.multiselect(
    "Select Nationality", 
    players_data["nationality_name"].unique(),
    default=players_data["nationality_name"].unique()
)

# Filter Data
filtered_data = players_data[
    (players_data["status"].isin(selected_status)) &
    (players_data["general_position"].isin(selected_position)) &
    (players_data["nationality_name"].isin(selected_nationality))
]

# Filter Data
filtered_data = players_data[
    (players_data["status"].isin(selected_status)) &
    (players_data["general_position"].isin(selected_position)) &
    (players_data["nationality_name"].isin(selected_nationality))
]


from itertools import cycle

# Define position coordinates for a 3-4-3 formation
position_coordinates = {
    "GK": cycle([(5, 34)]),  # Goalkeeper
    "CB": cycle([(25, 20), (25, 34), (25, 48)]),  # Center Backs
    "MID": cycle([(50, 10), (50, 24), (50, 44), (50, 58)]),  # Midfielders
    "FWD": cycle([(75, 24), (75, 34), (75, 44)])  # Forwards
}

# Assign coordinates to players based on their general position
def get_position_coordinates(player_position):
    # Extract primary position
    primary_position = player_position.split(',')[0].strip()
    if primary_position == "GK":
        return next(position_coordinates["GK"])
    elif primary_position in ["ST", "LW", "RW", "CF"]:
        return next(position_coordinates["FWD"])
    elif primary_position in ["CB", "LB", "RB"]:
        return next(position_coordinates["CB"])
    elif primary_position in ["CM", "CDM", "CAM", "LM", "RM"]:
        return next(position_coordinates["MID"])
    else:
        return (0, 0)  # Default position for undefined roles

# Apply the mapping to create new columns for x and y coordinates
filtered_data["x_position"], filtered_data["y_position"] = zip(
    *filtered_data["player_positions"].apply(get_position_coordinates)
)

# Debug: Check the generated positions
#st.write("Player positions with coordinates:", filtered_data[["short_name", "player_positions", "x_position", "y_position"]].head())


# Main Dashboard
st.image("Bristol_City_Logo.png", width=100)
st.title("Bristol City FC Team Dashboard")
st.markdown("### Overview")

# Compute Metrics with Formatted Values
total_players = len(filtered_data)
avg_market_value = f"{filtered_data['value_eur'].mean() / 1e6:,.2f}M"
avg_weekly_wage = f"{filtered_data['wage_eur'].mean():,.0f}K"
avg_age = f"{filtered_data['age'].mean():.1f}"
total_team_value = f"{filtered_data['value_eur'].sum() / 1e6:,.2f}M"

# Display Metrics
st.metric("Total Players", total_players)
st.metric("Average Market Value (€M)", avg_market_value)
st.metric("Average Weekly Wage (€M)", avg_weekly_wage)
st.metric("Average Age", avg_age)
st.metric("Total Team Value (€M)", total_team_value)

# Player Card
st.markdown("### Player Card")
player_name = st.selectbox("Select a Player", filtered_data["short_name"].unique())
player_card = filtered_data[filtered_data["short_name"] == player_name].iloc[0]

# Load and display the player's image
player_image = get_player_image(player_card["player_id"])  # Use player_id for the image filename
st.image(player_image, use_container_width=False)

# Display player details
st.write(f"**Name:** {player_card['short_name']}")
st.write(f"**Nationality:** {player_card['nationality_name']}")
st.write(f"**Position:** {player_card['general_position']}")
st.write(f"**Market Value (€):** {player_card['value_eur']:,}")
st.write(f"**Weekly Wage (€):** {player_card['wage_eur']:,}")
st.write(f"**Attributes:**")
st.bar_chart(player_card[["pace", "shooting", "passing", "dribbling", "defending", "physic"]])

# Nationality Visualization on Map
st.markdown("### Player Nationalities")
import requests
import json

# Load GeoJSON data from an online source
url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
world = gpd.read_file(url)  # Directly pass the URL to read GeoJSON data

# Merge player data with world GeoJSON data (if needed for further customization)
fig = px.scatter_geo(
    filtered_data,  # Corrected the data source to use filtered_data directly
    lat="latitude", 
    lon="longitude", 
    hover_name="short_name",
    title="Player Nationalities", 
    size="value_eur", 
    projection="natural earth"
)
st.plotly_chart(fig)

# Football Pitch and Player Positions
st.markdown("### Player Positions on the Pitch")

# Create the pitch
fig = go.Figure()

# Add pitch layout (green background)
fig.add_shape(type="rect", x0=0, y0=0, x1=105, y1=68, line=dict(color="white", width=2), fillcolor="green", opacity=0.3)
fig.add_shape(type="circle", x0=52.5 - 9.15, y0=34 - 9.15, x1=52.5 + 9.15, y1=34 + 9.15, line=dict(color="white", width=2))
fig.add_shape(type="line", x0=52.5, y0=0, x1=52.5, y1=68, line=dict(color="white", width=2))

# Add penalty areas
fig.add_shape(type="rect", x0=0, y0=22.32, x1=16.5, y1=45.68, line=dict(color="white", width=2))
fig.add_shape(type="rect", x0=105, y0=22.32, x1=88.5, y1=45.68, line=dict(color="white", width=2))

# Filter only starting 11 players
starting_11_data = filtered_data[filtered_data['status'] == 'Starting 11']

# Add player positions for starting 11
fig.add_trace(go.Scatter(
    x=starting_11_data["x_position"],
    y=starting_11_data["y_position"],
    mode="markers+text",
    marker=dict(size=12, color="blue"),
    text=starting_11_data["short_name"],  # Player names
    textposition="top center",
    hovertemplate=(
        "<b>%{text}</b><br>" +
        "Position: %{customdata[0]}<br>" +
        "Market Value: €%{customdata[1]:,.2f}<br>" +
        "<extra></extra>"
    ),
    customdata=starting_11_data[["general_position", "value_eur"]].values
))
# Update layout to make the pitch green
fig.update_layout(
    title="Bristol City FC Starting 11",
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    height=500,
    width=800,
    plot_bgcolor="green",  # Green pitch background
    showlegend=False
)

# Display the pitch
st.plotly_chart(fig)


# Bench Players Visual
st.markdown("### Bench Players")
bench_data = filtered_data[filtered_data['status'] == 'Bench']

# Columns to display
bench_columns = ["short_name", "age", "height_cm", "weight_kg", "club_position", "value_eur", "wage_eur", "release_clause_eur"]

# Filter and sort bench players data
bench_data = filtered_data[filtered_data['status'] == 'Bench'][bench_columns]

# Rename columns for better readability
bench_data.rename(columns={
    "short_name": "Name",
    "age": "Age",
    "height_cm": "Height (cm)",
    "weight_kg": "Weight (kg)",
    "club_position": "Club Position",
    "value_eur": "Value (€)",
    "wage_eur": "Wage (€)",
    "release_clause_eur": "Release Clause (€)"
}, inplace=True)

# Sort bench players by value
bench_data = bench_data.sort_values(by="Value (€)", ascending=False)

# Reset index to remove the first column
bench_data.reset_index(drop=True, inplace=True)

# Display the table
st.dataframe(bench_data)


# Player Comparison
st.markdown("### Two Player Attributes")

# Select players for comparison
player_options = filtered_data["short_name"].unique()
player_1 = st.selectbox("Select First Player", player_options, index=0)
player_2 = st.selectbox("Select Second Player", player_options, index=1)

# Attributes for comparison
attributes = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]

# Get data for the selected players
player_1_data = filtered_data[filtered_data["short_name"] == player_1][attributes].iloc[0]
player_2_data = filtered_data[filtered_data["short_name"] == player_2][attributes].iloc[0]

# Create radar chart
import plotly.graph_objects as go

fig = go.Figure()

# Add player 1 data with color-blind-friendly color
fig.add_trace(go.Scatterpolar(
    r=player_1_data.values,
    theta=attributes,
    fill='toself',
    name=player_1,
    line=dict(color='blue', dash='solid'),  # Blue solid line
    fillcolor='rgba(0, 112, 255, 0.3)'  # Semi-transparent blue fill
))

# Add player 2 data with color-blind-friendly color
fig.add_trace(go.Scatterpolar(
    r=player_2_data.values,
    theta=attributes,
    fill='toself',
    name=player_2,
    line=dict(color='orange', dash='dash'),  # Orange dashed line
    fillcolor='rgba(255, 165, 0, 0.3)'  # Semi-transparent orange fill
))

# Update layout
fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]  # Assuming attribute values are in the range 0-100
        )
    ),
    showlegend=True
)

# Display radar chart
st.plotly_chart(fig)


# Salary vs. Performance
st.markdown("### Salary vs. Performance")
fig = px.scatter(
    filtered_data, 
    x="wage_eur", 
    y="overall", 
    size="value_eur", 
    color="general_position",
    hover_name="short_name",
    labels={"wage_eur": "Weekly Salary (€)", "overall": "Overall Rating"}
)
st.plotly_chart(fig)



# Age Distribution
st.markdown("### Age Distribution")
fig = px.histogram(filtered_data, x="age", nbins=10)
st.plotly_chart(fig)


# Best Player by Position
st.markdown("### Best Player by Position")
best_players = filtered_data.loc[filtered_data.groupby("general_position")["overall"].idxmax()]
st.dataframe(best_players[["short_name", "general_position", "value_eur", "overall"]])



# Attribute Heatmap
st.markdown("### Team Attribute Heatmap")
attribute_cols = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]
attribute_data = filtered_data[attribute_cols]
fig = px.imshow(attribute_data.corr(), text_auto=True)
st.plotly_chart(fig)






