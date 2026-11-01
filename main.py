from railway_network import RailwayNetwork
from optimization import RailwayOptimizer
from database import RailwayDatabase


def display_result(title, result):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

    if result is None:
        print("No route found.")
        return

    print("Route:")
    print(" -> ".join(result["path"]))

    print("\nTotal distance:",
          result["total_distance"], "km")

    print("Total travel time:",
          result["total_time"], "minutes")

    print("\nTrain connections:")

    for connection in result["connections"]:
        print(
            f'{connection["source"]} -> '
            f'{connection["destination"]} | '
            f'Train: {connection["train_name"]} | '
            f'Number: {connection["train_number"]} | '
            f'Distance: {connection["distance"]} km | '
            f'Time: {connection["travel_time"]} min'
        )


def find_test_route(network):
    """
    Find two connected stations for testing.
    """

    for source, destination, data in network.graph.edges(
        data=True
    ):
        return source, destination

    return None, None


def main():

    print("\n")
    print("=" * 60)
    print("       AGA RAILWAY ROUTE OPTIMIZATION SYSTEM")
    print("=" * 60)

    # --------------------------------------------------
    # Load railway network
    # --------------------------------------------------

    print("\n[1] Loading railway network...")

    railway = RailwayNetwork()

    print(
        "Stations:",
        railway.get_number_of_stations()
    )

    print(
        "Connections:",
        railway.get_number_of_connections()
    )

    # --------------------------------------------------
    # Initialize optimizer
    # --------------------------------------------------

    print("\n[2] Initializing route optimizer...")

    optimizer = RailwayOptimizer(railway)

    print("Optimizer ready.")

    # --------------------------------------------------
    # Initialize database
    # --------------------------------------------------

    print("\n[3] Connecting to database...")

    database = RailwayDatabase()

    print(
        "Database stations:",
        len(database.get_stations())
    )

    print(
        "Database routes:",
        database.get_route_count()
    )

    # --------------------------------------------------
    # Select test stations
    # --------------------------------------------------

    source, destination = find_test_route(railway)

    if source is None or destination is None:

        print("\nNo connected stations found.")
        return

    print("\n[4] Test route selected")

    print("Source      :", source)
    print("Destination :", destination)

    # --------------------------------------------------
    # Shortest route
    # --------------------------------------------------

    print("\n[5] Calculating shortest-distance route using Dijkstra...")

    shortest = optimizer.shortest_distance_route(
        source,
        destination
    )

    display_result(
        "SHORTEST-DISTANCE ROUTE (DIJKSTRA)",
        shortest
    )

    # --------------------------------------------------
    # Fastest route
    # --------------------------------------------------

    print("\n[6] Calculating fastest route...")

    fastest = optimizer.fastest_route(
        source,
        destination
    )

    display_result(
        "FASTEST ROUTE",
        fastest
    )

    # --------------------------------------------------
    # Save results to database
    # --------------------------------------------------

    if shortest:

        database.save_result(
            source=source,
            destination=destination,
            optimization_type="Shortest Distance (Dijkstra)",
            route=" -> ".join(shortest["path"]),
            total_distance=shortest["total_distance"],
            total_time=shortest["total_time"]
        )

    if fastest:

        database.save_result(
            source=source,
            destination=destination,
            optimization_type="Fastest Time",
            route=" -> ".join(fastest["path"]),
            total_distance=fastest["total_distance"],
            total_time=fastest["total_time"]
        )

    print("\n" + "=" * 60)
    print("OPTIMIZATION RESULTS SAVED TO DATABASE")
    print("=" * 60)

    print("\nRailway optimization system test completed successfully.")


# ------------------------------------------------------
# Program entry point
# ------------------------------------------------------

if __name__ == "__main__":
    main()