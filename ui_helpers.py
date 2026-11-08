import folium
import osmnx as ox

from graph_data import road_coordinates

# Conversion factor
MILE = 1609.344

# Map bounds (precomputed)
SERVICE_BOUNDS = {
    "north": 37.8320262,
    "east": -122.3497964,
    "south": 37.708264,
    "west": -122.51194,
}

# Helper to find which cab the algorithm's path points to
def best_cab(paths):
    if not paths:
        return None
    return min(paths, key=lambda cab_id: paths[cab_id][1])

# Helper to get points to draw from the path data
def path_nodes(path, start_node):
    # Start at the driver and trace the path
    return [start_node] + [v for _, v in path]

def edge_points(graph, u, v):
    roads = graph.get_edge_data(u, v)
    if roads is None: return []
    key = min(roads, key=lambda k: roads[k]["travel_time"])
    return road_coordinates(graph, u, v, key)

# Helper to determine what routes are A* or Dijkstra only and which are both for color coding
def route_segments(graph, a_nodes, d_nodes):
    # Split into sets and determine which are both and which are unique
    a_edges = set(zip(a_nodes, a_nodes[1:]))
    d_edges = set(zip(d_nodes, d_nodes[1:]))
    groups = [(a_edges & d_edges, "purple", "Both"), (a_edges - d_edges, "red", "A* only"), (d_edges - a_edges, "blue", "Dijkstra only")]
    return [(edge_points(graph, u, v), color, label) for edges, color, label in groups for u, v in edges]

# Build folium map
def build_map(graph, pickup_id=None, radius=None, cabs=None, segments=None, origin_ids=()):
    # Declare map bounds
    b = SERVICE_BOUNDS
    corners = [[b["south"], b["west"]], [b["north"], b["east"]]]

    # Center on middle or pickup location
    if pickup_id is not None:
        node = graph.nodes[pickup_id]
        m = folium.Map(location=(node["y"], node["x"]), zoom_start=13)
    else:
        m = folium.Map()
        m.fit_bounds(corners)

    # Create rectangle for service area
    folium.Rectangle(bounds=corners, color="black", weight=2, dash_array="8 8", fill=False, tooltip="Service area",).add_to(m)

    if pickup_id is not None:
        # Draw search radius circle
        center = (node["y"], node["x"])
        folium.Circle(center, radius=radius * MILE, color="black", weight=1, fill=False).add_to(m)

        # Mark best cab as green, others marked as gray
        for cab_id, cab in (cabs or {}).items():
            if cab_id in origin_ids: color = "green"
            else: color = "gray"
            folium.Marker((cab.latitude, cab.longitude), tooltip=f"Cab {cab_id}", icon=folium.Icon(color=color)).add_to(m)

        # Draw route segments
        for points, color, label in (segments or []):
            folium.PolyLine(points, color=color, weight=5, opacity=0.85, tooltip=label).add_to(m)

        # Draw pickup location
        folium.Marker(center, tooltip="Pickup", icon=folium.Icon(color="red")).add_to(m)
    return m

# Helper to check if a location is within the map bounds
def in_bounds(lat, lon):
    return SERVICE_BOUNDS["south"] <= lat <= SERVICE_BOUNDS["north"] and SERVICE_BOUNDS["west"] <= lon <= SERVICE_BOUNDS["east"]

# Helper to snap a location to the nearest road node
def snap_to_node(graph, lat, lon):
    return ox.distance.nearest_nodes(graph, X=lon, Y=lat)