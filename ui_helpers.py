import folium
from graph_data import load_graph, cabs_within_radius, road_coordinates

# Conversion factor
MILE = 1609.344

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