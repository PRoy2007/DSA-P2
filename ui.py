from random import choice
from time import perf_counter

import streamlit as st
from streamlit_folium import st_folium

from graph_data import load_graph, cabs_within_radius, road_coordinates
from path_finding import a_star, dijkstra
from ui_helpers import build_map, route_points, best_cab

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