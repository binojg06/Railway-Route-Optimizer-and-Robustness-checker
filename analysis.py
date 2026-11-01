import pandas as pd
import matplotlib.pyplot as plt
import os


# --------------------------------------------------
# File paths
# --------------------------------------------------

input_file = os.path.join("data", "cleaned_routes.csv")
results_folder = "results"

os.makedirs(results_folder, exist_ok=True)


# --------------------------------------------------
# Load cleaned dataset
# --------------------------------------------------

df = pd.read_csv(input_file)

print("\n" + "=" * 60)
print("       AGA RAILWAY DATA ANALYSIS")
print("=" * 60)

print("\nTotal route records:", len(df))

print("Total unique source stations:",
      df["source"].nunique())

print("Total unique destination stations:",
      df["destination"].nunique())


# --------------------------------------------------
# Basic statistics
# --------------------------------------------------

print("\n" + "-" * 60)
print("DISTANCE STATISTICS")
print("-" * 60)

print(
    df["distance"].describe()
)


print("\n" + "-" * 60)
print("TRAVEL TIME STATISTICS")
print("-" * 60)

print(
    df["travel_time_min"].describe()
)


# --------------------------------------------------
# Most frequently occurring source stations
# --------------------------------------------------

print("\n" + "-" * 60)
print("TOP SOURCE STATIONS")
print("-" * 60)

top_sources = (
    df["source"]
    .value_counts()
    .head(10)
)

print(top_sources)


# --------------------------------------------------
# Most frequently occurring destination stations
# --------------------------------------------------

print("\n" + "-" * 60)
print("TOP DESTINATION STATIONS")
print("-" * 60)

top_destinations = (
    df["destination"]
    .value_counts()
    .head(10)
)

print(top_destinations)


# --------------------------------------------------
# Average distance
# --------------------------------------------------

average_distance = df["distance"].mean()

print("\nAverage route distance:",
      round(average_distance, 2), "km")


# --------------------------------------------------
# Average travel time
# --------------------------------------------------

average_time = df["travel_time_min"].mean()

print(
    "Average travel time:",
    round(average_time, 2),
    "minutes"
)


# --------------------------------------------------
# Create distance distribution chart
# --------------------------------------------------

plt.figure(figsize=(10, 6))

plt.hist(
    df["distance"],
    bins=30
)

plt.title("Railway Route Distance Distribution")
plt.xlabel("Distance (km)")
plt.ylabel("Number of Routes")

distance_chart = os.path.join(
    results_folder,
    "distance_distribution.png"
)

plt.savefig(distance_chart)

plt.close()


# --------------------------------------------------
# Create travel time distribution chart
# --------------------------------------------------

plt.figure(figsize=(10, 6))

plt.hist(
    df["travel_time_min"],
    bins=30
)

plt.title("Railway Travel Time Distribution")
plt.xlabel("Travel Time (minutes)")
plt.ylabel("Number of Routes")

time_chart = os.path.join(
    results_folder,
    "travel_time_distribution.png"
)

plt.savefig(time_chart)

plt.close()


# --------------------------------------------------
# Create top stations chart
# --------------------------------------------------

plt.figure(figsize=(10, 6))

top_sources.sort_values().plot(
    kind="barh"
)

plt.title("Top 10 Railway Source Stations")
plt.xlabel("Number of Routes")
plt.ylabel("Station")

station_chart = os.path.join(
    results_folder,
    "top_source_stations.png"
)

plt.savefig(station_chart)

plt.close()


# --------------------------------------------------
# Save analysis summary
# --------------------------------------------------

summary_file = os.path.join(
    results_folder,
    "analysis_summary.txt"
)

with open(summary_file, "w") as file:

    file.write("AGA RAILWAY ROUTE OPTIMIZATION SYSTEM\n")
    file.write("=" * 50 + "\n\n")

    file.write(
        f"Total route records: {len(df)}\n"
    )

    file.write(
        f"Unique source stations: {df['source'].nunique()}\n"
    )

    file.write(
        f"Unique destination stations: "
        f"{df['destination'].nunique()}\n"
    )

    file.write(
        f"Average distance: "
        f"{average_distance:.2f} km\n"
    )

    file.write(
        f"Average travel time: "
        f"{average_time:.2f} minutes\n"
    )

    file.write("\nTop source stations:\n")

    for station, count in top_sources.items():

        file.write(
            f"{station}: {count}\n"
        )


print("\n" + "=" * 60)
print("ANALYSIS COMPLETED")
print("=" * 60)

print("\nCharts saved in:")
print(results_folder)

print("\nAnalysis summary saved as:")
print(summary_file)