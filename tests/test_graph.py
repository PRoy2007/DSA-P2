from random import choice
from unittest import TestCase
from graph_data import cabs_within_radius, load_graph



# if you don't have the downloaded OSMNX data yet, run the graph_data.py file first
# but also make sure to do pip -r requirements.txt to download the libs
# then python3 graph_data.py
graph = load_graph()
# picks a random pickup location from the graph
pickup_id = choice(list(graph.nodes))
radius_miles = 5 # self explanatory
nearby_cabs = cabs_within_radius(graph, pickup_id, radius_miles)




# to run the tests, the terminal command is: python3 -B -m unittest discover -s tests -v
# not sure if it's diff for windows, but it's probably the same
class ExampleForPromit(TestCase):

    # here's how to iterate through nearby cabs/roads
    # should be able to be used inside of Dikjstra's and A* algos
    def test_iterate_nearby_cabs_and_roads(self):
        for cab_id in nearby_cabs:
            cab = nearby_cabs[cab_id]
            cab_node_id = cab.node_id
            # graph.out_edges gives roads leaving that node
            # one-way streets are directional edges, two way are bidirectional edges
            for start_id, neighbor_id, road_id, road in graph.out_edges(cab_node_id, keys=True, data=True):
                travel_seconds = road["travel_time"]
                # travel time is estimated by OSMNX, so that should make it easier hopefully
                self.assertGreaterEqual(travel_seconds, 0)




