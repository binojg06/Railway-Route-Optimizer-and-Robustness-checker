import pandas as pd
import networkx as nx
import os


class RailwayNetwork:

    def __init__(self, data_file="data/cleaned_routes.csv"):
        self.data_file = data_file
        self.graph = nx.MultiDiGraph()

        self.load_data()
        self.build_network()

    # ----------------------------------------------
    # Load cleaned railway data
    # ----------------------------------------------

    def load_data(self):

        if not os.path.exists(self.data_file):
            raise FileNotFoundError(
                f"Dataset not found: {self.data_file}"
            )

        self.data = pd.read_csv(self.data_file)

        print("Cleaned railway dataset loaded.")
        print("Records:", len(self.data))

    # ----------------------------------------------
    # Build railway graph
    # ----------------------------------------------

    def build_network(self):

        for _, row in self.data.iterrows():

            source = row["source"]
            destination = row["destination"]

            distance = float(row["distance"])
            travel_time = float(row["travel_time_min"])

            self.graph.add_edge(
                source,
                destination,
                train_name=row["train_name"],
                train_number=row["train_number"],
                distance=distance,
                travel_time=travel_time,
                departure=row["departure"],
                arrival=row["arrival"]
            )

        print("Railway network created successfully.")

    # ----------------------------------------------
    # Network information
    # ----------------------------------------------

    def get_number_of_stations(self):
        return self.graph.number_of_nodes()

    def get_number_of_connections(self):
        return self.graph.number_of_edges()

    def get_stations(self):
        return list(self.graph.nodes)


# ----------------------------------------------
# Test the railway network
# ----------------------------------------------

if __name__ == "__main__":

    railway = RailwayNetwork()

    print("\n========================================")
    print("RAILWAY NETWORK INFORMATION")
    print("========================================")

    print(
        "Number of stations:",
        railway.get_number_of_stations()
    )

    print(
        "Number of connections:",
        railway.get_number_of_connections()
    )

    print("\nFirst 10 stations:")

    for station in railway.get_stations()[:10]:
        print("-", station)