from time import perf_counter

import streamlit as st
from streamlit_folium import st_folium

from graph_data import load_graph, cabs_within_radius
from path_finding import a_star, dijkstra
from ui_helpers import build_map, route_points, best_cab, in_bounds, snap_to_node

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

#
# Streamlit UI
#

# Basic page setup
st.set_page_config(page_title="Drivers2You", layout="wide")
graph = get_graph()
pickup_id = st.session_state.get("pickup_id")
st.title("Drivers2You")

#Sidebar (Search options, run search, new pickup)
radius = st.sidebar.slider("Search radius (miles)", 0.5, 5.0, 2.0, 0.5)
algo = st.sidebar.selectbox("Algorithm", ["A*", "Dijkstra"])

if st.sidebar.button("Find ride", disabled=pickup_id is None):
    with st.spinner("Searching..."):
        st.session_state.result = (*run_search(graph, pickup_id, radius, algo), algo)

if st.sidebar.button("Clear Pickup", disabled=pickup_id is None):
    st.session_state.pickup_id = None
    st.session_state.pop("result", None)
    st.rerun()

# Initialize variables
cabs, route, best_id = {}, None, None

# Check for out of bounds or no cabs in radius
if pickup_id is None:
    st.info("Please click to select a pickup location inside the dashed box.")
else:
    cabs = cabs_within_radius(graph, pickup_id, radius)
    if not cabs:
        st.warning("No cabs available in the search radius, try a larger radius.")

    # Build summary
    result = st.session_state.get("result")
    if result:
        paths, runtime, used = result
        best_id = best_cab(paths)
        if best_id is None:
            st.warning("No reachable cabs found for this pickup location.")
        else:
            path, seconds = paths[best_id]
            route = route_points(graph, path)
            c1, c2 = st.columns(2)
            c1.metric("ETA (min)", f"{seconds / 60:.1f}")
            c2.metric(f"{used} runtime (s)", f"{runtime:.2f}")

# Create map with output and preserve last clicked location
out = st_folium(build_map(graph, pickup_id, radius, cabs, route, best_id), height = 600, returned_objects=["last_clicked"], key="map")

# Don't change location if a location was already selected
if out:
    clicked = out.get("last_clicked")
else:
    clicked = None

if clicked and clicked != st.session_state.get("handled_click"):
    st.session_state.handled_click = clicked
    if pickup_id is None:
        lat, lon = clicked["lat"], clicked["lng"]
        if in_bounds(lat, lon):
            st.session_state.pickup_id = snap_to_node(graph, lat, lon)
            st.session_state.pop("result", None)
            st.rerun()
        else:
            st.warning("Location outside service area.")

