import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

from railway_network import RailwayNetwork
from optimization import RailwayOptimizer
from database import RailwayDatabase
from schedule import TrainSchedule


# ==========================================================
# AGA RAILWAY ROUTE OPTIMIZATION SYSTEM
# GUI
# ==========================================================


class RailwayGUI:

    def __init__(self, root):

        self.root = root

        # --------------------------------------------------
        # Window
        # --------------------------------------------------

        self.root.title(
            "AGA Railway Route Optimization System"
        )

        self.root.geometry("1250x780")
        self.root.minsize(1050, 680)

        # --------------------------------------------------
        # Colors
        # --------------------------------------------------

        self.bg_color = "#F4F7FB"
        self.sidebar_color = "#102A43"
        self.sidebar_hover = "#1F4E79"

        self.primary_color = "#1976D2"
        self.primary_dark = "#1565C0"

        self.success_color = "#00897B"
        self.success_dark = "#00695C"

        self.dark_color = "#0B1F33"
        self.text_color = "#243B53"
        self.secondary_text = "#627D98"

        self.white = "#FFFFFF"
        self.light_blue = "#EAF3FF"
        self.border_color = "#D9E2EC"

        # --------------------------------------------------
        # Configure window
        # --------------------------------------------------

        self.root.configure(
            bg=self.bg_color
        )

        # --------------------------------------------------
        # Initialize backend
        # --------------------------------------------------

        try:

            self.railway = RailwayNetwork()

            self.optimizer = RailwayOptimizer(
                self.railway
            )

            self.database = RailwayDatabase()

            self.schedule = TrainSchedule()

        except Exception as error:

            messagebox.showerror(
                "Initialization Error",
                f"Could not initialize the railway system.\n\n{error}"
            )

            self.root.destroy()
            return

        # --------------------------------------------------
        # Images
        # --------------------------------------------------

        self.images = {}

        self.load_images()

        # --------------------------------------------------
        # Create GUI
        # --------------------------------------------------

        self.create_layout()

        # --------------------------------------------------
        # Show dashboard
        # --------------------------------------------------

        self.show_dashboard()

    # ======================================================
    # LOAD IMAGES
    # ======================================================

    def load_images(self):

        image_files = {

            "logo": "railway_logo.png",

            "banner": "railway_banner.png",

            "route": "route_optimization.png",

            "station": "railway_station.png",

            "welcome": "welcome.png"

        }

        for name, filename in image_files.items():

            path = os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ),
                "assets",
                filename
            )

            if os.path.exists(path):

                try:

                    image = Image.open(path)

                    self.images[name] = image

                except Exception as error:

                    print(
                        f"Could not load {filename}: {error}"
                    )

    # ======================================================
    # MAIN LAYOUT
    # ======================================================

    def create_layout(self):

        # --------------------------------------------------
        # Sidebar
        # --------------------------------------------------

        self.sidebar = tk.Frame(
            self.root,
            bg=self.sidebar_color,
            width=235
        )

        self.sidebar.pack(
            side="left",
            fill="y"
        )

        self.sidebar.pack_propagate(False)

        # --------------------------------------------------
        # Logo section
        # --------------------------------------------------

        logo_frame = tk.Frame(
            self.sidebar,
            bg=self.sidebar_color
        )

        logo_frame.pack(
            pady=22
        )

        if "logo" in self.images:

            logo = self.images["logo"].copy()

            logo.thumbnail(
                (72, 72)
            )

            self.logo_photo = ImageTk.PhotoImage(
                logo
            )

            tk.Label(
                logo_frame,
                image=self.logo_photo,
                bg=self.sidebar_color
            ).pack()

        else:

            tk.Label(
                logo_frame,
                text="🚆",
                font=("Arial", 38),
                bg=self.sidebar_color,
                fg=self.white
            ).pack()

        tk.Label(
            logo_frame,
            text="AGA RAILWAY",
            font=("Arial", 15, "bold"),
            bg=self.sidebar_color,
            fg=self.white
        ).pack(
            pady=(8, 0)
        )

        tk.Label(
            logo_frame,
            text="Route Optimization",
            font=("Arial", 9),
            bg=self.sidebar_color,
            fg="#BCCCDC"
        ).pack()

        # --------------------------------------------------
        # Navigation title
        # --------------------------------------------------

        tk.Label(
            self.sidebar,
            text="MAIN MENU",
            font=("Arial", 8, "bold"),
            bg=self.sidebar_color,
            fg="#829AB1"
        ).pack(
            anchor="w",
            padx=25,
            pady=(15, 8)
        )

        # --------------------------------------------------
        # Navigation
        # --------------------------------------------------

        self.create_nav_button(
            "⌂   Dashboard",
            self.show_dashboard
        )

        self.create_nav_button(
            "🚆   Route Optimizer",
            self.show_optimizer
        )

        self.create_nav_button(
            "📊   Network Information",
            self.show_network
        )

        self.create_nav_button(
            "ℹ   About Project",
            self.show_about
        )

        # --------------------------------------------------
        # Bottom area
        # --------------------------------------------------

        tk.Frame(
            self.sidebar,
            bg=self.sidebar_color
        ).pack(
            expand=True
        )

        tk.Label(
            self.sidebar,
            text="AGA Railway Route\nOptimization System",
            font=("Arial", 8),
            bg=self.sidebar_color,
            fg="#829AB1",
            justify="center"
        ).pack(
            pady=(5, 3)
        )

        tk.Label(
            self.sidebar,
            text="Academic Project",
            font=("Arial", 8),
            bg=self.sidebar_color,
            fg="#627D98"
        ).pack(
            pady=(0, 20)
        )

        # --------------------------------------------------
        # Main content area
        # --------------------------------------------------

        self.content = tk.Frame(
            self.root,
            bg=self.bg_color
        )

        self.content.pack(
            side="right",
            fill="both",
            expand=True
        )

    # ======================================================
    # NAVIGATION BUTTON
    # ======================================================

    def create_nav_button(
        self,
        text,
        command
    ):

        button = tk.Button(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            font=("Arial", 11, "bold"),
            bg=self.sidebar_color,
            fg=self.white,
            activebackground=self.sidebar_hover,
            activeforeground=self.white,
            relief="flat",
            bd=0,
            padx=25,
            pady=15,
            cursor="hand2"
        )

        button.pack(
            fill="x"
        )

        # Hover effect

        button.bind(
            "<Enter>",
            lambda event: button.configure(
                bg=self.sidebar_hover
            )
        )

        button.bind(
            "<Leave>",
            lambda event: button.configure(
                bg=self.sidebar_color
            )
        )

    # ======================================================
    # CLEAR CONTENT
    # ======================================================

    def clear_content(self):

        for widget in self.content.winfo_children():

            widget.destroy()

    # ======================================================
    # DASHBOARD
    # ======================================================

    def show_dashboard(self):

        self.clear_content()

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        header = tk.Frame(
            self.content,
            bg=self.white,
            height=75
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        tk.Label(
            header,
            text="Dashboard",
            font=("Arial", 23, "bold"),
            bg=self.white,
            fg=self.dark_color
        ).pack(
            side="left",
            padx=30,
            pady=20
        )

        tk.Label(
            header,
            text="Smart Railway Route Planning",
            font=("Arial", 10),
            bg=self.white,
            fg=self.secondary_text
        ).pack(
            side="right",
            padx=30
        )

        # --------------------------------------------------
        # Banner
        # --------------------------------------------------

        if "banner" in self.images:

            banner = self.images["banner"].copy()

            banner.thumbnail(
                (950, 280)
            )

            self.banner_photo = ImageTk.PhotoImage(
                banner
            )

            tk.Label(
                self.content,
                image=self.banner_photo,
                bg=self.bg_color
            ).pack(
                fill="x",
                padx=25,
                pady=20
            )

        else:

            banner_frame = tk.Frame(
                self.content,
                bg=self.primary_color,
                height=180
            )

            banner_frame.pack(
                fill="x",
                padx=25,
                pady=20
            )

            banner_frame.pack_propagate(False)

            tk.Label(
                banner_frame,
                text="AGA RAILWAY ROUTE OPTIMIZATION",
                font=("Arial", 25, "bold"),
                bg=self.primary_color,
                fg=self.white
            ).pack(
                pady=(50, 5)
            )

            tk.Label(
                banner_frame,
                text="Smart • Efficient • Optimized Railway Routing",
                font=("Arial", 11),
                bg=self.primary_color,
                fg=self.white
            ).pack()

        # --------------------------------------------------
        # Welcome card
        # --------------------------------------------------

        welcome = tk.Frame(
            self.content,
            bg=self.white
        )

        welcome.pack(
            fill="x",
            padx=25,
            pady=5
        )

        tk.Label(
            welcome,
            text="Welcome to AGA Railway Route Optimization",
            font=("Arial", 18, "bold"),
            bg=self.white,
            fg=self.dark_color
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 5)
        )

        tk.Label(
            welcome,
            text=(
                "Find efficient railway routes using "
                "graph-based optimization algorithms."
            ),
            font=("Arial", 11),
            bg=self.white,
            fg=self.text_color
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 20)
        )

        # --------------------------------------------------
        # Statistics
        # --------------------------------------------------

        stats = tk.Frame(
            self.content,
            bg=self.bg_color
        )

        stats.pack(
            fill="x",
            padx=25,
            pady=20
        )

        station_count = len(
            self.railway.get_stations()
        )

        route_count = (
            self.railway.get_number_of_connections()
        )

        database_routes = (
            self.database.get_route_count()
        )

        train_count = (
            self.schedule.get_train_count()
        )

        # --------------------------------------------------
        # Statistics cards
        # --------------------------------------------------

        self.create_stat_card(
            stats,
            "🚉",
            "Stations",
            str(station_count),
            0
        )

        self.create_stat_card(
            stats,
            "🚆",
            "Connections",
            str(route_count),
            1
        )

        self.create_stat_card(
            stats,
            "🗄",
            "Database Routes",
            str(database_routes),
            2
        )

        self.create_stat_card(
            stats,
            "🕐",
            "Scheduled Trains",
            str(train_count),
            3
        )

    # ======================================================
    # STAT CARD
    # ======================================================

    def create_stat_card(
        self,
        parent,
        icon,
        title,
        value,
        column
    ):

        card = tk.Frame(
            parent,
            bg=self.white,
            height=105
        )

        card.grid(
            row=0,
            column=column,
            padx=7,
            sticky="nsew"
        )

        card.grid_propagate(False)

        parent.grid_columnconfigure(
            column,
            weight=1
        )

        tk.Label(
            card,
            text=icon,
            font=("Arial", 25),
            bg=self.white
        ).pack(
            side="left",
            padx=15
        )

        text_frame = tk.Frame(
            card,
            bg=self.white
        )

        text_frame.pack(
            side="left",
            pady=15
        )

        tk.Label(
            text_frame,
            text=value,
            font=("Arial", 20, "bold"),
            bg=self.white,
            fg=self.primary_color
        ).pack(
            anchor="w"
        )

        tk.Label(
            text_frame,
            text=title,
            font=("Arial", 9),
            bg=self.white,
            fg=self.secondary_text
        ).pack(
            anchor="w"
        )

    # ======================================================
    # ROUTE OPTIMIZER
    # ======================================================

    def show_optimizer(self):

        self.clear_content()

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        header = tk.Frame(
            self.content,
            bg=self.white
        )

        header.pack(
            fill="x"
        )

        tk.Label(
            header,
            text="Route Optimizer",
            font=("Arial", 22, "bold"),
            bg=self.white,
            fg=self.dark_color
        ).pack(
            anchor="w",
            padx=30,
            pady=(20, 3)
        )

        tk.Label(
            header,
            text="Select source and destination stations",
            font=("Arial", 10),
            bg=self.white,
            fg=self.secondary_text
        ).pack(
            anchor="w",
            padx=30,
            pady=(0, 20)
        )

        # --------------------------------------------------
        # Selection card
        # --------------------------------------------------

        selection = tk.Frame(
            self.content,
            bg=self.white
        )

        selection.pack(
            fill="x",
            padx=30,
            pady=20
        )

        # Source

        tk.Label(
            selection,
            text="SOURCE STATION",
            font=("Arial", 10, "bold"),
            bg=self.white,
            fg="#486581"
        ).grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 5),
            sticky="w"
        )

        # Destination

        tk.Label(
            selection,
            text="DESTINATION STATION",
            font=("Arial", 10, "bold"),
            bg=self.white,
            fg="#486581"
        ).grid(
            row=0,
            column=1,
            padx=20,
            pady=(20, 5),
            sticky="w"
        )

        # Source dropdown

        self.source_combo = ttk.Combobox(
            selection,
            width=38,
            state="readonly",
            font=("Arial", 11)
        )

        self.source_combo.grid(
            row=1,
            column=0,
            padx=20,
            pady=5
        )

        # Destination dropdown

        self.destination_combo = ttk.Combobox(
            selection,
            width=38,
            state="readonly",
            font=("Arial", 11)
        )

        self.destination_combo.grid(
            row=1,
            column=1,
            padx=20,
            pady=5
        )

        # --------------------------------------------------
        # Buttons
        # --------------------------------------------------

        button_frame = tk.Frame(
            selection,
            bg=self.white
        )

        button_frame.grid(
            row=2,
            column=0,
            columnspan=2,
            pady=25
        )

        # Shortest

        shortest_button = tk.Button(
            button_frame,
            text="🚆  FIND SHORTEST ROUTE",
            command=self.find_shortest,
            font=("Arial", 10, "bold"),
            bg=self.primary_color,
            fg=self.white,
            activebackground=self.primary_dark,
            activeforeground=self.white,
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2"
        )

        shortest_button.pack(
            side="left",
            padx=8
        )

        # Fastest

        fastest_button = tk.Button(
            button_frame,
            text="⚡  FIND FASTEST ROUTE",
            command=self.find_fastest,
            font=("Arial", 10, "bold"),
            bg=self.success_color,
            fg=self.white,
            activebackground=self.success_dark,
            activeforeground=self.white,
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2"
        )

        fastest_button.pack(
            side="left",
            padx=8
        )

        # Clear

        clear_button = tk.Button(
            button_frame,
            text="CLEAR",
            command=self.clear_result,
            font=("Arial", 10, "bold"),
            bg="#829AB1",
            fg=self.white,
            activebackground="#627D98",
            activeforeground=self.white,
            relief="flat",
            padx=25,
            pady=12,
            cursor="hand2"
        )

        clear_button.pack(
            side="left",
            padx=8
        )

        # --------------------------------------------------
        # Load stations
        # --------------------------------------------------

        self.load_stations()

        # --------------------------------------------------
        # Result title
        # --------------------------------------------------

        tk.Label(
            self.content,
            text="OPTIMIZATION RESULT",
            font=("Arial", 15, "bold"),
            bg=self.bg_color,
            fg=self.dark_color
        ).pack(
            anchor="w",
            padx=30,
            pady=(5, 5)
        )

        # --------------------------------------------------
        # Result frame
        # --------------------------------------------------

        result_frame = tk.Frame(
            self.content,
            bg=self.white
        )

        result_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=(0, 10)
        )

        scrollbar = tk.Scrollbar(
            result_frame
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.result_text = tk.Text(
            result_frame,
            font=("Consolas", 10),
            bg=self.white,
            fg=self.text_color,
            relief="flat",
            wrap="word",
            padx=20,
            pady=15,
            yscrollcommand=scrollbar.set
        )

        self.result_text.pack(
            fill="both",
            expand=True
        )
        # --------------------------------------------------
# Route Visualization
# --------------------------------------------------

tk.Label(
    self.content,
    text="ROUTE VISUALIZATION",
    font=("Arial", 15, "bold"),
    bg=self.bg_color,
    fg=self.dark_color
).pack(
    anchor="w",
    padx=30,
    pady=(10, 5)
)

self.route_canvas = tk.Canvas(
    self.content,
    height=170,
    bg=self.white,
    highlightthickness=0
)

self.route_canvas.pack(
    fill="x",
    padx=30,
    pady=(0, 15)
)

        scrollbar.config(
            command=self.result_text.yview
        )

        # Initial message

        self.result_text.insert(
            tk.END,
            "\n"
            "       Select source and destination stations "
            "to calculate an optimal route."
        )

        # --------------------------------------------------
        # Status
        # --------------------------------------------------

        self.status_label = tk.Label(
            self.content,
            text="Ready",
            font=("Arial", 9),
            bg=self.bg_color,
            fg=self.secondary_text
        )

        self.status_label.pack(
            anchor="w",
            padx=30,
            pady=(0, 10)
        )

    # ======================================================
    # LOAD STATIONS
    # ======================================================

    def load_stations(self):

        stations = sorted(
            self.railway.get_stations()
        )

        self.source_combo["values"] = stations

        self.destination_combo["values"] = stations

        if len(stations) >= 2:

            self.source_combo.current(0)

            self.destination_combo.current(1)

    # ======================================================
    # GET SELECTED STATIONS
    # ======================================================

    def get_selected_stations(self):

        source = self.source_combo.get()

        destination = self.destination_combo.get()

        if not source or not destination:

            messagebox.showwarning(
                "Selection Required",
                "Please select both source and destination stations."
            )

            return None, None

        if source == destination:

            messagebox.showwarning(
                "Invalid Selection",
                "Source and destination must be different."
            )

            return None, None

        return source, destination

    # ======================================================
    # FIND SHORTEST ROUTE
    # ======================================================

    def find_shortest(self):

        source, destination = (
            self.get_selected_stations()
        )

        if not source:

            return

        self.status_label.config(
            text="Calculating shortest-distance route..."
        )

        self.root.update()

        try:

            result = self.optimizer.shortest_route(
                source,
                destination
            )

            self.display_result(
                result,
                "SHORTEST DISTANCE ROUTE",
                source,
                destination
            )

        except Exception as error:

            messagebox.showerror(
                "Optimization Error",
                str(error)
            )

            self.status_label.config(
                text="Optimization failed."

            )

    # ======================================================
    # FIND FASTEST ROUTE
    # ======================================================

    def find_fastest(self):

        source, destination = (
            self.get_selected_stations()
        )

        if not source:

            return

        self.status_label.config(
            text="Calculating fastest-time route..."
        )

        self.root.update()

        try:

            result = self.optimizer.fastest_route(
                source,
                destination
            )

            self.display_result(
                result,
                "FASTEST TIME ROUTE",
                source,
                destination
            )

        except Exception as error:

            messagebox.showerror(
                "Optimization Error",
                str(error)
            )

            self.status_label.config(
                text="Optimization failed."
            )

    # ======================================================
    # DISPLAY RESULT
    # ======================================================

    def display_result(
        self,
        result,
        title,
        source,
        destination
    ):

        self.result_text.delete(
            "1.0",
            tk.END
        )

        # --------------------------------------------------
        # No route
        # --------------------------------------------------

        if result is None:

            self.result_text.insert(
                tk.END,
                "\n"
            )

            self.result_text.insert(
                tk.END,
                "  NO ROUTE FOUND\n\n"
            )

            self.result_text.insert(
                tk.END,
                "  There is no available route between "
                "the selected stations."
            )

            self.status_label.config(
                text="No route found."
            )

            return

        # --------------------------------------------------
        # Title
        # --------------------------------------------------

        self.result_text.insert(
            tk.END,
            "\n"
        )

        self.result_text.insert(
            tk.END,
            "  " + "=" * 70 + "\n"
        )

        self.result_text.insert(
            tk.END,
            f"  {title}\n"
        )

        self.result_text.insert(
            tk.END,
            "  " + "=" * 70 + "\n\n"
        )

        # --------------------------------------------------
        # Source and destination
        # --------------------------------------------------

        self.result_text.insert(
            tk.END,
            f"  SOURCE       : {source}\n"
        )

        self.result_text.insert(
            tk.END,
            f"  DESTINATION  : {destination}\n\n"
        )

        # --------------------------------------------------
        # Optimized route
        # --------------------------------------------------

        self.result_text.insert(
            tk.END,
            "  OPTIMIZED ROUTE\n"
        )

        self.result_text.insert(
            tk.END,
            "  " + "-" * 70 + "\n\n"
        )

        self.result_text.insert(
            tk.END,
            "  "
            + "  →  ".join(
                result["path"]
            )
            + "\n\n"
        )

        # --------------------------------------------------
        # Route summary
        # --------------------------------------------------

        self.result_text.insert(
            tk.END,
            "  ROUTE SUMMARY\n"
        )

        self.result_text.insert(
            tk.END,
            "  " + "-" * 70 + "\n"
        )

        self.result_text.insert(
            tk.END,
            f"  Total Distance    : "
            f"{result['total_distance']} km\n"
        )

        self.result_text.insert(
            tk.END,
            f"  Total Travel Time : "
            f"{result['total_time']} minutes\n"
        )

        self.result_text.insert(
            tk.END,
            f"  Number of Stops   : "
            f"{len(result['path'])}\n\n"
        )

        # --------------------------------------------------
        # Train connections
        # --------------------------------------------------

        self.result_text.insert(
            tk.END,
            "  TRAIN CONNECTIONS\n"
        )

        self.result_text.insert(
            tk.END,
            "  " + "-" * 70 + "\n"
        )

        for i, connection in enumerate(
            result["connections"],
            start=1
        ):

            self.result_text.insert(
                tk.END,
                f"\n  CONNECTION {i}\n"
            )

            self.result_text.insert(
                tk.END,
                "  " + "-" * 35 + "\n"
            )

            self.result_text.insert(
                tk.END,
                f"  From        : "
                f"{connection['source']}\n"
            )

            self.result_text.insert(
                tk.END,
                f"  To          : "
                f"{connection['destination']}\n"
            )

            self.result_text.insert(
                tk.END,
                f"  Train       : "
                f"{connection['train_name']}\n"
            )

            self.result_text.insert(
                tk.END,
                f"  Train No.   : "
                f"{connection['train_number']}\n"
            )

            self.result_text.insert(
                tk.END,
                f"  Distance    : "
                f"{connection['distance']} km\n"
            )

            self.result_text.insert(
                tk.END,
                f"  Travel Time : "
                f"{connection['travel_time']} minutes\n"
            )

            self.result_text.insert(
                tk.END,
                f"  Departure   : "
                f"{connection['departure']}\n"
            )

            self.result_text.insert(
                tk.END,
                f"  Arrival     : "
                f"{connection['arrival']}\n"
            )

            # --------------------------------------------------
            # Schedule information
            # --------------------------------------------------

            train_number = str(
                connection["train_number"]
            ).strip()

            train_schedule = (
                self.schedule.get_train_schedule(
                    train_number
                )
            )

            if not train_schedule.empty:

                self.result_text.insert(
                    tk.END,
                    "\n  SCHEDULE INFORMATION\n"
                )

                self.result_text.insert(
                    tk.END,
                    "  " + "-" * 35 + "\n"
                )

                self.result_text.insert(
                    tk.END,
                    f"  Scheduled Stops: "
                    f"{len(train_schedule)}\n"
                )

                stops = (
                    train_schedule[
                        "station_name"
                    ]
                    .dropna()
                    .astype(str)
                    .tolist()
                )

                if stops:

                    self.result_text.insert(
                        tk.END,
                        "  Route Stops:\n"
                    )

                    display_stops = stops[:10]

                    self.result_text.insert(
                        tk.END,
                        "  "
                        + " → ".join(
                            display_stops
                        )
                        + "\n"
                    )

                    if len(stops) > 10:

                        self.result_text.insert(
                            tk.END,
                            f"  ... and "
                            f"{len(stops) - 10} "
                            f"more stops\n"
                        )

        # --------------------------------------------------
        # Save result
        # --------------------------------------------------

        try:

            self.database.save_result(
                source=source,
                destination=destination,
                optimization_type=title,
                route=" -> ".join(
                    result["path"]
                ),
                total_distance=result[
                    "total_distance"
                ],
                total_time=result[
                    "total_time"
                ]
            )

            self.status_label.config(
                text="✓ Route calculated and result saved to database."
            )

        except Exception as error:

            self.status_label.config(
                text="✓ Route calculated. Database save unavailable."
            )

            print(
                "Database save error:",
                error
            )

    # ======================================================
    # CLEAR RESULT
    # ======================================================

    def clear_result(self):

        self.result_text.delete(
            "1.0",
            tk.END
        )

        self.result_text.insert(
            tk.END,
            "\n"
            "       Select source and destination stations "
            "to calculate an optimal route."
        )

        self.status_label.config(
            text="Ready"
        )

    # ======================================================
    # NETWORK INFORMATION
    # ======================================================

    def show_network(self):

        self.clear_content()

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        tk.Label(
            self.content,
            text="Railway Network Information",
            font=("Arial", 22, "bold"),
            bg=self.bg_color,
            fg=self.dark_color
        ).pack(
            anchor="w",
            padx=30,
            pady=(30, 5)
        )

        tk.Label(
            self.content,
            text="Overview of the railway network used by the system",
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.secondary_text
        ).pack(
            anchor="w",
            padx=30,
            pady=(0, 20)
        )

        # --------------------------------------------------
        # Information card
        # --------------------------------------------------

        info = tk.Frame(
            self.content,
            bg=self.white
        )

        info.pack(
            fill="x",
            padx=30,
            pady=10
        )

        station_count = len(
            self.railway.get_stations()
        )

        connection_count = (
            self.railway.get_number_of_connections()
        )

        database_routes = (
            self.database.get_route_count()
        )

        train_count = (
            self.schedule.get_train_count()
        )

        information = [

            ("Total Stations", station_count),

            ("Railway Connections", connection_count),

            ("Database Routes", database_routes),

            ("Scheduled Trains", train_count)

        ]

        for i, (label, value) in enumerate(
            information
        ):

            tk.Label(
                info,
                text=label,
                font=("Arial", 12, "bold"),
                bg=self.white,
                fg=self.text_color
            ).grid(
                row=i,
                column=0,
                padx=30,
                pady=14,
                sticky="w"
            )

            tk.Label(
                info,
                text=str(value),
                font=("Arial", 14, "bold"),
                bg=self.white,
                fg=self.primary_color
            ).grid(
                row=i,
                column=1,
                padx=30,
                pady=14,
                sticky="w"
            )

        # --------------------------------------------------
        # Network image
        # --------------------------------------------------

        if "route" in self.images:

            image = self.images["route"].copy()

            image.thumbnail(
                (650, 350)
            )

            self.network_photo = ImageTk.PhotoImage(
                image
            )

            tk.Label(
                self.content,
                image=self.network_photo,
                bg=self.bg_color
            ).pack(
                pady=25
            )

        else:

            tk.Label(
                self.content,
                text="Railway Network",
                font=("Arial", 20, "bold"),
                bg=self.bg_color,
                fg=self.primary_color
            ).pack(
                pady=40
            )

    # ======================================================
    # ABOUT PROJECT
    # ======================================================

    def show_about(self):

        self.clear_content()

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        tk.Label(
            self.content,
            text="About the Project",
            font=("Arial", 22, "bold"),
            bg=self.bg_color,
            fg=self.dark_color
        ).pack(
            anchor="w",
            padx=30,
            pady=(30, 5)
        )

        tk.Label(
            self.content,
            text="AGA Railway Route Optimization System",
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.secondary_text
        ).pack(
            anchor="w",
            padx=30,
            pady=(0, 20)
        )

        # --------------------------------------------------
        # About card
        # --------------------------------------------------

        about = tk.Frame(
            self.content,
            bg=self.white
        )

        about.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=10
        )

        tk.Label(
            about,
            text="AGA Railway Route Optimization System",
            font=("Arial", 20, "bold"),
            bg=self.white,
            fg=self.primary_color
        ).pack(
            pady=(30, 10)
        )

        description = (
            "A graph-based railway route optimization system "
            "designed to identify efficient routes between "
            "railway stations using railway network data."
        )

        tk.Label(
            about,
            text=description,
            font=("Arial", 12),
            bg=self.white,
            fg=self.text_color,
            wraplength=750,
            justify="center"
        ).pack(
            pady=10
        )

        # --------------------------------------------------
        # Features
        # --------------------------------------------------

        features = (
            "KEY FEATURES\n\n"
            "• Railway network modelling using graphs\n"
            "• Shortest-distance route optimization\n"
            "• Fastest-time route optimization\n"
            "• Railway schedule integration\n"
            "• SQLite database management\n"
            "• Railway network analysis\n"
            "• Interactive graphical user interface"
        )

        tk.Label(
            about,
            text=features,
            font=("Arial", 11),
            bg=self.white,
            fg=self.text_color,
            justify="left"
        ).pack(
            pady=20
        )

        # --------------------------------------------------
        # Station image
        # --------------------------------------------------

        if "station" in self.images:

            image = self.images["station"].copy()

            image.thumbnail(
                (550, 230)
            )

            self.about_photo = ImageTk.PhotoImage(
                image
            )

            tk.Label(
                about,
                image=self.about_photo,
                bg=self.white
            ).pack(
                pady=10
            )

        # --------------------------------------------------
        # Technology
        # --------------------------------------------------

        tk.Label(
            about,
            text="Python  •  NetworkX  •  Pandas  •  SQLite  •  Tkinter",
            font=("Arial", 9, "bold"),
            bg=self.white,
            fg=self.secondary_text
        ).pack(
            pady=15
        )


# ==========================================================
# START APPLICATION
# ==========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = RailwayGUI(
        root
    )

    root.mainloop()