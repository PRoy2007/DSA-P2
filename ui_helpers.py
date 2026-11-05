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
def build_map(graph, pickup_id=None, radius=None, cabs=None, route=None, best_id=None, view=None):
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
        # Draw pickup location
        node = graph.nodes[pickup_id]
        center = (node["y"], node["x"])
        folium.Marker(center, tooltip="Pickup", icon=folium.Icon(color="red")).add_to(m)
        folium.Circle(center, radius=radius * MILE, color="red", fill=False).add_to(m)

        # Mark best cab as blue, others marked as green
        for cab_id, cab in (cabs or {}).items():
            color = "blue" if cab_id == best_id else "green"
            folium.Marker((cab.latitude, cab.longitude), tooltip=cab_id, icon=folium.Icon(color=color)).add_to(m)

        if route:
            folium.PolyLine(route, color="blue", weight=5).add_to(m)
    return m

# Helper to check if a location is within the map bounds
def in_bounds(lat, lon):
    return SERVICE_BOUNDS["south"] <= lat <= SERVICE_BOUNDS["north"] and SERVICE_BOUNDS["west"] <= lon <= SERVICE_BOUNDS["east"]

# Helper to snap a location to the nearest road node
def snap_to_node(graph, lat, lon):
    return ox.distance.nearest_nodes(graph, X=lon, Y=lat)