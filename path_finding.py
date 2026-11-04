from graph_data import cabs_within_radius, load_graph
from random import choice
from heapq import heapify, heappop, heappush
from math import sqrt
from time import perf_counter


#return dict of path time and the shortest paths from pickup location to nearby cabs
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

    while priorityQ:

        current_time, current_ID = heappop(priorityQ)

        if current_ID in visited:
            continue
        visited.add(current_ID)

        for start_id, neighbor_id, road_id, road in graph.out_edges(current_ID, keys=True, data=True):

            travel_seconds = road["travel_time"]
            new_time = current_time + travel_seconds

            if new_time < travel_times[neighbor_id]:
                travel_times[neighbor_id] = new_time

                # Remember how we reached this node
                previous[neighbor_id] = (start_id, current_ID, road_id)
                heappush(priorityQ, (new_time, neighbor_id))


    #reconstruct paths to nearby cabs
    paths = {}

    for cab_id, cab in nearby_cabs.items():

        cab_node_id = cab.node_id

        # Skip cabs that cannot be reached
        if travel_times[cab_node_id] == float('inf'):
            continue

        road_path = []
        current_node = cab_node_id

        # Work backward from cab to pickup location
        while current_node != pickup_id:

            previous_node, end_node, road_id = previous[current_node]

            road_path.append((previous_node, end_node))

            current_node = previous_node

        # Reverse because we reconstructed backward
        road_path.reverse()

        paths[cab_id] = (road_path, travel_times[cab_node_id])

    return paths

#estimate minimum travel time in seconds
def heuristic(graph, node_id, end_node_id):
    x1, y1 = graph.nodes[node_id]['x'], graph.nodes[node_id]['y']
    x2, y2 = graph.nodes[end_node_id]['x'], graph.nodes[end_node_id]['y']
    shortest_distance = sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    shortest_distance_miles = shortest_distance / 1609.344  #meters to miles
    max_speed_miles = 80  

    return 3600 * (shortest_distance_miles / max_speed_miles)

def a_star(graph, pickup_id, radius_miles):

    nearby_cabs = cabs_within_radius(graph, pickup_id, radius_miles)

    paths = {}

    for cab_id, cab in nearby_cabs.items():
        travel_times = {node: float('inf') for node in graph.nodes}

        destination = cab.node_id

        priorityQ = [(0, pickup_id)]
        travel_times[pickup_id] = 0

        previous = {}
        visited = set()

        while priorityQ:
            current_priority, current_ID = heappop(priorityQ)

            if current_ID in visited:
                continue

            if current_ID == destination:
                break
            visited.add(current_ID)

            for start_id, neighbor_id, edge_key, road in graph.out_edges(current_ID, keys=True, data=True):

                travel_seconds = road["travel_time"]
                new_distance = (travel_times[current_ID] + travel_seconds)

                if new_distance < travel_times.get(neighbor_id, float("inf")):

                    travel_times[neighbor_id] = new_distance

                    previous[neighbor_id] = (current_ID, neighbor_id)

                    #A* priority
                    estimated_total = (new_distance + heuristic(graph, neighbor_id, destination))
                    heappush(priorityQ, (estimated_total, neighbor_id))

        if destination not in previous:
            continue

        road_path = []
        current_node = destination

        while current_node != pickup_id:
            edge = previous[current_node]
            road_path.append(edge)
            current_node = edge[0]

        road_path.reverse()

        # Store cab ID, road path, and travel time
        paths[cab_id] = (road_path, travel_times[destination])

    return paths


def main():
    graph = load_graph()
    # picks a random pickup location from the graph
    pickup_id = choice(list(graph.nodes))
    radius_miles = 10 # self explanatory

    start = perf_counter()
    distances_a = a_star(graph, pickup_id, radius_miles)
    end = perf_counter()
    print("A* execution time:", end - start)
    start = perf_counter()
    distances_dijkstra = dijkstra(graph, pickup_id, radius_miles)
    end = perf_counter()
    print("Dijkstra execution time:", end - start)
    
    
    for cab_id in distances_dijkstra:
        if cab_id not in distances_a:
            print(f"Cab {cab_id}: Missing from A*")
            continue

        # dijkstra_time = distances_dijkstra[cab_id][1]
        # astar_time = distances_a[cab_id][1]

        # print(f"\nCab {cab_id}")
        # print("Dijkstra:", dijkstra_time)
        # print("A*:", astar_time)


    


if __name__ == "__main__":
    main()