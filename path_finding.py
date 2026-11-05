from graph_data import cabs_within_radius, load_graph
from heapq import heapify, heappop, heappush
from math import sin, cos, asin, sqrt, radians


#return dict of path time and the shortest paths from pickup location to nearby cabs
#and a stats dict
#paths will be lists of edges using road_id
#paths = { cab_id: (path, time), ... }
#the path is a list of tuples (start_id, end_id)

def dijkstra(graph, pickup_id, radius_miles):

    nearby_cabs = cabs_within_radius(graph, pickup_id, radius_miles)

    #initialize all travel times to infinity
    travel_times = {node: float('inf') for node in graph.nodes}

    #previous node and road used
    previous = {}
    travel_times[pickup_id] = 0

    priorityQ = [(0, pickup_id)]
    heapify(priorityQ)

    visited = set()
    nodes_checked = []

    while priorityQ:

        current_time, current_ID = heappop(priorityQ)

        if current_ID in visited:
            continue
        visited.add(current_ID)
        nodes_checked.append(current_ID)

        for start_id, neighbor_id, road_id, road in graph.out_edges(current_ID, keys=True, data=True):

            travel_seconds = road["travel_time"]
            new_time = current_time + travel_seconds

            if new_time < travel_times[neighbor_id]:
                travel_times[neighbor_id] = new_time

                # Remember how we reached this node
                previous[neighbor_id] = (neighbor_id, start_id, road_id)
                heappush(priorityQ, (new_time, neighbor_id))


    #reconstruct paths to nearby cabs
    paths = {}

    for cab_id, cab in nearby_cabs.items():

        cab_node_id = cab.node_id

        #skip cabs that cannot be reached
        if travel_times[cab_node_id] == float('inf'):
            continue

        road_path = []
        current_node = cab_node_id

        while current_node != pickup_id:

            previous_node, end_node, road_id = previous[current_node]
            road_path.append((previous_node, end_node))

            current_node = end_node

        paths[cab_id] = (road_path, travel_times[cab_node_id])

    stats = {
        "nodes_checked": {
            cab_id: nodes_checked
            for cab_id in paths
        },
        "nodes_checked_count": {
            cab_id: len(nodes_checked)
            for cab_id in paths
        },
        "total_nodes_checked": len(nodes_checked)
    }

    return paths, stats

#estimate minimum travel time in seconds using haverstine distance
def heuristic(graph, node_id, end_node_id):
    lon1 = radians(graph.nodes[node_id]['x'])
    lat1 = radians(graph.nodes[node_id]['y'])

    lon2 = radians(graph.nodes[end_node_id]['x'])
    lat2 = radians(graph.nodes[end_node_id]['y'])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (sin(dlat / 2) ** 2+ cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2)

    distance_meters = 2 * 6371000 * asin(sqrt(a))
    distance_miles = distance_meters / 1609.344

    max_speed_mph = 80

    return 3600 * (distance_miles / max_speed_mph)  


#runs A* on every pick_up, cab, pair
#return dict of path time and the shortest paths from pickup location to nearby cabs
#and return a stats dict
#paths will be lists of edges using road_id
#paths = { cab_id: (path, time), ... }
#the path is a list of tuples (start_id, end_id)

def a_star(graph, pickup_id, radius_miles):

    nearby_cabs = cabs_within_radius(graph, pickup_id, radius_miles)

    paths = {}
    nodes_checked = {}
    nodes_checked_count = {}

    for cab_id, cab in nearby_cabs.items():
        travel_times = {node: float('inf') for node in graph.nodes}

        destination = cab.node_id

        priorityQ = [(0, pickup_id)]
        travel_times[pickup_id] = 0

        previous = {}
        visited = set()
        checked_nodes = []

        while priorityQ:
            current_priority, current_ID = heappop(priorityQ)

            if current_ID in visited:
                continue

            checked_nodes.append(current_ID)

            if current_ID == destination:
                break
            visited.add(current_ID)

            for start_id, neighbor_id, edge_key, road in graph.out_edges(current_ID, keys=True, data=True):

                travel_seconds = road["travel_time"]
                new_distance = (travel_times[current_ID] + travel_seconds)

                if new_distance < travel_times.get(neighbor_id, float("inf")):

                    travel_times[neighbor_id] = new_distance

                    previous[neighbor_id] = (neighbor_id, current_ID)

                    estimated_total = (new_distance + heuristic(graph, neighbor_id, destination))
                    heappush(priorityQ, (estimated_total, neighbor_id))

        #store nodes checked, even if destination is unreachable
        nodes_checked[cab_id] = checked_nodes
        nodes_checked_count[cab_id] = len(checked_nodes)

        if destination not in previous:
            continue

        road_path = []
        current_node = destination

        while current_node != pickup_id:
            previous_node, next_node = previous[current_node]
            road_path.append((previous_node, next_node))
            current_node = next_node

        #cab ID, road path, and travel time
        paths[cab_id] = (road_path, travel_times[destination])

    stats = {"nodes_checked": nodes_checked, "nodes_checked_count": nodes_checked_count, "total_nodes_checked": sum(nodes_checked_count.values())}

    return paths, stats

# def check_path(path):
#     for i in range(len(path) - 1):
#         current_end = path[i][1]
#         next_start = path[i + 1][0]

#         if current_end != next_start:
#             print(
#                 f"Discontinuity at edge {i}: "
#                 f"{path[i]} -> {path[i + 1]}"
#             )

#     print("First edge:", path[0])
#     print("Last edge:", path[-1])

# from time import perf_counter
# from random import choice
# def test_run():
#     graph = load_graph()
#     # picks a random pickup location from the graph
#     pickup_id = choice(list(graph.nodes))
#     radius_miles = 0.5 # self explanatory

#     start = perf_counter()
#     distances_a, a_stats = a_star(graph, pickup_id, radius_miles)
#     end = perf_counter()
#     print("A* execution time:", end - start)

#     for cab_id in distances_a:
#         print(f"Cab {cab_id}:")
#         check_path(distances_a[cab_id][0])
    
#     start = perf_counter()
#     distances_dijkstra, dijkstra_stats = dijkstra(graph, pickup_id, radius_miles)
#     end = perf_counter()
#     print("Dijkstra execution time:", end - start)
    
#     for cab_id in distances_dijkstra:
#         print(f"Cab {cab_id}:")
#         check_path(distances_dijkstra[cab_id][0])

#     # for cab_id in distances_dijkstra:
#     #     if cab_id not in distances_a:
#     #         print(f"Cab {cab_id}: Missing from A*")
#     #         continue

#         # dijkstra_time = distances_dijkstra[cab_id][1]
#         # astar_time = distances_a[cab_id][1]

#         # print(f"\nCab {cab_id}")
#         # print("Dijkstra:", dijkstra_time)
#         # print("A*:", astar_time)
    
#     print(distances_dijkstra)
#     print("----------------------")
#     print(distances_a)

# test_run()