import networkx as nx

class SmartGridRerouter:
    def __init__(self):
        """
        Initialize the Smart Grid as a Directed Graph.
        Nodes: Substations
        Edges: Power Lines with 'weight' (distance/cost) and 'capacity' (MW).
        """
        self.G = nx.DiGraph()
        self._initialize_network()

    def _initialize_network(self):
        """
        Model a sample Nigerian distribution network.
        Nodes: Lagos_Main, Ikeja_Sub, Victoria_Island_Sub, Lekki_Sub, Epe_Sub
        """
        # (Source, Target, weight/cost, capacity_MW)
        lines = [
            ('Lagos_Main', 'Ikeja_Sub', 10, 5000),
            ('Lagos_Main', 'Victoria_Island_Sub', 15, 3000),
            ('Ikeja_Sub', 'Lekki_Sub', 20, 2000),
            ('Victoria_Island_Sub', 'Lekki_Sub', 12, 1500),
            ('Lekki_Sub', 'Epe_Sub', 25, 1000),
            ('Ikeja_Sub', 'Epe_Sub', 40, 800),
            # Redundant paths for rerouting
            ('Victoria_Island_Sub', 'Epe_Sub', 35, 1200)
        ]
        
        for u, v, w, c in lines:
            self.G.add_edge(u, v, weight=w, capacity=c)

    def find_alternative_path(self, source, target, faulty_node, required_load_mw):
        """
        Calculates the shortest alternative path avoiding a faulty node.
        Checks if the path has sufficient capacity.
        """
        print(f"\n--- Rerouting Request: {source} -> {target} (Avoiding {faulty_node}) ---")
        
        # Create a temporary copy of the graph to simulate the fault
        temp_G = self.G.copy()
        if faulty_node in temp_G:
            temp_G.remove_node(faulty_node)
            print(f"Node {faulty_node} marked as FAULTY and removed from active topology.")

        try:
            # Calculate shortest path using Dijkstra (based on 'weight')
            path = nx.shortest_path(temp_G, source=source, target=target, weight='weight')
            
            # Check capacity along the path
            min_capacity = float('inf')
            path_edges = []
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                cap = temp_G[u][v]['capacity']
                min_capacity = min(min_capacity, cap)
                path_edges.append((u, v, cap))

            if min_capacity >= required_load_mw:
                print(f"SUCCESS: Alternative path found: {' -> '.join(path)}")
                print(f"Path Capacity: {min_capacity} MW (Required: {required_load_mw} MW)")
                return {
                    'status': 'SUCCESS',
                    'path': path,
                    'bottleneck_capacity': min_capacity,
                    'total_cost': nx.path_weight(temp_G, path, weight='weight')
                }
            else:
                print(f"FAILURE: Path found but capacity is insufficient ({min_capacity} MW < {required_load_mw} MW).")
                return {
                    'status': 'INSUFFICIENT_CAPACITY',
                    'path': path,
                    'bottleneck_capacity': min_capacity
                }

        except nx.NetworkXNoPath:
            print(f"FAILURE: No alternative path exists from {source} to {target} avoiding {faulty_node}.")
            return {'status': 'NO_PATH_EXISTS'}

# Example Usage:
# rerouter = SmartGridRerouter()
# # Normal flow: Lagos_Main -> Ikeja_Sub -> Lekki_Sub -> Epe_Sub
# # If Ikeja_Sub fails, find another way to Epe_Sub
# result = rerouter.find_alternative_path(
#     source='Lagos_Main', 
#     target='Epe_Sub', 
#     faulty_node='Ikeja_Sub', 
#     required_load_mw=900
# )
# print(result)
