from pathlib import Path
from unittest import TestCase
from folium import Circle, Icon, Map, Marker, PolyLine
from graph_data import road_coordinates
# pull some things from the test graph file
from test_graph import graph, nearby_cabs, pickup_id, radius_miles


class AndersExample(TestCase):


    def test_draw_real_pickup_cabs_and_streets(self):

        # gets the position of the random pickup spot
        pickup = graph.nodes[pickup_id]
        pickup_position = (pickup["y"], pickup["x"])

        # some things from this folium library that makes plotting easy
        drawing = Map(location=pickup_position, zoom_start=12)
        Marker(location=pickup_position, tooltip="Random pickup", icon=Icon(color="red")).add_to(drawing)
        Circle(location=pickup_position, radius=radius_miles * 1609.344, color="red", fill=False, tooltip="Five-mile pickup radius").add_to(drawing)

        # plot the cabs
        for cab_id in nearby_cabs:
            cab = nearby_cabs[cab_id]
            position = (cab.latitude, cab.longitude)
            Marker(location=position, tooltip=cab_id, popup="Actual recorded cab location", icon=Icon(color="green")).add_to(drawing)

        # plot the street the pickup will happen on
        # aka the edge touching the pickup node
        for start_id, end_id, road_id, road in graph.out_edges(pickup_id, keys=True, data=True):
            points = road_coordinates(graph, start_id, end_id, road_id)
            PolyLine(locations=points, color="blue", weight=5, tooltip="Street leaving pickup").add_to(drawing)

        # save it so you can view it
        output = Path("tests/map_example.html")
        drawing.save(str(output))
        self.assertTrue(output.is_file())



