import os
import pandas as pd


class TrainSchedule:

    def __init__(self):

        base_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        self.file_path = os.path.join(
            base_dir,
            "data",
            "Trains schedule.csv"
        )

        self.df = None

        self.load_schedule()

    # ======================================================
    # LOAD SCHEDULE
    # ======================================================

    def load_schedule(self):

        if not os.path.exists(self.file_path):

            raise FileNotFoundError(
                "Trains schedule.csv was not found in the data folder."
            )

        self.df = pd.read_csv(
            self.file_path
        )

        # Remove unwanted index column

        if "Unnamed: 0" in self.df.columns:

            self.df = self.df.drop(
                columns=["Unnamed: 0"]
            )

        # Clean column names

        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.lower()
        )

        # Clean text columns

        text_columns = [
            "train_name",
            "station_name",
            "station_code",
            "train_number",
            "departure",
            "arrival"
        ]

        for column in text_columns:

            if column in self.df.columns:

                self.df[column] = (
                    self.df[column]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

        print(
            "Train schedule loaded successfully."
        )

        print(
            "Schedule records:",
            len(self.df)
        )

    # ======================================================
    # GET COMPLETE TRAIN SCHEDULE
    # ======================================================

    def get_train_schedule(
        self,
        train_number
    ):

        train_number = str(
            train_number
        ).strip()

        result = self.df[
            self.df["train_number"] == train_number
        ].copy()

        return result

    # ======================================================
    # GET STATIONS FOR A TRAIN
    # ======================================================

    def get_train_stations(
        self,
        train_number
    ):

        schedule = self.get_train_schedule(
            train_number
        )

        if schedule.empty:

            return []

        return schedule[
            "station_name"
        ].tolist()

    # ======================================================
    # FIND TRAINS BETWEEN TWO STATIONS
    # ======================================================

    def find_trains_between(
        self,
        source,
        destination
    ):

        source = str(
            source
        ).strip().upper()

        destination = str(
            destination
        ).strip().upper()

        matching_trains = []

        train_numbers = (
            self.df["train_number"]
            .dropna()
            .unique()
        )

        for train_number in train_numbers:

            schedule = self.get_train_schedule(
                train_number
            )

            if schedule.empty:
                continue

            station_names = (
                schedule["station_name"]
                .str.upper()
                .tolist()
            )

            if (
                source in station_names
                and destination in station_names
            ):

                source_index = (
                    station_names.index(source)
                )

                destination_index = (
                    station_names.index(destination)
                )

                # Destination must occur after source

                if destination_index > source_index:

                    matching_trains.append(
                        train_number
                    )

        return matching_trains

    # ======================================================
    # GET TRAIN COUNT
    # ======================================================

    def get_train_count(self):

        return self.df[
            "train_number"
        ].nunique()

    # ======================================================
    # GET STATION COUNT
    # ======================================================

    def get_station_count(self):

        return self.df[
            "station_code"
        ].nunique()


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    schedule = TrainSchedule()

    print("\n" + "=" * 60)
    print("          TRAIN SCHEDULE TEST")
    print("=" * 60)

    print(
        "\nTotal schedule records:",
        len(schedule.df)
    )

    print(
        "Total trains:",
        schedule.get_train_count()
    )

    print(
        "Total stations:",
        schedule.get_station_count()
    )

    print("\nFirst 5 schedule records:")

    print(
        schedule.df.head().to_string(
            index=False
        )
    )