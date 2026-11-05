from time import perf_counter

import streamlit as st
from streamlit_folium import st_folium

from graph_data import load_graph, cabs_within_radius
from path_finding import a_star, dijkstra
from ui_helpers import build_map, best_cab, path_nodes, route_segments, in_bounds, snap_to_node

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

# Run both algorithms
if st.sidebar.button("Find ride", disabled=pickup_id is None):
    with st.spinner("Searching..."):
        st.session_state.result = {"A*": run_search(graph, pickup_id, radius, "A*"), "Dijkstra": run_search(graph, pickup_id, radius, "Dijkstra")}
        st.session_state.results_key = (pickup_id, radius)

if st.sidebar.button("Clear Pickup", disabled=pickup_id is None):
    st.session_state.pickup_id = None
    st.session_state.pop("result", None)
    st.rerun()

# Initialize variables
cabs, segments, origin_ids = {}, [], set()

# Check for out of bounds or no cabs in radius
if pickup_id is None:
    st.info("Please click to select a pickup location inside the dashed box.")
else:
    cabs = cabs_within_radius(graph, pickup_id, radius)
    if not cabs:
        st.warning("No cabs available in the search radius, try a larger radius.")

    # Build summary
    result = st.session_state.get("result")

    # Filter out cabs that are not in the search radius
    if result and st.session_state.get("results_key") == (pickup_id, radius):
        summary = {}
        for name, (paths, runtime) in result.items():
            best = best_cab(paths)
            if best is not None:
                path, seconds = paths[best]
                summary[name] = dict(best=best, seconds=seconds, runtime=runtime, nodes=path_nodes(path, cabs[best].node_id))

        # Check for results and display summary
        if len(summary) < 2:
            st.warning("No reachable cabs found for this pickup location.")
        else:
            a, d = summary["A*"], summary["Dijkstra"]
            origin_ids = {a["best"], d["best"]}
            segments = route_segments(graph, a["nodes"], d["nodes"])

            # Display stats for both algorithms
            cols = st.columns(4)
            cols[0].metric("A* compute (s)", f"{a['runtime']:.2f}")
            cols[1].metric("Dijkstra compute (s)", f"{d['runtime']:.2f}")
            cols[2].metric("A* route (min)", f"{a['seconds'] / 60:.1f}")
            cols[3].metric("Dijkstra route (min)", f"{d['seconds'] / 60:.1f}")
            st.markdown(":green[■ Selected driver]   ·   :gray[■ Other drivers]   ·   :red[■ Pickup]   ·   :violet[■ Both routes]   ·   :red[■ A* only]   ·   :blue[■ Dijkstra only]")

# Create map with output and preserve last clicked location
out = st_folium(build_map(graph, pickup_id, radius, cabs, segments, origin_ids), height = 600, returned_objects=["last_clicked"], key="map")

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

