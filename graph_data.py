from pathlib import Path
from osmnx.distance import great_circle, nearest_nodes
from osmnx.graph import graph_from_bbox
from osmnx.io import load_graphml, save_graphml
from osmnx.routing import add_edge_speeds, add_edge_travel_times
# using the graph from here: https://osmnx.readthedocs.io/en/stable/user-reference.html#module-osmnx.graph
# _create_graph method is defined here: https://github.com/gboeing/osmnx/blob/v2.1.1/osmnx/graph.py



class Cab: # make a cab class for our data
    def __init__(self, cab_id, latitude, longitude, occupied, timestamp):
        self.cab_id = cab_id
        self.latitude = latitude
        self.longitude = longitude
        self.occupied = occupied
        self.timestamp = timestamp
        self.node_id = None




def load_cabs(folder, timestamp):
    cabs = {}
    # within the data folder /cabspottingdata/ each cab is organized like new_XXXXXX.txt
    # there are 537 of those files with locations at each point in time
    # get all txt files from the folder & iterate through them, then iterate line by line
    for path in Path(folder).glob("*.txt"):
        cab_id = path.stem
        with path.open() as file:
            for line in file:
                # distribute the tuple into these vars
                latitude, longitude, occupied, observed_at = line.split()
                observed_at = int(observed_at)
                if observed_at <= timestamp:
                    # inject the data into our cab class
                    cabs[cab_id] = Cab(cab_id, float(latitude), float(longitude), occupied == "1", observed_at)
    return cabs




def attach_cabs(graph, cabs):
    # this is to store the cab data inside of the graph
    # it'll find the nearest street node for each cab
    # and then set that to cab.node_id 
    #this givse it a real location that will be used for Ander's visuals
    graph.graph["cabs"] = cabs
    cab_list = list(cabs.values())
    longitudes = []
    latitudes = []
    for cab in cab_list:
        longitudes.append(cab.longitude)
        latitudes.append(cab.latitude)
    node_ids = nearest_nodes(graph, X=longitudes, Y=latitudes)
    for index in range(len(cab_list)):
        cab_list[index].node_id = int(node_ids[index])
    return graph




def cabs_within_radius(graph, pickup_id, radius_miles):
    # within the network of nodes, we want to find which are in a radius circle
    # it'll reuturn UNOCUPIED cabs (available to take passengers) within that radius
    pickup = graph.nodes[pickup_id]
    nearby = {}
    cabs = graph.graph["cabs"]
    for cab_id in cabs:
        cab = cabs[cab_id]
        if not cab.occupied:
            distance_meters = great_circle(pickup["y"], pickup["x"], cab.latitude, cab.longitude)
            distance_miles = distance_meters / 1609.344
            if distance_miles <= radius_miles:
                nearby[cab_id] = cab
    return nearby




def road_coordinates(graph, start_id, end_id, road_id):
    # this gives Anders the points needed to draw a particular road
    # has a list of (latitude, longitude) nad points that follow the road shape
    # if there are no shape points, then just the two endpoints are used
    # the shape points help "shape" the road so that it fits the map data better
    road = graph.edges[start_id, end_id, road_id]
    start = graph.nodes[start_id]
    end = graph.nodes[end_id]
    points = [(start["y"], start["x"]), (end["y"], end["x"])]
    if "geometry" in road:
        points = []
        for longitude, latitude in road["geometry"].coords:
            points.append((latitude, longitude))
        if points[0] != (start["y"], start["x"]):
            points.reverse()
    return points





def load_graph():
    # makes it easy to load the locally stored graph
    cab_files = sorted(Path("cabspottingdata").glob("*.txt"))
    observations = cab_files[0].read_text().splitlines()
    middle_observation = observations[len(observations) // 2].split()
    timestamp = int(middle_observation[3])
    graph = load_graphml("roads.graphml")
    cabs = load_cabs("cabspottingdata", timestamp)
    attach_cabs(graph, cabs)
    return graph



def download_roads(filename="roads.graphml"):
    # downloads the maps data for local SF area
    # just needs to be done once
    graph = graph_from_bbox(
        (-122.943611, 37.378775, -121.918125, 38.161515),
        network_type="drive",
    ) # expand area to get at least 100k data points
    graph = add_edge_speeds(graph, fallback=30)
    graph = add_edge_travel_times(graph)
    print(f"{graph.number_of_nodes():,} nodes")
    assert graph.number_of_nodes() >= 100_000, "Expand the bounds further"
    save_graphml(graph, filename)
    return graph

    
if __name__ == '__main__':
    download_roads() # if you don't have the roads yet, run this file
    # should be uploaded via git, but if not, it can be downloaded again
    
    




