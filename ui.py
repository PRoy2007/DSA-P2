from random import choice
from time import perf_counter

import folium
import streamlit as st
from streamlit_folium import st_folium

from graph_data import load_graph, cabs_within_radius, road_coordinates
from path_finding import a_star, dijkstra

##
## HELPER FUNCTIONS
##

# Conversion factor
MILE = 1609.344

@st.cache_resource
def get_graph():
    return load_graph()

# Performs the search operations and returns the path found and runtime
@st.cache_resource
def run_search(_graph, pickup_id, radius = 3, algo = "A*"):
    start = perf_counter()
    if algo == "Dijkstra":
        path = dijkstra(_graph, pickup_id, radius)
    else:
        path = a_star(_graph, pickup_id, radius)
    return path, perf_counter() - start

# Helper to find which cab the algorithm's path points to
def best_cab(paths):
    if not paths:
        return None
    return min(paths, key=lambda cab_id: paths[cab_id][1])

# Helper to get points to draw from the path data
def route_points(graph, path):
    points = []
    for u, v in path:
        roads = graph.get_edge_data(u, v)
        if roads is None:
            continue
        key = min(roads, key=lambda k: roads[k]["travel_time"])
        points.extend(road_coordinates(graph, u, v, key))
    return points

# Build folium map
def build_map(graph, pickup_id, radius, cabs, route=None, best_id=None):
    pickup = graph.nodes[pickup_id]
    center = (pickup["y"], pickup["x"])

    # Create pickup marker and radius marker
    m = folium.Map(location=center, zoom_start=13)
    folium.Marker(center, tooltip="Pickup", icon=folium.Icon(color="red")).add_to(m)
    folium.Circle(center, radius=radius * MILE, color="red", fill=False).add_to(m)

    # Mark best cab as blue, rest as green
    for cab_id, cab in cabs.items():
        color = "blue" if cab_id == best_id else "green"
        folium.Marker((cab.latitude, cab.longitude), tooltip=cab_id, icon=folium.Icon(color=color)).add_to(m)

    if route:
        folium.PolyLine(route, color="blue", weight=5).add_to(m)
    return m

##
## PAGE
##

graph = get_graph()
st.title("Drivers2You")

# Choose a random pickup location if none is selected
if "pickup_id" not in st.session_state:
    st.session_state.pickup_id = choice(list(graph.nodes))
pickup_id = st.session_state.pickup_id

# Search options, run search, and new pickup
radius = st.sidebar.slider("Search radius (miles)", 0.5, 5.0, 2.0, 0.5)
algo = st.sidebar.selectbox("Algorithm", ["A*", "Dijkstra"])
if st.sidebar.button("Find ride"):
    st.session_state.result = (*run_search(graph, pickup_id, radius, algo), algo)
if st.sidebar.button("New random pickup"):
    st.session_state.pickup_id = choice(list(graph.nodes))
    st.session_state.pop("result", None)
    st.rerun()

# Initialize variables
cabs = cabs_within_radius(graph, pickup_id, radius)
route, best_id = None, None

# Build summary
result = st.session_state.get("result")
if result:
    paths, runtime, used = result
    best_id = best_cab(paths)
    if best_id is not None:
        path, seconds = paths[best_id]
        route = route_points(graph, path)
        c1, c2 = st.columns(2)
        c1.metric("ETA (min)", f"{seconds / 60:.1f}")
        c2.metric(f"{used} runtime (s)", f"{runtime:.2f}")

# Create map
st_folium(build_map(graph, pickup_id, radius, cabs, route, best_id), height = 550, returned_objects=[])