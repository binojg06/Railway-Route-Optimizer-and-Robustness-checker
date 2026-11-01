import networkx as nx
from collections import deque


class RailwayOptimizer:

    def __init__(self, railway_network):
        self.network = railway_network
        self.graph = railway_network.graph

    # ==========================================================
    # BASIC GRAPH
    # ==========================================================

    def simple_graph(self):
        """
        Convert the railway graph into an undirected simple graph.

        Stations = vertices
        Railway connections = edges
        """
        # Build once and reuse; return a copy so callers can
        # safely modify the graph without corrupting the cache.
        if getattr(self, "_simple_cache", None) is None:
            base = nx.Graph()
            base.add_nodes_from(self.graph.nodes())

            for u, v in self.graph.edges():
                if u != v:
                    base.add_edge(u, v)

            self._simple_cache = base

        return self._simple_cache.copy()

    # ==========================================================
    # CAPACITY GRAPH
    # ==========================================================

    def capacity_graph(self):
        """
        Create a directed capacity graph.

        Every railway connection contributes capacity 1.
        Parallel railway connections increase the capacity.
        """

        g = nx.DiGraph()

        g.add_nodes_from(self.graph.nodes())

        for u, v in self.graph.edges():

            if u == v:
                continue

            if g.has_edge(u, v):
                g[u][v]["capacity"] += 1
            else:
                g.add_edge(
                    u,
                    v,
                    capacity=1
                )

        return g

    # ==========================================================
    # SHORTEST-DISTANCE ROUTE (DIJKSTRA)
    # ==========================================================

    def shortest_distance_route(self, source, destination):
        """
        Find the minimum-distance route using Dijkstra's algorithm.

        The ``distance`` edge weight is read directly from the
        cleaned railway dataset. For parallel train connections
        between the same stations, NetworkX considers the minimum
        distance edge weight when calculating the route.
        """
        if source == destination:
            if source in self.graph:
                return {
                    "path": [source],
                    "total_distance": 0.0,
                    "total_time": 0.0,
                    "connections": []
                }
            return None

        try:
            path = nx.dijkstra_path(
                self.graph,
                source=source,
                target=destination,
                weight="distance"
            )
            return self._route_details(path, "distance")

        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def distance_alternative_routes(self, source, destination, min_extra_km=100, max_extra_km=200, max_candidates=500):
        """Return shortest route and alternatives 100-200 km longer.

        Routes are simple paths ranked by summed dataset distance. Because the
        source graph is a MultiDiGraph, collapse parallel edges to the minimum
        distance edge for path enumeration; _route_details then resolves each
        segment to the matching minimum-distance connection.
        """
        shortest = self.shortest_distance_route(source, destination)
        if shortest is None:
            return {"shortest": None, "alternatives": [], "message": "No route exists in the supplied dataset."}

        simple = nx.DiGraph()
        simple.add_nodes_from(self.graph.nodes())
        for u, v, data in self.graph.edges(data=True):
            if u == v:
                continue
            try:
                distance = float(data.get("distance", 0))
            except (TypeError, ValueError):
                continue
            if distance < 0:
                continue
            if not simple.has_edge(u, v) or distance < simple[u][v].get("distance", float("inf")):
                simple.add_edge(u, v, distance=distance)

        alternatives = []
        checked = 0
        try:
            paths = nx.shortest_simple_paths(simple, source, destination, weight="distance")
            for path in paths:
                checked += 1
                if checked > max_candidates:
                    break
                details = self._route_details(path, "distance")
                extra = details["total_distance"] - shortest["total_distance"]
                if extra < min_extra_km - 1e-6:
                    continue
                if extra <= max_extra_km + 1e-6:
                    details["extra_distance"] = extra
                    alternatives.append(details)
                elif extra > max_extra_km:
                    # Paths are distance-sorted; later paths cannot qualify.
                    break
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            pass

        return {
            "shortest": shortest,
            "alternatives": alternatives,
            "message": "" if alternatives else f"No alternative path was found between {min_extra_km:g} and {max_extra_km:g} km longer within the first {max_candidates} candidate paths."
        }

    def shortest_route(self, source, destination):
        """Backward-compatible alias for shortest-distance Dijkstra."""
        return self.shortest_distance_route(source, destination)

    # ==========================================================
    # BALANCED OPTIMAL ROUTE (DISTANCE + TIME)
    # ==========================================================

    def optimal_balanced_route(self, source, destination, distance_weight=0.5):
        """
        Find a balanced route using normalized distance and travel time.
        Neither metric is optimized alone: both contribute equally by default.
        Routes are only searched within the source's connected component.
        """
        if source not in self.graph or destination not in self.graph:
            return None
        if source == destination:
            return {"path": [source], "total_distance": 0.0,
                    "total_time": 0.0, "connections": [],
                    "optimal_score": 0.0, "connected_component_size": 1}

        g = nx.DiGraph()
        g.add_nodes_from(self.graph.nodes())
        distances, times = [], []
        best_edges = {}
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            if u == v:
                continue
            try:
                d = float(data.get("distance", 0))
                t = float(data.get("travel_time", 0))
                if d < 0 or t < 0:
                    continue
            except (TypeError, ValueError):
                continue
            distances.append(d)
            times.append(t)
            pair = (u, v)
            score = (d, t)
            if pair not in best_edges or (
                distance_weight * d + (1-distance_weight) * t
                < distance_weight * best_edges[pair][0]
                + (1-distance_weight) * best_edges[pair][1]
            ):
                best_edges[pair] = (d, t, data)

        if not distances or not times:
            return None
        d_min, d_max = min(distances), max(distances)
        t_min, t_max = min(times), max(times)
        d_range = max(d_max - d_min, 1e-9)
        t_range = max(t_max - t_min, 1e-9)
        for (u, v), (d, t, data) in best_edges.items():
            normalized_distance = (d - d_min) / d_range
            normalized_time = (t - t_min) / t_range
            combined = distance_weight * normalized_distance + (1-distance_weight) * normalized_time
            g.add_edge(u, v, distance=d, travel_time=t, combined_cost=combined, **{k: data.get(k, "") for k in ("train_name", "train_number", "departure", "arrival")})

        try:
            path = nx.dijkstra_path(g, source, destination, weight="combined_cost")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        connections = []
        total_distance = total_time = total_score = 0.0
        for u, v in zip(path, path[1:]):
            edge = g[u][v]
            total_distance += edge["distance"]
            total_time += edge["travel_time"]
            total_score += edge["combined_cost"]
            original = edge
            connections.append({
                "source": u, "destination": v,
                "train_name": original.get("train_name", ""),
                "train_number": original.get("train_number", ""),
                "distance": float(edge["distance"]),
                "travel_time": float(edge["travel_time"]),
                "departure": original.get("departure", ""),
                "arrival": original.get("arrival", "")
            })
        component = nx.node_connected_component(self.simple_graph(), source)
        return {
            "path": path,
            "total_distance": round(total_distance, 2),
            "total_time": round(total_time, 2),
            "connections": connections,
            "optimal_score": round(total_score, 4),
            "connected_component_size": len(component)
        }

    # ==========================================================
    # FASTEST ROUTE
    # ==========================================================

    def fastest_route(self, source, destination):

        try:

            path = nx.dijkstra_path(
                self.graph,
                source=source,
                target=destination,
                weight="travel_time"
            )

            return self._route_details(
                path,
                "travel_time"
            )

        except (
            nx.NetworkXNoPath,
            nx.NodeNotFound
        ):

            return None

    # ==========================================================
    # ROUTE DETAILS
    # ==========================================================

    def _route_details(
        self,
        path,
        optimization
    ):

        total_distance = 0
        total_time = 0

        connections = []

        for u, v in zip(
            path,
            path[1:]
        ):

            edges = self.graph[u][v]

            if optimization == "distance":

                key = min(
                    edges,
                    key=lambda k:
                    float(
                        edges[k].get(
                            "distance",
                            0
                        )
                    )
                )

            else:

                key = min(
                    edges,
                    key=lambda k:
                    float(
                        edges[k].get(
                            "travel_time",
                            0
                        )
                    )
                )

            edge = edges[key]

            distance = float(
                edge.get(
                    "distance",
                    0
                )
            )

            travel_time = float(
                edge.get(
                    "travel_time",
                    0
                )
            )

            total_distance += distance
            total_time += travel_time

            connections.append({
                "source": u,
                "destination": v,
                "train_name":
                    edge.get(
                        "train_name",
                        ""
                    ),
                "train_number":
                    edge.get(
                        "train_number",
                        ""
                    ),
                "distance":
                    distance,
                "travel_time":
                    travel_time,
                "departure":
                    edge.get(
                        "departure",
                        ""
                    ),
                "arrival":
                    edge.get(
                        "arrival",
                        ""
                    )
            })

        return {
            "path": path,
            "total_distance":
                round(
                    total_distance,
                    2
                ),
            "total_time":
                round(
                    total_time,
                    2
                ),
            "connections":
                connections
        }

    # ==========================================================
    # 1. CUTS AND CONNECTIVITY
    # ==========================================================

    def pair_connectivity_and_cuts(
        self,
        source,
        destination
    ):
        """
        Pair-specific Cuts and Connectivity.

        Finds only the critical stations and tracks that actually
        affect the selected Source -> Destination connection.

        Returned keys:
            connected           - is there a path source -> destination
            components          - number of connected components
                                  (separate islands) in the railway network
            critical_stations   - stations whose failure disconnects the pair
            critical_tracks     - tracks whose failure disconnects the pair
        """

        g = self.simple_graph()

        result = {
            "source": source,
            "destination": destination,
            "connected": False,
            "components": nx.number_connected_components(g),
            "critical_stations": [],
            "critical_tracks": []
        }

        if source not in g or destination not in g:
            return result

        result["connected"] = nx.has_path(g, source, destination)

        if not result["connected"]:
            # Source and destination lie in separate islands
            return result

        # Work only inside the island that contains the pair.
        # (Much faster than analysing the whole dataset, and the
        # answer is identical because other islands are irrelevant.)
        island = g.subgraph(
            nx.node_connected_component(g, source)
        ).copy()

        # ------------------------------------------------------
        # Critical stations
        # ------------------------------------------------------

        for station in list(nx.articulation_points(island)):

            # Source and destination themselves are not
            # considered intermediate failure stations.
            if station in (source, destination):
                continue

            neighbors = list(island.adj[station])
            island.remove_node(station)

            if not nx.has_path(island, source, destination):
                result["critical_stations"].append(station)

            # Restore the station
            island.add_node(station)
            island.add_edges_from(
                (station, n) for n in neighbors
            )

        # ------------------------------------------------------
        # Critical tracks
        # ------------------------------------------------------

        for u, v in list(nx.bridges(island)):

            island.remove_edge(u, v)

            if not nx.has_path(island, source, destination):
                result["critical_tracks"].append((u, v))

            # Restore the track
            island.add_edge(u, v)

        return result

    # ==========================================================
    # 2. k-CONNECTED GRAPHS
    # ==========================================================

    def k_connectivity(
        self,
        source,
        destination
    ):
        """
        Pair vertex connectivity.

        k represents the minimum number of vertices whose
        removal is required to disconnect source and destination.
        """

        g = self.simple_graph()

        result = {
            "source": source,
            "destination": destination,
            "k": 0,
            "connected": False
        }

        if source not in g:
            return result

        if destination not in g:
            return result

        if source == destination:
            return result

        if not nx.has_path(
            g,
            source,
            destination
        ):
            return result

        try:

            k = nx.node_connectivity(
                g,
                source,
                destination
            )

            result["k"] = int(k)
            result["connected"] = True

        except nx.NetworkXError:

            result["k"] = 0
            result["connected"] = False

        return result

    # ==========================================================
    # 3 & 4. NETWORK FLOW + FORD-FULKERSON
    # ==========================================================

    def ford_fulkerson(
        self,
        source,
        destination
    ):
        """
        Manual Ford-Fulkerson labeling algorithm.

        BFS labels vertices in the residual graph.
        Each augmenting path contributes its bottleneck
        capacity to the maximum flow.
        """

        capacity = self.capacity_graph()

        result = {
            "source": source,
            "destination": destination,
            "max_flow": 0,
            "augmenting_paths": []
        }

        if source not in capacity:
            return result

        if destination not in capacity:
            return result

        if source == destination:
            return result

        # ------------------------------------------------------
        # Residual network
        # ------------------------------------------------------

        residual = {}

        for node in capacity.nodes():

            residual[node] = {}

        for u, v, data in capacity.edges(
            data=True
        ):

            cap = float(
                data.get(
                    "capacity",
                    1
                )
            )

            residual[u][v] = cap

            if v not in residual:
                residual[v] = {}

            residual[v].setdefault(
                u,
                0
            )

        maximum_flow = 0

        # ------------------------------------------------------
        # Ford-Fulkerson loop
        # ------------------------------------------------------

        while True:

            # ----------------------------------------------
            # LABELING STEP
            # ----------------------------------------------

            parent = {
                source: None
            }

            queue = deque(
                [source]
            )

            while (
                queue
                and destination not in parent
            ):

                u = queue.popleft()

                for v, capacity_value in residual[
                    u
                ].items():

                    if (
                        v not in parent
                        and capacity_value > 0
                    ):

                        parent[v] = u

                        queue.append(v)

                        if v == destination:
                            break

            # No augmenting path
            if destination not in parent:
                break

            # ----------------------------------------------
            # FIND BOTTLENECK
            # ----------------------------------------------

            path = []

            path_flow = float(
                "inf"
            )

            current = destination

            while current != source:

                previous = parent[
                    current
                ]

                path.append(
                    current
                )

                path_flow = min(
                    path_flow,
                    residual[
                        previous
                    ][current]
                )

                current = previous

            path.append(source)

            path.reverse()

            # ----------------------------------------------
            # AUGMENT FLOW
            # ----------------------------------------------

            current = destination

            while current != source:

                previous = parent[
                    current
                ]

                residual[
                    previous
                ][current] -= path_flow

                residual[
                    current
                ].setdefault(
                    previous,
                    0
                )

                residual[
                    current
                ][previous] += path_flow

                current = previous

            maximum_flow += path_flow

            result[
                "augmenting_paths"
            ].append({
                "path": path,
                "flow":
                    int(path_flow)
                    if path_flow.is_integer()
                    else round(
                        path_flow,
                        2
                    )
            })

        result[
            "max_flow"
        ] = (
            int(maximum_flow)
            if float(
                maximum_flow
            ).is_integer()
            else round(
                maximum_flow,
                2
            )
        )

        return result

    # ==========================================================
    # 5. MAX-FLOW MIN-CUT THEOREM
    # ==========================================================

    def max_flow_min_cut(
        self,
        source,
        destination
    ):
        """
        Calculate maximum flow and minimum cut.

        The result verifies:
            Maximum Flow = Minimum Cut
        """

        capacity = self.capacity_graph()

        result = {
            "source": source,
            "destination": destination,
            "max_flow": 0,
            "min_cut": 0,
            "theorem_verified": False,
            "cut_edges": []
        }

        if source not in capacity:
            return result

        if destination not in capacity:
            return result

        if source == destination:
            return result

        try:

            max_flow, flow_dict = nx.maximum_flow(
                capacity,
                source,
                destination,
                capacity="capacity"
            )

            min_cut, partition = nx.minimum_cut(
                capacity,
                source,
                destination,
                capacity="capacity"
            )

            reachable, non_reachable = partition

            cut_edges = []

            for u in reachable:

                for v in capacity.successors(
                    u
                ):

                    if v in non_reachable:

                        cut_edges.append({
                            "source": u,
                            "destination": v,
                            "capacity":
                                capacity[u][v][
                                    "capacity"
                                ]
                        })

            result["max_flow"] = int(
                max_flow
            )

            result["min_cut"] = int(
                min_cut
            )

            result[
                "theorem_verified"
            ] = (
                max_flow == min_cut
            )

            result[
                "cut_edges"
            ] = cut_edges

            result[
                "flow_dict"
            ] = flow_dict

        except nx.NetworkXError:

            pass

        return result

    # ==========================================================
    # 6. MENGER'S THEOREM
    # ==========================================================

    def menger_analysis(
        self,
        source,
        destination
    ):
        """
        Menger's theorem through edge-disjoint paths.

        Maximum number of edge-disjoint paths between
        two vertices equals their edge connectivity.
        """

        g = self.simple_graph()

        result = {
            "source": source,
            "destination": destination,
            "paths": [],
            "count": 0,
            "edge_connectivity": 0
        }

        if source not in g:
            return result

        if destination not in g:
            return result

        if source == destination:
            return result

        if not nx.has_path(
            g,
            source,
            destination
        ):
            return result

        try:

            paths = list(
                nx.edge_disjoint_paths(
                    g,
                    source,
                    destination
                )
            )

            connectivity = nx.edge_connectivity(
                g,
                source,
                destination
            )

            result[
                "paths"
            ] = paths

            result[
                "count"
            ] = len(paths)

            result[
                "edge_connectivity"
            ] = int(
                connectivity
            )

        except nx.NetworkXError:

            pass

        return result

    # ==========================================================
    # ROBUSTNESS GRAPH
    # ==========================================================

    def robustness_graph(
        self,
        source,
        destination
    ):
        """
        Build ONLY the graph relevant to the robustness
        analysis of the selected Source -> Destination.

        This DOES NOT use shortest route or fastest route.

        Priority:
        1. Menger edge-disjoint paths
        2. Critical stations/tracks
        3. Connected supporting structure
        """

        g = self.simple_graph()

        if source not in g:
            return {
                "connected": False,
                "nodes": [],
                "edges": [],
                "critical_stations": [],
                "critical_tracks": [],
                "menger_paths": []
            }

        if destination not in g:
            return {
                "connected": False,
                "nodes": [],
                "edges": [],
                "critical_stations": [],
                "critical_tracks": [],
                "menger_paths": []
            }

        if not nx.has_path(
            g,
            source,
            destination
        ):

            return {
                "connected": False,
                "nodes": [source, destination],
                "edges": [],
                "critical_stations": [],
                "critical_tracks": [],
                "menger_paths": []
            }

        cuts = self.pair_connectivity_and_cuts(
            source,
            destination
        )

        menger = self.menger_analysis(
            source,
            destination
        )

        critical_stations = set(
            cuts[
                "critical_stations"
            ]
        )

        critical_tracks = set()

        for u, v in cuts[
            "critical_tracks"
        ]:

            critical_tracks.add(
                frozenset(
                    (u, v)
                )
            )

        # ------------------------------------------------------
        # Build visualization graph from Menger paths
        # ------------------------------------------------------

        selected_edges = set()
        selected_nodes = {
            source,
            destination
        }

        for path in menger[
            "paths"
        ]:

            for node in path:
                selected_nodes.add(
                    node
                )

            for u, v in zip(
                path,
                path[1:]
            ):

                selected_edges.add(
                    frozenset(
                        (u, v)
                    )
                )

        # ------------------------------------------------------
        # If no Menger path was returned but connection exists,
        # use the connectivity structure ONLY as a fallback.
        # This is NOT shortest/fastest routing.
        # ------------------------------------------------------

        if not selected_edges:

            try:

                connected_component = nx.node_connected_component(
                    g,
                    source
                )

                subgraph = g.subgraph(
                    connected_component
                )

                # Keep only nodes that lie in the
                # source-destination connection structure.
                nodes_on_paths = set()

                for node in subgraph.nodes():

                    if node in (
                        source,
                        destination
                    ):

                        nodes_on_paths.add(
                            node
                        )
                        continue

                    test = subgraph.copy()

                    test.remove_node(
                        node
                    )

                    if (
                        source in test
                        and destination in test
                        and nx.has_path(
                            test,
                            source,
                            destination
                        )
                    ):
                        nodes_on_paths.add(
                            node
                        )

                # Always keep source and destination.
                selected_nodes.update(
                    nodes_on_paths
                )

                for u, v in subgraph.edges():

                    if (
                        u in selected_nodes
                        and v in selected_nodes
                    ):

                        selected_edges.add(
                            frozenset(
                                (u, v)
                            )
                        )

            except nx.NetworkXError:
                pass

        # ------------------------------------------------------
        # Add critical components affecting this pair
        # ------------------------------------------------------

        for station in critical_stations:

            selected_nodes.add(
                station
            )

        for track in critical_tracks:

            values = list(track)

            if len(values) == 2:

                selected_nodes.update(
                    values
                )

                selected_edges.add(
                    track
                )

        edges = []

        for edge in selected_edges:

            values = list(edge)

            if len(values) != 2:
                continue

            u, v = values

            edges.append({
                "source": u,
                "destination": v,
                "critical":
                    edge in critical_tracks
            })

        return {
            "connected": True,
            "nodes": list(
                selected_nodes
            ),
            "edges": edges,
            "critical_stations":
                list(
                    critical_stations
                ),
            "critical_tracks":
                [
                    list(edge)
                    for edge in critical_tracks
                ],
            "menger_paths":
                menger[
                    "paths"
                ]
        }

    # ==========================================================
    # COMPLETE AGA ROBUSTNESS REPORT
    # ==========================================================

    def aga_robustness_report(
        self,
        source,
        destination
    ):
        """
        Execute all six AGA concepts for the selected
        Source -> Destination pair.
        """

        cuts = self.pair_connectivity_and_cuts(
            source,
            destination
        )

        k_result = self.k_connectivity(
            source,
            destination
        )

        ford_result = self.ford_fulkerson(
            source,
            destination
        )

        flow_result = self.max_flow_min_cut(
            source,
            destination
        )

        menger_result = self.menger_analysis(
            source,
            destination
        )

        graph_result = self.robustness_graph(
            source,
            destination
        )

        return {
            "cuts": cuts,

            "k_connectivity":
                k_result,

            "ford_fulkerson":
                ford_result,

            "max_flow_min_cut":
                flow_result,

            "menger":
                menger_result,

            "robustness_graph":
                graph_result
        }


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    from railway_network import RailwayNetwork

    railway = RailwayNetwork()

    optimizer = RailwayOptimizer(
        railway
    )

    stations = list(
        railway.get_stations()
    )

    if len(stations) >= 2:

        source = stations[0]
        destination = stations[1]

        print()
        print("=" * 70)
        print(
            "AGA RAILWAY NETWORK ROBUSTNESS ANALYZER"
        )
        print("=" * 70)

        print(
            "\nSource      :",
            source
        )

        print(
            "Destination :",
            destination
        )

        report = optimizer.aga_robustness_report(
            source,
            destination
        )

        print("\nCUTS AND CONNECTIVITY")
        print(
            "Connected:",
            report["cuts"]["connected"]
        )

        print(
            "Critical stations:",
            report["cuts"][
                "critical_stations"
            ]
        )

        print(
            "Critical tracks:",
            report["cuts"][
                "critical_tracks"
            ]
        )

        print("\nK-CONNECTIVITY")
        print(
            "k =",
            report["k_connectivity"]["k"]
        )

        print("\nNETWORK FLOW / FORD-FULKERSON")
        print(
            "Maximum flow:",
            report["ford_fulkerson"][
                "max_flow"
            ]
        )

        print("\nMAX-FLOW MIN-CUT")
        print(
            "Maximum flow:",
            report["max_flow_min_cut"][
                "max_flow"
            ]
        )

        print(
            "Minimum cut:",
            report["max_flow_min_cut"][
                "min_cut"
            ]
        )

        print(
            "Theorem verified:",
            report["max_flow_min_cut"][
                "theorem_verified"
            ]
        )

        print("\nMENGER'S THEOREM")
        print(
            "Edge connectivity:",
            report["menger"][
                "edge_connectivity"
            ]
        )

        print(
            "Edge-disjoint paths:",
            report["menger"][
                "count"
            ]
        )

        print("\nROBUSTNESS GRAPH")

        print(
            "Nodes:",
            len(
                report[
                    "robustness_graph"
                ]["nodes"]
            )
        )

        print(
            "Edges:",
            len(
                report[
                    "robustness_graph"
                ]["edges"]
            )
        )

        print("\nAnalysis completed.")