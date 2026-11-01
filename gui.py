import tkinter as tk
from tkinter import ttk, messagebox

import networkx as nx
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from railway_network import RailwayNetwork
from optimization import RailwayOptimizer
from database import RailwayDatabase


# ==================================================================
# LIVE AUTOCOMPLETE ENTRY
# A text box with its own popup suggestion list underneath it,
# like a website search field. Every keystroke updates the list to
# only stations that START WITH what's typed so far ("k" -> all
# K-stations, "ka" -> narrows to KA-stations, and so on). Typing
# never loses focus, so you can keep entering letters continuously
# while the suggestions refresh live. Clicking a suggestion (or
# pressing Down then Enter) fills the box with that station.
# ==================================================================

class AutocompleteEntry(tk.Frame):

    def __init__(self, parent, values, width=38, bg="#FFFFFF"):

        super().__init__(parent, bg=bg)

        self.values = sorted(
            values,
            key=str.lower
        )

        self.var = tk.StringVar()

        self.entry = ttk.Entry(
            self,
            textvariable=self.var,
            width=width
        )

        self.entry.pack(
            fill="both",
            expand=True
        )

        self.popup = None
        self.listbox = None

        self.var.trace_add(
            "write",
            self._on_change
        )

        self.entry.bind(
            "<Down>",
            self._focus_listbox
        )

        self.entry.bind(
            "<Escape>",
            lambda event: self._hide_popup()
        )

        self.bind_all(
            "<Button-1>",
            self._on_global_click,
            add="+"
        )

    # --------------------------------------------------------
    # FILTERING
    # --------------------------------------------------------

    def _on_change(self, *args):

        typed = self.var.get().strip().lower()

        if not typed:

            self._hide_popup()

            return

        matches = [
            station
            for station in self.values
            if station.lower().startswith(typed)
        ]

        if matches:

            self._show_popup(matches)

        else:

            self._hide_popup()

    # --------------------------------------------------------
    # POPUP LIST
    # --------------------------------------------------------

    def _show_popup(self, matches):

        if self.popup is None:

            self.popup = tk.Toplevel(self)

            self.popup.wm_overrideredirect(True)

            self.popup.attributes(
                "-topmost",
                True
            )

            self.listbox = tk.Listbox(
                self.popup,
                font=("Segoe UI", 10),
                activestyle="none",
                highlightthickness=1,
                highlightbackground="#D9E2EC",
                bd=0,
                relief="flat"
            )

            self.listbox.pack(
                fill="both",
                expand=True
            )

            self.listbox.bind(
                "<ButtonRelease-1>",
                self._on_listbox_select
            )

            self.listbox.bind(
                "<Return>",
                self._on_listbox_select
            )

        self.listbox.delete(
            0,
            tk.END
        )

        for station in matches[:15]:

            self.listbox.insert(
                tk.END,
                station
            )

        visible_rows = min(
            len(matches),
            8
        )

        self.listbox.config(
            height=visible_rows
        )

        x = self.entry.winfo_rootx()

        y = (
            self.entry.winfo_rooty()
            + self.entry.winfo_height()
        )

        width = self.entry.winfo_width()

        self.popup.geometry(
            f"{width}x{visible_rows * 20}+{x}+{y}"
        )

        self.popup.deiconify()

        self.popup.lift()

    def _hide_popup(self):

        if self.popup is not None:

            self.popup.withdraw()

    def _focus_listbox(self, event):

        if (
            self.popup is not None
            and self.popup.winfo_viewable()
            and self.listbox.size() > 0
        ):

            self.listbox.focus_set()

            self.listbox.selection_set(0)

            self.listbox.activate(0)

        return "break"

    def _on_listbox_select(self, event):

        if self.listbox.curselection():

            value = self.listbox.get(
                self.listbox.curselection()
            )

        else:

            value = self.listbox.get(
                tk.ACTIVE
            )

        self.var.set(
            value
        )

        self.entry.icursor(
            tk.END
        )

        self._hide_popup()

        self.entry.focus_set()

    def _on_global_click(self, event):

        widget = event.widget

        if widget == self.entry:

            return

        if (
            self.popup is not None
            and widget.winfo_toplevel() == self.popup
        ):

            return

        self._hide_popup()

    # --------------------------------------------------------
    # PUBLIC API (matches what a Combobox call site needs)
    # --------------------------------------------------------

    def get(self):

        return self.var.get()

    def set(self, value):

        self.var.set(
            value
        )


class RailwayGUI:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Railway Network Robustness Analyzer"
        )

        self.root.geometry(
            "1400x850"
        )

        self.root.minsize(
            1100,
            700
        )

        self.root.configure(
            bg="#F4F7FB"
        )

        # ======================================================
        # COLORS
        # ======================================================

        self.bg = "#F4F7FB"
        self.sidebar = "#102A43"
        self.sidebar_hover = "#1F4E79"
        self.primary = "#1976D2"
        self.success = "#00897B"
        self.danger = "#C62828"
        self.warning = "#F57C00"
        self.dark = "#102A43"
        self.text = "#243B53"
        self.muted = "#627D98"
        self.white = "#FFFFFF"
        self.border = "#D9E2EC"
        self.light = "#FBFCFE"

        # ======================================================
        # ROBUSTNESS STORAGE
        # ======================================================

        self.robustness_report = None
        self.robustness_source = None
        self.robustness_destination = None
        self.selected_source = None
        self.selected_destination = None

        self.graph_canvas = None
        self.graph_figure = None

        # ======================================================
        # LOAD RAILWAY NETWORK
        # ======================================================

        try:

            self.railway = RailwayNetwork()

            self.optimizer = RailwayOptimizer(
                self.railway
            )

            self.stations = sorted(
                self.railway.get_stations()
            )

        except Exception as error:

            messagebox.showerror(
                "Startup Error",
                "Unable to initialize railway network.\n\n"
                + str(error)
            )

            self.root.destroy()

            return

        # ======================================================
        # CREATE GUI
        # ======================================================

        self.create_layout()

        self.show_dashboard()

    # ==========================================================
    # MAIN LAYOUT
    # ==========================================================

    def create_layout(self):

        self.create_sidebar()

        self.create_main_area()

    # ==========================================================
    # SIDEBAR
    # ==========================================================

    def create_sidebar(self):

        self.sidebar_frame = tk.Frame(
            self.root,
            bg=self.sidebar,
            width=250
        )

        self.sidebar_frame.pack(
            side="left",
            fill="y"
        )

        self.sidebar_frame.pack_propagate(
            False
        )

        tk.Label(
            self.sidebar_frame,
            text="🚆",
            font=("Segoe UI Emoji", 38),
            bg=self.sidebar,
            fg=self.white
        ).pack(
            pady=(25, 5)
        )

        tk.Label(
            self.sidebar_frame,
            text="INDIAN RAILWAY",
            font=("Segoe UI", 16, "bold"),
            bg=self.sidebar,
            fg=self.white
        ).pack()

        tk.Label(
            self.sidebar_frame,
            text="Network Robustness Analyzer",
            font=("Segoe UI", 9),
            bg=self.sidebar,
            fg="#BCCCDC"
        ).pack(
            pady=(2, 25)
        )

        tk.Label(
            self.sidebar_frame,
            text="MAIN MENU",
            font=("Segoe UI", 8, "bold"),
            bg=self.sidebar,
            fg="#829AB1"
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 8)
        )

        self.nav_button(
            "⌂   Dashboard",
            self.show_dashboard
        )

        self.nav_button(
            "🛡   Robustness Analysis",
            self.show_robustness
        )

        self.nav_button(
            "🎯   Path Comparison",
            self.show_shortest_paths
        )

        self.nav_button(
            "🚉   Network Information",
            self.show_network
        )

        self.nav_button(
            "📊   Dataset Analysis",
            self.show_analysis
        )

        self.nav_button(
            "ℹ   About Project",
            self.show_about
        )

        tk.Frame(
            self.sidebar_frame,
            bg=self.sidebar
        ).pack(
            expand=True
        )

        tk.Label(
            self.sidebar_frame,
            text="Advanced Graph Algorithms",
            font=("Segoe UI", 8),
            bg=self.sidebar,
            fg="#829AB1"
        ).pack(
            pady=(0, 3)
        )

        tk.Label(
            self.sidebar_frame,
            text="Academic Project",
            font=("Segoe UI", 8),
            bg=self.sidebar,
            fg="#627D98"
        ).pack(
            pady=(0, 20)
        )

    # ==========================================================
    # NAVIGATION BUTTON
    # ==========================================================

    def nav_button(
        self,
        text,
        command
    ):

        button = tk.Button(
            self.sidebar_frame,
            text=text,
            command=command,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
            bg=self.sidebar,
            fg=self.white,
            activebackground=self.sidebar_hover,
            activeforeground=self.white,
            relief="flat",
            bd=0,
            padx=25,
            pady=13,
            cursor="hand2"
        )

        button.pack(
            fill="x"
        )

        button.bind(
            "<Enter>",
            lambda event:
            button.configure(
                bg=self.sidebar_hover
            )
        )

        button.bind(
            "<Leave>",
            lambda event:
            button.configure(
                bg=self.sidebar
            )
        )

    # ==========================================================
    # MAIN SCROLLABLE AREA
    # ==========================================================

    def create_main_area(self):

        self.main_container = tk.Frame(
            self.root,
            bg=self.bg
        )

        self.main_container.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.main_canvas = tk.Canvas(
            self.main_container,
            bg=self.bg,
            highlightthickness=0
        )

        self.vertical_scrollbar = ttk.Scrollbar(
            self.main_container,
            orient="vertical",
            command=self.main_canvas.yview
        )

        self.main_canvas.configure(
            yscrollcommand=self.vertical_scrollbar.set
        )

        self.vertical_scrollbar.pack(
            side="right",
            fill="y"
        )

        self.main_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.content = tk.Frame(
            self.main_canvas,
            bg=self.bg
        )

        self.canvas_window = self.main_canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw"
        )

        self.content.bind(
            "<Configure>",
            self.update_scroll_region
        )

        self.main_canvas.bind(
            "<Configure>",
            self.resize_content
        )

        self.main_canvas.bind_all(
            "<MouseWheel>",
            self.mousewheel
        )

    # ==========================================================
    # SCROLL
    # ==========================================================

    def update_scroll_region(
        self,
        event=None
    ):

        self.main_canvas.configure(
            scrollregion=self.main_canvas.bbox(
                "all"
            )
        )

    def resize_content(
        self,
        event
    ):

        self.main_canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    def mousewheel(
        self,
        event
    ):

        try:

            self.main_canvas.yview_scroll(
                int(
                    -1 *
                    (event.delta / 120)
                ),
                "units"
            )

        except Exception:

            pass

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear_content(self):

        for widget in self.content.winfo_children():

            widget.destroy()

        self.main_canvas.yview_moveto(
            0
        )

    # ==========================================================
    # HEADER
    # ==========================================================

    def header(
        self,
        title,
        subtitle=""
    ):

        tk.Label(
            self.content,
            text=title,
            font=("Segoe UI", 27, "bold"),
            bg=self.bg,
            fg=self.dark
        ).pack(
            anchor="w",
            padx=35,
            pady=(25, 3)
        )

        if subtitle:

            tk.Label(
                self.content,
                text=subtitle,
                font=("Segoe UI", 11),
                bg=self.bg,
                fg=self.muted
            ).pack(
                anchor="w",
                padx=35,
                pady=(0, 15)
            )

    # ==========================================================
    # CARD
    # ==========================================================

    def create_card(self):

        frame = tk.Frame(
            self.content,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        frame.pack(
            fill="x",
            padx=30,
            pady=8
        )

        return frame

    # ==========================================================
    # DASHBOARD
    # ==========================================================

    def show_dashboard(self):

        self.clear_content()

        self.header(
            "Dashboard",
            "AGA Railway Network Robustness Analyzer"
        )

        banner = tk.Frame(
            self.content,
            bg=self.primary,
            height=180
        )

        banner.pack(
            fill="x",
            padx=30,
            pady=10
        )

        banner.pack_propagate(
            False
        )

        tk.Label(
            banner,
            text="RAILWAY NETWORK ROBUSTNESS",
            font=("Segoe UI", 25, "bold"),
            bg=self.primary,
            fg=self.white
        ).pack(
            pady=(42, 4)
        )

        tk.Label(
            banner,
            text=(
                "Connectivity • Critical Components • "
                "Network Flow • Bottlenecks"
            ),
            font=("Segoe UI", 11),
            bg=self.primary,
            fg=self.white
        ).pack()

        stats = tk.Frame(
            self.content,
            bg=self.bg
        )

        stats.pack(
            fill="x",
            padx=30,
            pady=18
        )

        try:

            station_count = (
                self.railway.get_number_of_stations()
            )

        except Exception:

            station_count = len(
                self.stations
            )

        try:

            connection_count = (
                self.railway.get_number_of_connections()
            )

        except Exception:

            connection_count = 0

        values = [

            (
                "🚉",
                station_count,
                "Stations"
            ),

            (
                "🛤",
                connection_count,
                "Railway Connections"
            ),

            (
                "🔗",
                "Graph",
                "Network Model"
            ),

            (
                "⚙",
                "6",
                "AGA Concepts"
            )

        ]

        for i, (
            icon,
            value,
            title
        ) in enumerate(values):

            stats.grid_columnconfigure(
                i,
                weight=1
            )

            frame = tk.Frame(
                stats,
                bg=self.white,
                height=110,
                highlightbackground=self.border,
                highlightthickness=1
            )

            frame.grid(
                row=0,
                column=i,
                padx=7,
                sticky="nsew"
            )

            frame.grid_propagate(
                False
            )

            tk.Label(
                frame,
                text=icon,
                font=("Segoe UI Emoji", 23),
                bg=self.white
            ).pack(
                side="left",
                padx=15
            )

            inner = tk.Frame(
                frame,
                bg=self.white
            )

            inner.pack(
                side="left",
                pady=20
            )

            tk.Label(
                inner,
                text=str(value),
                font=("Segoe UI", 21, "bold"),
                bg=self.white,
                fg=self.primary
            ).pack(
                anchor="w"
            )

            tk.Label(
                inner,
                text=title,
                font=("Segoe UI", 9),
                bg=self.white,
                fg=self.muted
            ).pack(
                anchor="w"
            )

        card = self.create_card()

        tk.Label(
            card,
            text="Complete Robustness Analysis",
            font=("Segoe UI", 17, "bold"),
            bg=self.white,
            fg=self.dark
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 8)
        )

        tk.Label(
            card,
            text=(
                "Select two railway stations and perform a "
                "source-to-destination robustness analysis using "
                "six Advanced Graph Algorithm concepts."
            ),
            font=("Segoe UI", 11),
            bg=self.white,
            fg=self.text,
            justify="left",
            wraplength=1050
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 18)
        )

        tk.Button(
            card,
            text="OPEN ROBUSTNESS CHECK",
            command=self.show_robustness,
            font=("Segoe UI", 10, "bold"),
            bg=self.primary,
            fg=self.white,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 12)
        )

        tk.Button(
            card,
            text="FIND OPTIMAL PATH",
            command=self.show_shortest_paths,
            font=("Segoe UI", 10, "bold"),
            bg=self.success,
            fg=self.white,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 22)
        )

        self.update_scroll_region()

    # ==========================================================
    # ROBUSTNESS CHECK
    # ==========================================================

    def show_robustness(self, source=None, destination=None, auto_run=False):
        """Open the Robustness Analysis page directly (no intermediate page)."""
        self._show_robustness_results(source, destination, auto_run)

    def _show_robustness_results(self, selected_source=None, selected_destination=None, auto_run=False):

        self.clear_content()

        self.header(
            "Robustness Analysis",
            "Connectivity and robustness analysis results with their graphs"
        )

        # Button to jump to the Shortest & Optimal Paths page with the same stations.
        navigation = self.create_card()
        nav_row = tk.Frame(navigation, bg=self.white)
        nav_row.pack(fill="x", padx=20, pady=16)
        tk.Label(nav_row, text="Currently on: Robustness Analysis",
                 font=("Segoe UI", 10, "bold"), bg=self.white, fg=self.muted).pack(side="left")
        tk.Button(nav_row, text="SHORTEST & OPTIMAL PATHS  →",
                  command=lambda: go_to_paths(),
                  font=("Segoe UI", 10, "bold"), bg=self.success, fg=self.white,
                  activebackground=self.sidebar_hover, activeforeground=self.white,
                  relief="flat", padx=16, pady=10, cursor="hand2").pack(side="right")

        # ======================================================
        # SOURCE / DESTINATION CARD
        # ======================================================

        selection_card = self.create_card()

        tk.Label(
            selection_card,
            text="SELECT SOURCE AND DESTINATION",
            font=("Segoe UI", 11, "bold"),
            bg=self.white,
            fg=self.dark
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 10)
        )

        controls = tk.Frame(
            selection_card,
            bg=self.white
        )

        controls.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        tk.Label(
            controls,
            text="Source Station",
            font=("Segoe UI", 10, "bold"),
            bg=self.white,
            fg=self.muted
        ).grid(
            row=0,
            column=0,
            padx=8,
            sticky="w"
        )

        tk.Label(
            controls,
            text="Destination Station",
            font=("Segoe UI", 10, "bold"),
            bg=self.white,
            fg=self.muted
        ).grid(
            row=0,
            column=1,
            padx=8,
            sticky="w"
        )

        source_combo = AutocompleteEntry(
            controls,
            self.stations,
            width=38,
            bg=self.white
        )

        source_combo.grid(
            row=1,
            column=0,
            padx=8,
            pady=6
        )

        destination_combo = AutocompleteEntry(
            controls,
            self.stations,
            width=38,
            bg=self.white
        )

        destination_combo.grid(
            row=1,
            column=1,
            padx=8,
            pady=6
        )

        selected_source = selected_source or self.selected_source
        selected_destination = selected_destination or self.selected_destination
        if selected_source in self.stations and selected_destination in self.stations:
            source_combo.set(selected_source)
            destination_combo.set(selected_destination)
        elif len(self.stations) >= 2:
            source_combo.set(self.stations[0])
            destination_combo.set(self.stations[1])

        tk.Button(
            controls,
            text="RUN ROBUSTNESS CHECK",
            command=lambda:
            run_robustness(),
            font=("Segoe UI", 10, "bold"),
            bg=self.success,
            fg=self.white,
            relief="flat",
            padx=22,
            pady=10,
            cursor="hand2"
        ).grid(
            row=1,
            column=2,
            padx=20,
            pady=6
        )


        # ======================================================
        # ANALYSIS RESULT
        # ======================================================

        analysis_card = self.create_card()

        tk.Label(
            analysis_card,
            text="Analysis Result",
            font=("Segoe UI", 17, "bold"),
            bg=self.white,
            fg=self.dark
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 8)
        )

        tk.Label(
            analysis_card,
            text="Select a robustness analysis result:",
            font=("Segoe UI", 10),
            bg=self.white,
            fg=self.muted
        ).pack(
            anchor="w",
            padx=25
        )

        result_combo = ttk.Combobox(
            analysis_card,
            state="readonly",
            width=55,
            values=[
                "All Algorithms (Combined)",
                "Cuts and Connectivity",
                "k-Connected Graph",
                "Network Flow",
                "Ford-Fulkerson Labeling",
                "Max-Flow Min-Cut",
                "Menger's Theorem"
            ]
        )

        result_combo.pack(
            anchor="w",
            padx=25,
            pady=8
        )

        result_frame = tk.Frame(
            analysis_card,
            bg=self.white
        )

        result_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(5, 20)
        )

        result_scrollbar = ttk.Scrollbar(
            result_frame,
            orient="vertical"
        )

        result_output = tk.Text(
            result_frame,
            height=18,
            font=("Consolas", 10),
            bg=self.light,
            fg=self.text,
            relief="flat",
            wrap="word",
            padx=15,
            pady=15,
            yscrollcommand=result_scrollbar.set
        )

        result_scrollbar.config(
            command=result_output.yview
        )

        result_scrollbar.pack(
            side="right",
            fill="y"
        )

        result_output.pack(
            side="left",
            fill="both",
            expand=True
        )

        result_output.insert(
            "1.0",
            "Run the robustness check first.\n\n"
            "Then select one of the AGA concepts "
            "from the dropdown above, or choose "
            "'All Algorithms (Combined)' to see every "
            "result in one go."
        )

        result_output.config(
            state="disabled"
        )


        # ======================================================
        # GRAPH
        # ======================================================

        graph_card = self.create_card()

        tk.Label(
            graph_card,
            text="Graph",
            font=("Segoe UI", 17, "bold"),
            bg=self.white,
            fg=self.dark
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 8)
        )

        tk.Label(
            graph_card,
            text=(
                "Select a graph generated from the robustness "
                "analysis. Shortest and fastest routes are not "
                "used for this visualization."
            ),
            font=("Segoe UI", 10),
            bg=self.white,
            fg=self.muted,
            wraplength=1000
        ).pack(
            anchor="w",
            padx=25
        )

        graph_combo = ttk.Combobox(
            graph_card,
            state="readonly",
            width=55,
            values=[
                "Robustness Graph",
                "Menger Independent Paths",
                "Critical Components"
            ]
        )

        graph_combo.pack(
            anchor="w",
            padx=25,
            pady=8
        )

        graph_frame = tk.Frame(
            graph_card,
            bg=self.white,
            height=550
        )

        graph_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(5, 20)
        )

        graph_frame.pack_propagate(
            False
        )

        tk.Label(
            graph_frame,
            text=(
                "Run the robustness check first,\n"
                "then select a graph."
            ),
            font=("Segoe UI", 12),
            bg=self.white,
            fg=self.muted
        ).pack(
            expand=True
        )

        # ======================================================
        # DISPLAY ANALYSIS RESULT
        # ======================================================

        def display_result():

            report = self.robustness_report

            if report is None:

                return

            selected = result_combo.get()

            if not selected:

                return

            source = self.robustness_source

            destination = self.robustness_destination

            result_output.config(
                state="normal"
            )

            result_output.delete(
                "1.0",
                tk.END
            )

            result_output.insert(
                tk.END,
                "=" * 70 + "\n"
            )

            result_output.insert(
                tk.END,
                "ANALYSIS RESULT\n"
            )

            result_output.insert(
                tk.END,
                "=" * 70 + "\n\n"
            )

            result_output.insert(
                tk.END,
                f"Source      : {source}\n"
            )

            result_output.insert(
                tk.END,
                f"Destination : {destination}\n\n"
            )

            # ==================================================
            # SECTION WRITERS
            # ==================================================

            def write_cuts():

                data = report[
                    "cuts"
                ]

                result_output.insert(
                    tk.END,
                    "CUTS AND CONNECTIVITY\n"
                )

                result_output.insert(
                    tk.END,
                    "-" * 70 + "\n\n"
                )

                result_output.insert(
                    tk.END,
                    f"Connected : "
                    f"{data['connected']}\n\n"
                )

                critical_stations = data[
                    "critical_stations"
                ]

                critical_tracks = data[
                    "critical_tracks"
                ]

                result_output.insert(
                    tk.END,
                    f"Critical stations : "
                    f"{len(critical_stations)}\n"
                )

                if critical_stations:

                    for station in critical_stations:

                        result_output.insert(
                            tk.END,
                            f"  • {station}\n"
                        )

                else:

                    result_output.insert(
                        tk.END,
                        "  None\n"
                    )

                result_output.insert(
                    tk.END,
                    f"\nCritical tracks : "
                    f"{len(critical_tracks)}\n"
                )

                if critical_tracks:

                    for track in critical_tracks:

                        result_output.insert(
                            tk.END,
                            f"  • {track[0]} ↔ "
                            f"{track[1]}\n"
                        )

                else:

                    result_output.insert(
                        tk.END,
                        "  None\n"
                    )

            def write_k():

                data = report[
                    "k_connectivity"
                ]

                result_output.insert(
                    tk.END,
                    "k-CONNECTED GRAPH\n"
                )

                result_output.insert(
                    tk.END,
                    "-" * 70 + "\n\n"
                )

                result_output.insert(
                    tk.END,
                    f"Vertex connectivity (k) : "
                    f"{data['k']}\n\n"
                )

                result_output.insert(
                    tk.END,
                    f"Connected : "
                    f"{data['connected']}\n\n"
                )

                if data["connected"]:

                    result_output.insert(
                        tk.END,
                        "The selected source and destination "
                        "are connected with the calculated "
                        "vertex connectivity value.\n"
                    )

                else:

                    result_output.insert(
                        tk.END,
                        "The selected stations are not connected.\n"
                    )

            def write_flow():

                data = report[
                    "ford_fulkerson"
                ]

                result_output.insert(
                    tk.END,
                    "NETWORK FLOW\n"
                )

                result_output.insert(
                    tk.END,
                    "-" * 70 + "\n\n"
                )

                result_output.insert(
                    tk.END,
                    "Each railway connection is represented "
                    "as a unit-capacity flow connection.\n\n"
                )

                result_output.insert(
                    tk.END,
                    f"Maximum network flow : "
                    f"{data['max_flow']}\n"
                )

                result_output.insert(
                    tk.END,
                    f"Augmenting paths : "
                    f"{len(data['augmenting_paths'])}\n"
                )

            def write_ff_labeling():

                data = report[
                    "ford_fulkerson"
                ]

                result_output.insert(
                    tk.END,
                    "FORD-FULKERSON LABELING ALGORITHM\n"
                )

                result_output.insert(
                    tk.END,
                    "-" * 70 + "\n\n"
                )

                result_output.insert(
                    tk.END,
                    f"Maximum flow : "
                    f"{data['max_flow']}\n\n"
                )

                paths = data[
                    "augmenting_paths"
                ]

                result_output.insert(
                    tk.END,
                    f"Augmenting paths found : "
                    f"{len(paths)}\n\n"
                )

                for i, item in enumerate(
                    paths,
                    start=1
                ):

                    result_output.insert(
                        tk.END,
                        f"Augmenting Path {i}\n"
                    )

                    result_output.insert(
                        tk.END,
                        "-" * 30 + "\n"
                    )

                    result_output.insert(
                        tk.END,
                        "Path : "
                    )

                    result_output.insert(
                        tk.END,
                        " → ".join(
                            map(
                                str,
                                item["path"]
                            )
                        )
                        + "\n"
                    )

                    result_output.insert(
                        tk.END,
                        f"Flow added : "
                        f"{item['flow']}\n\n"
                    )

            def write_max_flow_min_cut():

                data = report[
                    "max_flow_min_cut"
                ]

                result_output.insert(
                    tk.END,
                    "MAX-FLOW MIN-CUT THEOREM\n"
                )

                result_output.insert(
                    tk.END,
                    "-" * 70 + "\n\n"
                )

                result_output.insert(
                    tk.END,
                    f"Maximum flow : "
                    f"{data['max_flow']}\n"
                )

                result_output.insert(
                    tk.END,
                    f"Minimum cut : "
                    f"{data['min_cut']}\n\n"
                )

                if data[
                    "theorem_verified"
                ]:

                    result_output.insert(
                        tk.END,
                        "THEOREM VERIFIED\n"
                    )

                    result_output.insert(
                        tk.END,
                        "Maximum Flow = Minimum Cut\n\n"
                    )

                else:

                    result_output.insert(
                        tk.END,
                        "The equality could not be verified.\n\n"
                    )

                result_output.insert(
                    tk.END,
                    "MINIMUM CUT EDGES\n"
                )

                result_output.insert(
                    tk.END,
                    "-" * 70 + "\n"
                )

                cut_edges = data[
                    "cut_edges"
                ]

                if cut_edges:

                    for edge in cut_edges:

                        result_output.insert(
                            tk.END,
                            f"{edge['source']} → "
                            f"{edge['destination']} "
                            f"(capacity = "
                            f"{edge['capacity']})\n"
                        )

                else:

                    result_output.insert(
                        tk.END,
                        "None\n"
                    )

            def write_menger():

                data = report[
                    "menger"
                ]

                result_output.insert(
                    tk.END,
                    "MENGER'S THEOREM\n"
                )

                result_output.insert(
                    tk.END,
                    "-" * 70 + "\n\n"
                )

                result_output.insert(
                    tk.END,
                    f"Edge connectivity : "
                    f"{data['edge_connectivity']}\n"
                )

                result_output.insert(
                    tk.END,
                    f"Edge-disjoint paths : "
                    f"{data['count']}\n\n"
                )

                if data["paths"]:

                    for i, path in enumerate(
                        data["paths"],
                        start=1
                    ):

                        result_output.insert(
                            tk.END,
                            f"Independent Path {i} : "
                        )

                        result_output.insert(
                            tk.END,
                            " → ".join(
                                map(
                                    str,
                                    path
                                )
                            )
                            + "\n"
                        )

                else:

                    result_output.insert(
                        tk.END,
                        "No independent path was found.\n"
                    )

            # ==================================================
            # DISPATCH
            # ==================================================

            if selected == "All Algorithms (Combined)":

                sections = [
                    write_cuts,
                    write_k,
                    write_flow,
                    write_ff_labeling,
                    write_max_flow_min_cut,
                    write_menger
                ]

                for i, section in enumerate(sections):

                    section()

                    if i != len(sections) - 1:

                        result_output.insert(
                            tk.END,
                            "\n" + "=" * 70 + "\n\n"
                        )

            elif selected == "Cuts and Connectivity":

                write_cuts()

            elif selected == "k-Connected Graph":

                write_k()

            elif selected == "Network Flow":

                write_flow()

            elif selected == "Ford-Fulkerson Labeling":

                write_ff_labeling()

            elif selected == "Max-Flow Min-Cut":

                write_max_flow_min_cut()

            elif selected == "Menger's Theorem":

                write_menger()

            result_output.config(
                state="disabled"
            )

            result_output.see(
                "1.0"
            )

        # ======================================================
        # DRAW GRAPH
        # ======================================================

        def draw_graph():

            if self.robustness_report is None:

                return

            graph_type = graph_combo.get()

            if not graph_type:

                return

            for widget in graph_frame.winfo_children():

                widget.destroy()

            graph_data = self.robustness_report[
                "robustness_graph"
            ]

            # --------------------------------------------------
            # NO CONNECTION
            # --------------------------------------------------

            if not graph_data[
                "connected"
            ]:

                tk.Label(
                    graph_frame,
                    text=(
                        "NO ROUTE AVAILABLE\n\n"
                        "The selected source and destination "
                        "are not connected."
                    ),
                    font=("Segoe UI", 15, "bold"),
                    bg=self.white,
                    fg=self.danger
                ).pack(
                    expand=True
                )

                return

            graph = nx.Graph()

            # --------------------------------------------------
            # ROBUSTNESS GRAPH
            # --------------------------------------------------

            if graph_type == "Robustness Graph":

                graph.add_nodes_from(
                    graph_data[
                        "nodes"
                    ]
                )

                for edge in graph_data[
                    "edges"
                ]:

                    graph.add_edge(
                        edge["source"],
                        edge["destination"]
                    )

            # --------------------------------------------------
            # MENGER GRAPH
            # --------------------------------------------------

            elif graph_type == "Menger Independent Paths":

                paths = graph_data[
                    "menger_paths"
                ]

                for path in paths:

                    for station in path:

                        graph.add_node(
                            station
                        )

                    for u, v in zip(
                        path,
                        path[1:]
                    ):

                        graph.add_edge(
                            u,
                            v
                        )

                if graph.number_of_nodes() == 0:

                    tk.Label(
                        graph_frame,
                        text="No independent paths found.",
                        font=("Segoe UI", 12),
                        bg=self.white,
                        fg=self.muted
                    ).pack(
                        expand=True
                    )

                    return

            # --------------------------------------------------
            # CRITICAL COMPONENT GRAPH
            # --------------------------------------------------

            elif graph_type == "Critical Components":

                graph.add_nodes_from(
                    graph_data[
                        "nodes"
                    ]
                )

                for edge in graph_data[
                    "edges"
                ]:

                    graph.add_edge(
                        edge["source"],
                        edge["destination"]
                    )

            if graph.number_of_nodes() == 0:

                tk.Label(
                    graph_frame,
                    text="No graph data available.",
                    font=("Segoe UI", 12),
                    bg=self.white,
                    fg=self.muted
                ).pack(
                    expand=True
                )

                return

            # --------------------------------------------------
            # CREATE FIGURE
            # --------------------------------------------------

            figure = plt.Figure(
                figsize=(11, 5.5),
                dpi=100
            )

            axis = figure.add_subplot(
                111
            )

            axis.set_axis_off()

            # --------------------------------------------------
            # GRAPH LAYOUT
            # --------------------------------------------------

            try:

                if graph.number_of_nodes() <= 20:

                    positions = nx.spring_layout(
                        graph,
                        seed=42,
                        k=1.5
                    )

                else:

                    positions = nx.kamada_kawai_layout(
                        graph
                    )

            except Exception:

                positions = nx.spring_layout(
                    graph,
                    seed=42
                )

            # --------------------------------------------------
            # CRITICAL COMPONENTS
            # --------------------------------------------------

            critical_stations = set(
                graph_data[
                    "critical_stations"
                ]
            )

            critical_tracks = set()

            for track in graph_data[
                "critical_tracks"
            ]:

                if len(track) == 2:

                    critical_tracks.add(
                        frozenset(
                            (
                                track[0],
                                track[1]
                            )
                        )
                    )

            normal_edges = []
            critical_edges = []

            for u, v in graph.edges():

                if frozenset(
                    (
                        u,
                        v
                    )
                ) in critical_tracks:

                    critical_edges.append(
                        (
                            u,
                            v
                        )
                    )

                else:

                    normal_edges.append(
                        (
                            u,
                            v
                        )
                    )

            # --------------------------------------------------
            # NORMAL TRACKS
            # --------------------------------------------------

            if normal_edges:

                nx.draw_networkx_edges(
                    graph,
                    positions,
                    edgelist=normal_edges,
                    ax=axis,
                    width=2,
                    edge_color="gray"
                )

            # --------------------------------------------------
            # CRITICAL TRACKS
            # --------------------------------------------------

            if critical_edges:

                nx.draw_networkx_edges(
                    graph,
                    positions,
                    edgelist=critical_edges,
                    ax=axis,
                    width=5,
                    edge_color="red"
                )

            # --------------------------------------------------
            # NODES
            # --------------------------------------------------

            node_colors = []

            for node in graph.nodes():

                if node == self.robustness_source:

                    node_colors.append(
                        "green"
                    )

                elif node == self.robustness_destination:

                    node_colors.append(
                        "royalblue"
                    )

                elif node in critical_stations:

                    node_colors.append(
                        "red"
                    )

                else:

                    node_colors.append(
                        "lightgray"
                    )

            nx.draw_networkx_nodes(
                graph,
                positions,
                node_color=node_colors,
                node_size=900,
                edgecolors="black",
                linewidths=1.5,
                ax=axis
            )

            # --------------------------------------------------
            # LABELS
            # --------------------------------------------------

            nx.draw_networkx_labels(
                graph,
                positions,
                ax=axis,
                font_size=8,
                font_weight="bold"
            )

            axis.set_title(
                (
                    f"Robustness Analysis Graph\n"
                    f"{self.robustness_source} → "
                    f"{self.robustness_destination}"
                ),
                fontsize=13,
                fontweight="bold"
            )

            # --------------------------------------------------
            # LEGEND
            # --------------------------------------------------

            from matplotlib.lines import Line2D

            legend_items = [

                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="w",
                    label="Source",
                    markerfacecolor="green",
                    markersize=10
                ),

                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="w",
                    label="Destination",
                    markerfacecolor="royalblue",
                    markersize=10
                ),

                Line2D(
                    [0],
                    [0],
                    marker="o",
                    color="w",
                    label="Critical Station",
                    markerfacecolor="red",
                    markersize=10
                ),

                Line2D(
                    [0],
                    [0],
                    color="gray",
                    linewidth=2,
                    label="Normal Track"
                ),

                Line2D(
                    [0],
                    [0],
                    color="red",
                    linewidth=4,
                    label="Critical Track"
                )
            ]

            axis.legend(
                handles=legend_items,
                loc="best"
            )

            figure.tight_layout()

            # --------------------------------------------------
            # EMBED GRAPH
            # --------------------------------------------------

            self.graph_figure = figure

            self.graph_canvas = FigureCanvasTkAgg(
                figure,
                master=graph_frame
            )

            self.graph_canvas.draw()

            canvas_widget = (
                self.graph_canvas.get_tk_widget()
            )

            canvas_widget.pack(
                fill="both",
                expand=True
            )

        # ======================================================
        # RUN ROBUSTNESS
        # ======================================================

        def resolve_station(typed_text):

            typed_text = typed_text.strip()

            for station in self.stations:

                if station.lower() == typed_text.lower():

                    return station

            return None

        def run_robustness(silent=False):

            source_typed = source_combo.get().strip()

            destination_typed = (
                destination_combo
                .get()
                .strip()
            )

            if not source_typed or not destination_typed:

                messagebox.showwarning(
                    "Selection Required",
                    "Please select or type both source and destination."
                )

                return

            source = resolve_station(
                source_typed
            )

            destination = resolve_station(
                destination_typed
            )

            if source is None:

                messagebox.showwarning(
                    "Invalid Station",
                    f"'{source_typed}' is not a recognized station.\n"
                    "Please pick a valid station from the list."
                )

                return

            if destination is None:

                messagebox.showwarning(
                    "Invalid Station",
                    f"'{destination_typed}' is not a recognized station.\n"
                    "Please pick a valid station from the list."
                )

                return

            if source == destination:

                messagebox.showwarning(
                    "Invalid Selection",
                    "Source and destination must be different."
                )

                return

            try:

                self.root.config(
                    cursor="watch"
                )

                self.root.update_idletasks()

                report = (
                    self.optimizer
                    .aga_robustness_report(
                        source,
                        destination
                    )
                )

                self.robustness_report = report

                self.selected_source = source

                self.selected_destination = destination

                self.robustness_source = source

                self.robustness_destination = destination

                result_combo.set("")

                graph_combo.set("")

                result_output.config(
                    state="normal"
                )

                result_output.delete(
                    "1.0",
                    tk.END
                )

                result_output.insert(
                    tk.END,
                    "ROBUSTNESS ANALYSIS COMPLETED\n\n"
                    f"Source      : {source}\n"
                    f"Destination : {destination}\n\n"
                    "Select an algorithm from the "
                    "Analysis Result dropdown, or choose "
                    "'All Algorithms (Combined)' to view "
                    "every result at once."
                )

                result_output.config(
                    state="disabled"
                )

                for widget in graph_frame.winfo_children():

                    widget.destroy()

                tk.Label(
                    graph_frame,
                    text=(
                        "Select a graph from the "
                        "Graph dropdown."
                    ),
                    font=("Segoe UI", 12),
                    bg=self.white,
                    fg=self.muted
                ).pack(
                    expand=True
                )

                if not silent:

                    messagebox.showinfo(
                        "Analysis Complete",
                        "All six AGA robustness algorithms "
                        "have been executed successfully."
                    )

            except Exception as error:

                messagebox.showerror(
                    "Robustness Analysis Error",
                    (
                        "Unable to perform robustness analysis.\n\n"
                        + str(error)
                    )
                )

            finally:

                self.root.config(
                    cursor=""
                )

            self.update_scroll_region()

        # ======================================================
        # SWITCH TO PATHS PAGE (keeps the selected stations)
        # ======================================================

        def go_to_paths():

            source = resolve_station(source_combo.get())
            destination = resolve_station(destination_combo.get())

            if source is None or destination is None:

                messagebox.showwarning(
                    "Invalid Station",
                    "Please select valid source and destination "
                    "stations from the suggestions."
                )

                return

            if source == destination:

                messagebox.showwarning(
                    "Invalid Selection",
                    "Source and destination must be different."
                )

                return

            self.selected_source = source
            self.selected_destination = destination

            self.show_shortest_paths(source, destination)

        # ======================================================
        # DROPDOWN EVENTS
        # ======================================================

        result_combo.bind(
            "<<ComboboxSelected>>",
            lambda event:
            display_result()
        )

        graph_combo.bind(
            "<<ComboboxSelected>>",
            lambda event:
            draw_graph()
        )

        self.update_scroll_region()

        if auto_run and selected_source and selected_destination:

            self.root.after(
                50,
                lambda: run_robustness(silent=True)
            )

    # ==========================================================
    # SHORTEST PATH SELECTION (shortest + alternatives)
    # ==========================================================

    @staticmethod
    def _select_diverse_alternatives(alternatives, limit=8):
        """Pick up to ``limit`` alternatives that differ meaningfully.

        The raw list can contain dozens of routes that differ by a single
        station, which makes a list and graph unreadable. Routes are taken in
        distance order, skipping any that share >85% of stations with one
        already chosen; remaining slots are filled in distance order.
        """
        chosen = []
        for route in alternatives:
            stations = set(route["path"])
            similar = False
            for kept in chosen:
                kept_set = set(kept["path"])
                overlap = len(stations & kept_set) / max(1, len(stations | kept_set))
                if overlap > 0.85:
                    similar = True
                    break
            if not similar:
                chosen.append(route)
            if len(chosen) >= limit:
                break
        if len(chosen) < limit:
            for route in alternatives:
                if route not in chosen:
                    chosen.append(route)
                if len(chosen) >= limit:
                    break
        chosen.sort(key=lambda r: r["total_distance"])
        return chosen

    def show_shortest_paths(self, source=None, destination=None):
        """New page: shortest path, +100-200 km alternatives and a graph."""
        self.clear_content()
        self.header(
            "Route Comparison",
            "Compare the shortest-distance route with the balanced optimal route and viable alternatives"
        )

        # ---------------- selection card ----------------
        selection_card = self.create_card()
        top_row = tk.Frame(selection_card, bg=self.white)
        top_row.pack(fill="x", padx=25, pady=(20, 6))
        tk.Label(top_row, text="SELECT SOURCE AND DESTINATION",
                 font=("Segoe UI", 11, "bold"), bg=self.white, fg=self.dark).pack(side="left")
        tk.Button(top_row, text="ROBUSTNESS ANALYSIS  →",
                  command=lambda: go_to_robustness(),
                  font=("Segoe UI", 10, "bold"), bg=self.primary, fg=self.white,
                  activebackground=self.sidebar_hover, activeforeground=self.white,
                  relief="flat", padx=16, pady=8, cursor="hand2").pack(side="right")

        controls = tk.Frame(selection_card, bg=self.white)
        controls.pack(fill="x", padx=20, pady=(0, 20))
        tk.Label(controls, text="Source Station", font=("Segoe UI", 10, "bold"),
                 bg=self.white, fg=self.muted).grid(row=0, column=0, padx=8, sticky="w")
        tk.Label(controls, text="Destination Station", font=("Segoe UI", 10, "bold"),
                 bg=self.white, fg=self.muted).grid(row=0, column=1, padx=8, sticky="w")
        source_combo = AutocompleteEntry(controls, self.stations, width=34, bg=self.white)
        source_combo.grid(row=1, column=0, padx=8, pady=6)
        destination_combo = AutocompleteEntry(controls, self.stations, width=34, bg=self.white)
        destination_combo.grid(row=1, column=1, padx=8, pady=6)
        source = source or self.selected_source
        destination = destination or self.selected_destination
        if source and destination:
            source_combo.set(source)
            destination_combo.set(destination)
        elif len(self.stations) >= 2:
            source_combo.set(self.stations[0])
            destination_combo.set(self.stations[1])

        # ---------------- summary / list card ----------------
        list_card = self.create_card()
        tk.Label(list_card, text="SHORTEST PATH & ALTERNATIVE PATHS (UP TO 200 KM EXTRA)",
                 font=("Segoe UI", 15, "bold"), bg=self.white, fg=self.dark).pack(
                     anchor="w", padx=25, pady=(18, 6))
        status_label = tk.Label(
            list_card,
            text="Choose stations and click FIND BOTH PATHS.",
            font=("Segoe UI", 10), bg=self.white, fg=self.muted,
            wraplength=1000, justify="left")
        status_label.pack(anchor="w", padx=25, pady=(0, 8))

        optimal_card = self.create_card()
        tk.Label(optimal_card, text="BALANCED OPTIMAL PATH", font=("Segoe UI", 15, "bold"),
                 bg=self.white, fg=self.dark).pack(anchor="w", padx=25, pady=(18, 6))
        optimal_result_label = tk.Label(
            optimal_card,
            text="The balanced optimal route will appear here when you calculate both paths.",
            font=("Segoe UI", 10), bg=self.white, fg=self.text,
            wraplength=1100, justify="left", anchor="w")
        optimal_result_label.pack(fill="x", padx=25, pady=(0, 18))

        table_frame = tk.Frame(list_card, bg=self.white)
        table_frame.pack(fill="x", padx=20, pady=(0, 10))
        columns = ("type", "distance", "extra", "time", "stops", "route")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=9)
        headings = {"type": "Path", "distance": "Distance (km)", "extra": "Extra vs shortest (km)",
                    "time": "Time (min)", "stops": "Stations", "route": "Route"}
        widths = {"type": 110, "distance": 100, "extra": 150, "time": 90, "stops": 70, "route": 520}
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col],
                        anchor="w" if col in ("type", "route") else "center",
                        stretch=(col == "route"))
        tree.tag_configure("shortest", background="#FDECEA", foreground="#B71C1C")
        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side="right", fill="y")
        tree.pack(side="left", fill="x", expand=True)

        tk.Label(list_card, text="Full route of the selected row:",
                 font=("Segoe UI", 9, "bold"), bg=self.white, fg=self.muted).pack(
                     anchor="w", padx=25)
        detail_label = tk.Label(list_card, text="—", font=("Segoe UI", 10),
                                bg=self.light, fg=self.text, wraplength=1000,
                                justify="left", anchor="w", padx=12, pady=8)
        detail_label.pack(fill="x", padx=20, pady=(2, 18))

        # ---------------- graph card ----------------
        graph_card = self.create_card()
        tk.Label(graph_card, text="ROUTE COMPARISON GRAPH", font=("Segoe UI", 15, "bold"),
                 bg=self.white, fg=self.dark).pack(anchor="w", padx=25, pady=(18, 6))
        tk.Label(graph_card,
                 text="Shortest path is shown in red, balanced optimal path in teal, and alternative routes in dashed colours.",
                 font=("Segoe UI", 10), bg=self.white, fg=self.muted,
                 wraplength=1000, justify="left").pack(anchor="w", padx=25)
        plot_frame = tk.Frame(graph_card, bg=self.white, height=720)
        plot_frame.pack(fill="x", padx=20, pady=(10, 20))
        plot_frame.pack_propagate(False)
        placeholder = tk.Label(plot_frame, text="Graphs will appear here after FIND BOTH PATHS.",
                               font=("Segoe UI", 11), bg=self.white, fg=self.muted)
        placeholder.pack(expand=True)
        state = {"canvas": None, "figure": None, "routes": {}}

        def resolve_station(value):
            value = value.strip()
            for station in self.stations:
                if station.casefold() == value.casefold():
                    return station
            return None

        def go_to_robustness():
            src = resolve_station(source_combo.get())
            dst = resolve_station(destination_combo.get())
            if src is None or dst is None:
                messagebox.showwarning("Invalid Station",
                                       "Please select valid source and destination stations from the suggestions.")
                return
            if src == dst:
                messagebox.showwarning("Invalid Selection",
                                       "Source and destination must be different stations.")
                return
            self.selected_source, self.selected_destination = src, dst
            self.show_robustness(src, dst, auto_run=True)

        def on_select(event=None):
            selected = tree.selection()
            if not selected:
                return
            route = state["routes"].get(selected[0])
            if route:
                detail_label.config(text="  →  ".join(route["path"]))

        tree.bind("<<TreeviewSelect>>", on_select)

        def draw_graph(shortest, alternatives, optimal=None):
            import math
            import textwrap
            from matplotlib.figure import Figure
            from matplotlib.lines import Line2D

            if placeholder.winfo_exists():
                placeholder.destroy()
            if state["canvas"] is not None:
                state["canvas"].get_tk_widget().destroy()
                plt.close(state["figure"])

            palette = ["#1E88E5", "#43A047", "#FB8C00", "#8E24AA", "#00ACC1",
                       "#6D4C41", "#D81B60", "#7CB342", "#5E35B1", "#F4511E"]

            sp = shortest["path"]
            sp_index = {st: i for i, st in enumerate(sp)}
            sp_set = set(sp)

            # ---------------- ARRANGED LAYOUT ----------------
            # Shortest path = straight horizontal "trunk", evenly spaced.
            # Every detour (stretch of an alternative that leaves the trunk
            # and rejoins it) becomes a clean arc in its own lane, alternating
            # above / below the trunk, with its stations evenly spaced.
            pos = {st: (float(i), 0.0) for i, st in enumerate(sp)}
            lane_count = 0
            layout_routes = list(alternatives)
            if optimal and optimal.get("path"):
                layout_routes.append(optimal)
            for route in layout_routes:
                path = route["path"]
                n = len(path)
                i = 0
                while i < n:
                    if path[i] in sp_set:
                        i += 1
                        continue
                    j = i
                    while j < n and path[j] not in sp_set:
                        j += 1
                    run = path[i:j]
                    left = sp_index.get(path[i - 1]) if i > 0 else None
                    right = sp_index.get(path[j]) if j < n else None
                    if left is None and right is None:
                        left, right = 0, len(sp) - 1
                    elif left is None:
                        left = right
                    elif right is None:
                        right = left
                    if left == right:  # dead-end spur: push it outward
                        left, right = left - 0.5, right + 0.5
                    fresh = [st for st in run if st not in pos]
                    if fresh:
                        lane_count += 1
                        side = 1 if lane_count % 2 else -1
                        height = 1.7 + 1.5 * ((lane_count - 1) // 2)
                        seq = ([path[i - 1]] if i > 0 else []) + run + ([path[j]] if j < n else [])
                        if all(st not in pos for st in run) and \
                                (i == 0 or path[i - 1] in sp_set) and (j >= n or path[j] in sp_set):
                            # whole detour is new: clean arch between its two trunk anchors
                            for k, st in enumerate(run):
                                frac = (k + 1) / (len(run) + 1)
                                x = left + (right - left) * frac
                                y = side * height * (0.55 + 0.45 * math.sin(math.pi * frac))
                                pos[st] = (x, y)
                        else:
                            # partly known detour: put new stations between their placed neighbours
                            m = 0
                            while m < len(seq):
                                if seq[m] in pos:
                                    m += 1
                                    continue
                                g = m
                                while g < len(seq) and seq[g] not in pos:
                                    g += 1
                                P = pos[seq[m - 1]] if m > 0 else None
                                Q = pos[seq[g]] if g < len(seq) else None
                                if P is None:
                                    P = (Q[0] - 0.8, Q[1])
                                if Q is None:
                                    Q = (P[0] + 0.8, P[1])
                                bump_side = side if (P[1] + Q[1]) == 0 else (1 if (P[1] + Q[1]) > 0 else -1)
                                cnt = g - m
                                for t in range(cnt):
                                    frac = (t + 1) / (cnt + 1)
                                    x = P[0] + (Q[0] - P[0]) * frac
                                    y = P[1] + (Q[1] - P[1]) * frac + bump_side * 0.9 * math.sin(math.pi * frac)
                                    pos[seq[m + t]] = (x, y)
                                m = g
                    i = j

            union = nx.Graph()
            for route in [shortest] + alternatives + ([optimal] if optimal and optimal.get("path") else []):
                for u, v in zip(route["path"], route["path"][1:]):
                    union.add_edge(u, v)

            fig = Figure(figsize=(16, 8.5), dpi=100, constrained_layout=True)
            ax = fig.add_subplot(111)

            # Alternatives first (underneath the trunk)
            legend_handles = []
            shortest_edges = set(zip(sp, sp[1:])) | set(zip(sp[1:], sp))
            for idx, route in enumerate(alternatives):
                colour = palette[idx % len(palette)]
                edges = [e for e in zip(route["path"], route["path"][1:])
                         if e not in shortest_edges]
                rad = (-1) ** idx * 0.05 * (1 + idx // 2)  # tiny fan-out so shared edges stay visible
                nx.draw_networkx_edges(
                    nx.DiGraph(edges), pos, edgelist=edges, ax=ax,
                    edge_color=colour, width=1.8, style="dashed", alpha=0.9,
                    arrows=True, arrowsize=10, node_size=300,
                    connectionstyle=f"arc3,rad={rad}")
                legend_handles.append(Line2D(
                    [0], [0], color=colour, lw=2, ls="--",
                    label=f"Alt {idx + 1}: {route['total_distance']:,.0f} km "
                          f"(+{route['extra_distance']:,.0f})"))

            # Balanced optimal path is drawn in teal so it can be compared with the shortest path.
            if optimal and optimal.get("path"):
                optimal_edges = list(zip(optimal["path"], optimal["path"][1:]))
                optimal_only_edges = [edge for edge in optimal_edges
                                      if edge not in shortest_edges]
                nx.draw_networkx_edges(
                    nx.DiGraph(optimal_only_edges), pos, edgelist=optimal_only_edges, ax=ax,
                    edge_color="#00897B", width=4.0, style="solid", alpha=0.98,
                    arrows=True, arrowsize=15, node_size=300,
                    connectionstyle="arc3,rad=0.13")
                legend_handles.append(Line2D(
                    [0], [0], color="#00897B", lw=4,
                    label=f"Balanced optimal: {optimal.get('total_distance', 0):,.0f} km"))

            # Shortest path (trunk) on top
            sp_edges = list(zip(sp, sp[1:]))
            nx.draw_networkx_edges(
                nx.DiGraph(sp_edges), pos, edgelist=sp_edges, ax=ax,
                edge_color="#D32F2F", width=4.5, arrows=True, arrowsize=16,
                node_size=300)
            legend_handles.insert(0, Line2D(
                [0], [0], color="#D32F2F", lw=5,
                label=f"Shortest: {shortest['total_distance']:,.0f} km"))

            # Nodes
            on_alt = [s_ for s_ in union.nodes if s_ not in sp_set]
            nx.draw_networkx_nodes(union, pos, nodelist=on_alt, ax=ax, node_size=300,
                                   node_color="#FFFFFF", edgecolors="#546E7A", linewidths=1.5)
            mid = [s_ for s_ in sp if s_ not in (sp[0], sp[-1])]
            nx.draw_networkx_nodes(union, pos, nodelist=mid, ax=ax, node_size=300,
                                   node_color="#FFCDD2", edgecolors="#D32F2F", linewidths=2)
            nx.draw_networkx_nodes(union, pos, nodelist=[sp[0]], ax=ax, node_size=650,
                                   node_color="#43A047", edgecolors="#1B5E20", linewidths=2)
            nx.draw_networkx_nodes(union, pos, nodelist=[sp[-1]], ax=ax, node_size=650,
                                   node_color="#E53935", edgecolors="#7F0000", linewidths=2)

            # Trunk labels alternate above / below so they never collide
            for i, st in enumerate(sp):
                x, y = pos[st]
                dy = 0.42 if i % 2 == 0 else -0.42
                ax.text(x, y + dy, "\n".join(textwrap.wrap(st, 12)), ha="center",
                        va="bottom" if dy > 0 else "top", fontsize=7.5,
                        fontweight="bold", color="#B71C1C",
                        bbox={"boxstyle": "round,pad=0.15", "fc": "white",
                              "ec": "none", "alpha": 0.9}, zorder=6)
            # Detour labels sit just outside the arc (above on top lanes, below on bottom lanes)
            for st in union.nodes:
                if st in sp_set:
                    continue
                x, y = pos[st]
                up = y >= 0
                ax.text(x, y + (0.28 if up else -0.28), "\n".join(textwrap.wrap(st, 14)),
                        ha="center", va="bottom" if up else "top", fontsize=7,
                        fontweight="bold", color="#102A43",
                        bbox={"boxstyle": "round,pad=0.12", "fc": "white",
                              "ec": "none", "alpha": 0.85}, zorder=6)

            # Distances on trunk edges, at the midpoint between stations
            for c in shortest["connections"]:
                u, v = c["source"], c["destination"]
                if u in pos and v in pos:
                    mx = (pos[u][0] + pos[v][0]) / 2
                    ax.text(mx, 0.0, f"{c['distance']:g}", ha="center", va="center",
                            fontsize=7, color="#B71C1C", zorder=7,
                            bbox={"boxstyle": "round,pad=0.12", "fc": "white",
                                  "ec": "#EF9A9A", "lw": 0.6})

            ax.set_title(
                f"{sp[0]}  \u2192  {sp[-1]}   |   shortest {shortest['total_distance']:,.0f} km, "
                f"{len(alternatives)} alternative path(s)",
                fontsize=12, fontweight="bold", color="#102A43")
            ax.legend(handles=legend_handles, loc="upper left", fontsize=8,
                      framealpha=0.95, title="Paths (km)", ncol=1)
            ax.margins(0.06, 0.18)
            ax.axis("off")

            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            state["canvas"] = canvas
            state["figure"] = fig

        def find_paths():
            if not tree.winfo_exists():
                return
            src = resolve_station(source_combo.get())
            dst = resolve_station(destination_combo.get())
            if src is None or dst is None:
                messagebox.showwarning("Invalid Station",
                                       "Please select valid source and destination stations from the suggestions.")
                return
            if src == dst:
                messagebox.showwarning("Invalid Selection",
                                       "Source and destination must be different stations.")
                return
            self.selected_source, self.selected_destination = src, dst
            try:
                self.root.config(cursor="watch")
                self.root.update_idletasks()
                result = self.optimizer.distance_alternative_routes(
                    src, dst, min_extra_km=0, max_extra_km=100)
            except Exception as error:
                messagebox.showerror("Path Search Error",
                                     f"Unable to find paths.\n\n{error}")
                return
            finally:
                self.root.config(cursor="")

            for item in tree.get_children():
                tree.delete(item)
            state["routes"] = {}
            detail_label.config(text="—")

            shortest = result.get("shortest")
            if shortest is None:
                status_label.config(
                    text=f"No railway route exists from {src} to {dst} in the supplied dataset.")
                messagebox.showinfo("No Route", f"No route found from {src} to {dst}.")
                return

            all_alts = result.get("alternatives", [])
            alts = self._select_diverse_alternatives(all_alts, limit=8)

            try:
                optimal = self.optimizer.optimal_balanced_route(src, dst)
            except Exception as error:
                optimal = None
                optimal_result_label.config(text=f"Balanced optimal route could not be calculated: {error}")

            if optimal:
                optimal_route = "  →  ".join(optimal.get("path", []))
                optimal_connections = optimal.get("connections", [])
                connection_lines = "\n".join(
                    f"{edge.get('source', '')} → {edge.get('destination', '')}  |  "
                    f"{edge.get('distance', 0):,.2f} km  |  "
                    f"{edge.get('travel_time', 0):,.2f} min  |  "
                    f"{edge.get('train_name', 'Train information unavailable')}"
                    for edge in optimal_connections
                ) or "No intermediate connections."
                optimal_result_label.config(text=(
                    f"Route\n{optimal_route}\n\n"
                    f"Total distance: {optimal.get('total_distance', 0):,.2f} km     |     "
                    f"Total travel time: {optimal.get('total_time', 0):,.2f} minutes\n"
                    f"Balanced score: {optimal.get('optimal_score', 0):.4f}     |     "
                    f"Connected component size: {optimal.get('connected_component_size', 'N/A')} stations\n\n"
                    f"Train connections\n{connection_lines}"
                ))
            else:
                optimal_result_label.config(text="No balanced optimal route exists for this source and destination.")

            iid = tree.insert("", "end", tags=("shortest",), values=(
                "★ SHORTEST", f"{shortest['total_distance']:,.2f}", "0.00",
                f"{shortest['total_time']:,.0f}", len(shortest["path"]),
                "  →  ".join(shortest["path"])))
            state["routes"][iid] = shortest
            for index, route in enumerate(alts, start=1):
                iid = tree.insert("", "end", values=(
                    f"Alternative {index}", f"{route['total_distance']:,.2f}",
                    f"+{route['extra_distance']:,.2f}", f"{route['total_time']:,.0f}",
                    len(route["path"]), "  →  ".join(route["path"])))
                state["routes"][iid] = route
            tree.selection_set(tree.get_children()[0])

            if alts:
                note = (f"Shortest path: {shortest['total_distance']:,.2f} km. "
                        f"{len(all_alts)} alternative route(s) are within 0–200 km extra distance; "
                        f"showing {len(alts)} distinct ones.")
            else:
                note = (f"Shortest path: {shortest['total_distance']:,.2f} km. "
                        + (result.get("message") or
                           "No alternative path within 0–200 km extra distance was found in the dataset."))
            status_label.config(text=note)
            draw_graph(shortest, alts, optimal)
            self.update_scroll_region()

        tk.Button(controls, text="FIND BOTH PATHS", command=find_paths,
                  font=("Segoe UI", 10, "bold"), bg=self.success, fg=self.white,
                  activebackground=self.sidebar_hover, activeforeground=self.white,
                  relief="flat", padx=24, pady=10, cursor="hand2").grid(
                      row=1, column=2, padx=16, pady=6)

        self.update_scroll_region()
        if source and destination:
            self.root.after(50, find_paths)

    # ==========================================================
    # SHORTEST-DISTANCE ROUTE OPTIMIZATION
    # ==========================================================

    def show_route_optimization(self):
        """Display and visualize the shortest-distance route in the GUI."""
        self.clear_content()
        self.header(
            "Route Optimization",
            "Find the minimum-distance railway route using Dijkstra's algorithm and dataset distances"
        )

        selection_card = self.create_card()
        tk.Label(
            selection_card, text="SELECT SOURCE AND DESTINATION",
            font=("Segoe UI", 11, "bold"), bg=self.white, fg=self.dark
        ).pack(anchor="w", padx=25, pady=(20, 10))

        controls = tk.Frame(selection_card, bg=self.white)
        controls.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(controls, text="Source Station", font=("Segoe UI", 10, "bold"),
                 bg=self.white, fg=self.muted).grid(row=0, column=0, padx=8, sticky="w")
        tk.Label(controls, text="Destination Station", font=("Segoe UI", 10, "bold"),
                 bg=self.white, fg=self.muted).grid(row=0, column=1, padx=8, sticky="w")

        source_combo = AutocompleteEntry(controls, self.stations, width=34, bg=self.white)
        source_combo.grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        destination_combo = AutocompleteEntry(controls, self.stations, width=34, bg=self.white)
        destination_combo.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

        if len(self.stations) >= 2:
            source_combo.set(self.stations[0])
            destination_combo.set(self.stations[1])

        result_card = self.create_card()
        tk.Label(result_card, text="SHORTEST DISTANCE RESULT (DIJKSTRA)",
                 font=("Segoe UI", 16, "bold"), bg=self.white, fg=self.dark).pack(
                     anchor="w", padx=25, pady=(20, 8))
        tk.Label(result_card,
                 text="The route distance is calculated from the 'distance' column in data/cleaned_routes.csv. This is the shortest route available in the supplied dataset; missing railway links cannot be inferred.",
                 font=("Segoe UI", 10), bg=self.white, fg=self.muted,
                 wraplength=1000, justify="left").pack(anchor="w", padx=25, pady=(0, 10))

        summary = tk.Frame(result_card, bg=self.light, highlightbackground=self.border, highlightthickness=1)
        summary.pack(fill="x", padx=20, pady=8)
        distance_value = tk.Label(summary, text="Total distance: —", font=("Segoe UI", 16, "bold"),
                                  bg=self.light, fg=self.success, padx=15, pady=12)
        distance_value.pack(anchor="w")
        time_value = tk.Label(summary, text="Estimated dataset travel time: —",
                              font=("Segoe UI", 11), bg=self.light, fg=self.text, padx=15, pady=4)
        time_value.pack(anchor="w")
        route_value = tk.Label(summary, text="Route: run the search to see the shortest path.",
                               font=("Segoe UI", 10), bg=self.light, fg=self.text, padx=15, pady=6,
                               wraplength=1000, justify="left")
        route_value.pack(anchor="w", fill="x")

        connection_card = self.create_card()
        tk.Label(connection_card, text="ROUTE CONNECTION DETAILS", font=("Segoe UI", 14, "bold"),
                 bg=self.white, fg=self.dark).pack(anchor="w", padx=25, pady=(18, 8))
        table_frame = tk.Frame(connection_card, bg=self.white)
        table_frame.pack(fill="x", padx=20, pady=(0, 20))
        columns = ("no", "source", "destination", "train", "number", "distance", "time")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
        headings = {"no": "No.", "source": "From", "destination": "To", "train": "Train",
                    "number": "Train No.", "distance": "Distance (km)", "time": "Time (min)"}
        widths = {"no": 45, "source": 150, "destination": 150, "train": 190, "number": 85, "distance": 105, "time": 95}
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="w" if col in ("source", "destination", "train") else "center")
        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        tree.pack(side="left", fill="x", expand=True)
        tree_scroll.pack(side="right", fill="y")

        graph_card = self.create_card()
        tk.Label(graph_card, text="SHORTEST ROUTE VISUALIZATION", font=("Segoe UI", 14, "bold"),
                 bg=self.white, fg=self.dark).pack(anchor="w", padx=25, pady=(18, 8))
        tk.Label(graph_card, text="A clearer route map with distance labels for every connection. The result is the shortest route supported by the supplied dataset.",
                 font=("Segoe UI", 10), bg=self.white, fg=self.muted, wraplength=1000).pack(anchor="w", padx=25)
        plot_frame = tk.Frame(graph_card, bg=self.white, height=420)
        plot_frame.pack(fill="x", expand=False, padx=20, pady=(10, 20))
        plot_frame.pack_propagate(False)
        plot_canvas = {"canvas": None, "figure": None}
        placeholder = tk.Label(plot_frame, text="Choose stations and click FIND SHORTEST DISTANCE.",
                               font=("Segoe UI", 11), bg=self.white, fg=self.muted)
        placeholder.pack(expand=True)

        def resolve_station(value):
            value = value.strip()
            for station in self.stations:
                if station.casefold() == value.casefold():
                    return station
            return None

        def run_search():
            source_text = source_combo.get().strip()
            destination_text = destination_combo.get().strip()
            source = resolve_station(source_text)
            destination = resolve_station(destination_text)
            if source is None or destination is None:
                messagebox.showwarning("Invalid Station", "Please select valid source and destination stations from the suggestions.")
                return
            if source == destination:
                messagebox.showwarning("Invalid Selection", "Source and destination must be different stations.")
                return

            try:
                self.root.config(cursor="watch")
                self.root.update_idletasks()
                result = self.optimizer.shortest_distance_route(source, destination)
            except Exception as error:
                messagebox.showerror("Route Calculation Error", f"Unable to calculate the shortest-distance route.\n\n{error}")
                return
            finally:
                self.root.config(cursor="")

            for item in tree.get_children():
                tree.delete(item)

            if result is None:
                distance_value.config(text="Total distance: No route found")
                time_value.config(text="Estimated dataset travel time: —")
                route_value.config(text=f"No railway route was found from {source} to {destination}.")
                return

            distance_value.config(text=f"Total distance: {result['total_distance']:,.2f} km")
            time_value.config(text=f"Estimated dataset travel time: {result['total_time']:,.2f} minutes")
            route_value.config(text="Route: " + "  →  ".join(result["path"]))

            for index, connection in enumerate(result["connections"], start=1):
                tree.insert("", "end", values=(
                    index, connection["source"], connection["destination"],
                    connection.get("train_name", ""), connection.get("train_number", ""),
                    f"{connection['distance']:,.2f}", f"{connection['travel_time']:,.2f}"
                ))

            # Save result when the database is available; failure to save must not hide the route.
            try:
                database = RailwayDatabase()
                database.save_result(
                    source=source, destination=destination,
                    optimization_type="Shortest Distance (Dijkstra)",
                    route=" -> ".join(result["path"]),
                    total_distance=result["total_distance"], total_time=result["total_time"]
                )
            except Exception:
                pass

            # Redraw the path diagram. Use the chosen route's consecutive edges only.
            if placeholder.winfo_exists():
                placeholder.destroy()
            if plot_canvas["canvas"] is not None:
                plot_canvas["canvas"].get_tk_widget().destroy()
                plt.close(plot_canvas["figure"])

            from matplotlib.figure import Figure
            import textwrap

            # Arrange stations in a serpentine layout so long paths remain readable.
            node_count = len(result["path"])
            columns = min(5, max(2, node_count))
            rows = (node_count + columns - 1) // columns
            fig_width = max(10.0, min(15.0, columns * 2.25))
            fig_height = max(4.8, rows * 1.65 + 1.2)
            fig = Figure(figsize=(fig_width, fig_height), dpi=110, constrained_layout=True)
            ax = fig.add_subplot(111)
            path_graph = nx.DiGraph()
            path_graph.add_nodes_from(result["path"])
            path_graph.add_edges_from(zip(result["path"], result["path"][1:]))

            positions = {}
            for index, station in enumerate(result["path"]):
                row = index // columns
                col = index % columns
                if row % 2 == 1:
                    col = columns - 1 - col
                positions[station] = (col, -row)

            nx.draw_networkx_edges(
                path_graph, positions, ax=ax, edge_color="#2563EB", width=2.8,
                arrows=True, arrowsize=18, node_size=2400,
                connectionstyle="arc3,rad=0.04"
            )
            nx.draw_networkx_nodes(
                path_graph, positions, ax=ax, node_size=2400,
                node_color="#DDF7EE", edgecolors="#07866F", linewidths=2.2
            )
            labels = {station: "\n".join(textwrap.wrap(station, width=15))
                      for station in result["path"]}
            nx.draw_networkx_labels(
                path_graph, positions, labels=labels, ax=ax,
                font_size=8, font_weight="bold", font_color="#123047"
            )
            edge_labels = {
                (c["source"], c["destination"]): f"{c['distance']:g} km"
                for c in result["connections"]
            }
            nx.draw_networkx_edge_labels(
                path_graph, positions, edge_labels=edge_labels, ax=ax,
                font_size=8, font_color="#9A3412", label_pos=0.5,
                rotate=False, bbox={"alpha": 0.85, "color": "white", "pad": 1}
            )
            ax.set_title(
                f"Shortest dataset route • {result['total_distance']:,.2f} km  |  "
                f"{node_count} stations",
                fontsize=12, fontweight="bold", color="#123047", pad=18
            )
            ax.margins(x=0.12, y=0.22)
            ax.axis("off")
            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            plot_canvas["canvas"] = canvas
            plot_canvas["figure"] = fig

        tk.Button(controls, text="FIND SHORTEST DISTANCE", command=run_search,
                  font=("Segoe UI", 10, "bold"), bg=self.primary, fg=self.white,
                  activebackground=self.sidebar_hover, activeforeground=self.white,
                  relief="flat", padx=20, pady=10, cursor="hand2").grid(
                      row=1, column=2, padx=16, pady=6, sticky="ew")
        self.update_scroll_region()

    # ==========================================================
    # BALANCED OPTIMAL PATH (SEPARATE PAGE)
    # ==========================================================

    def show_optimal_path(self, selected_source=None, selected_destination=None):
        """Compatibility entry point; both route results now share one page."""
        return self.show_shortest_paths(selected_source, selected_destination)

    # ==========================================================
    # NETWORK INFORMATION
    # ==========================================================

    def show_network(self):

        self.clear_content()

        self.header(
            "Network Information",
            "Railway network represented as a graph"
        )

        card = self.create_card()

        try:

            stations = (
                self.railway
                .get_number_of_stations()
            )

        except Exception:

            stations = len(
                self.stations
            )

        try:

            connections = (
                self.railway
                .get_number_of_connections()
            )

        except Exception:

            connections = 0

        information = (
            "RAILWAY NETWORK\n"
            "============================\n\n"
            f"Total Stations       : {stations}\n"
            f"Total Connections    : {connections}\n\n"
            "GRAPH REPRESENTATION\n"
            "============================\n\n"
            "Railway Station      → Vertex\n"
            "Railway Connection   → Edge\n"
            "Multiple connections → Multiple edges\n"
            "Connection capacity  → Flow capacity\n"
            "Selected stations    → Source-Destination pair"
        )

        tk.Label(
            card,
            text=information,
            font=("Consolas", 11),
            bg=self.white,
            fg=self.text,
            justify="left"
        ).pack(
            anchor="w",
            padx=30,
            pady=30
        )

        station_card = self.create_card()

        tk.Label(
            station_card,
            text="Railway Stations",
            font=("Segoe UI", 16, "bold"),
            bg=self.white,
            fg=self.dark
        ).pack(
            anchor="w",
            padx=25,
            pady=15
        )

        frame = tk.Frame(
            station_card,
            bg=self.white
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical"
        )

        tree = ttk.Treeview(
            frame,
            columns=(
                "No",
                "Station"
            ),
            show="headings",
            yscrollcommand=scrollbar.set
        )

        tree.heading(
            "No",
            text="No."
        )

        tree.heading(
            "Station",
            text="Station Name"
        )

        tree.column(
            "No",
            width=80,
            anchor="center"
        )

        tree.column(
            "Station",
            width=600
        )

        for i, station in enumerate(
            self.stations,
            start=1
        ):

            tree.insert(
                "",
                "end",
                values=(
                    i,
                    station
                )
            )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.config(
            command=tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.update_scroll_region()

    # ==========================================================
    # DATASET ANALYSIS
    # ==========================================================

    def show_analysis(self):

        self.clear_content()

        self.header(
            "Dataset Analysis",
            "Statistics from the railway dataset"
        )

        card = self.create_card()

        try:

            data = self.railway.data

            lines = [

                "RAILWAY DATASET SUMMARY",

                "=" * 60,

                "",

                f"Total route records : "
                f"{len(data)}"
            ]

            if "source" in data.columns:

                lines.append(
                    f"Unique source stations : "
                    f"{data['source'].nunique()}"
                )

            if "destination" in data.columns:

                lines.append(
                    f"Unique destination stations : "
                    f"{data['destination'].nunique()}"
                )

            if "distance" in data.columns:

                distance = data[
                    "distance"
                ]

                lines.extend(
                    [
                        "",
                        "DISTANCE STATISTICS",
                        "-" * 60,
                        f"Minimum : "
                        f"{distance.min():.2f}",
                        f"Average : "
                        f"{distance.mean():.2f}",
                        f"Maximum : "
                        f"{distance.max():.2f}"
                    ]
                )

            tk.Label(
                card,
                text="\n".join(lines),
                font=("Consolas", 11),
                bg=self.white,
                fg=self.text,
                justify="left"
            ).pack(
                anchor="w",
                padx=30,
                pady=30
            )

        except Exception as error:

            tk.Label(
                card,
                text=(
                    "Unable to load dataset analysis.\n\n"
                    + str(error)
                ),
                font=("Segoe UI", 11),
                bg=self.white,
                fg=self.danger
            ).pack(
                anchor="w",
                padx=30,
                pady=30
            )

        self.update_scroll_region()

    # ==========================================================
    # ABOUT
    # ==========================================================

    def show_about(self):

        self.clear_content()

        self.header(
            "About Project",
            "AGA Railway Network Robustness Analyzer"
        )

        card = self.create_card()

        information = (
            "PROJECT OBJECTIVE\n"
            "============================\n\n"
            "The project models a railway network as a graph "
            "and evaluates the robustness of a selected "
            "source-to-destination connection.\n\n"

            "AGA CONCEPTS IMPLEMENTED\n"
            "============================\n\n"

            "1. Cuts and Connectivity\n"
            "   Critical stations and railway tracks\n\n"

            "2. k-Connected Graphs\n"
            "   Pair vertex connectivity\n\n"

            "3. Network Flow\n"
            "   Railway connections represented using capacities\n\n"

            "4. Ford-Fulkerson Labeling Algorithm\n"
            "   Residual network and augmenting paths\n\n"

            "5. Max-Flow Min-Cut Theorem\n"
            "   Maximum flow, minimum cut and bottlenecks\n\n"

            "6. Menger's Theorem\n"
            "   Edge-disjoint railway paths\n\n"

            "ROBUSTNESS GRAPH\n"
            "============================\n\n"
            "The graph shown in the Robustness Check page "
            "is generated from the robustness analysis of "
            "the selected source-to-destination pair. "
            "Shortest and fastest route calculations are "
            "not used to create this graph.\n\n"

            "GRAPH COLOURING\n"
            "============================\n\n"
            "Green  → Source\n"
            "Blue   → Destination\n"
            "Red    → Critical station / track\n"
            "Gray   → Normal railway connection"
        )

        tk.Label(
            card,
            text=information,
            font=("Segoe UI", 11),
            bg=self.white,
            fg=self.text,
            justify="left",
            anchor="nw",
            wraplength=1050
        ).pack(
            anchor="w",
            padx=30,
            pady=30
        )

        self.update_scroll_region()


# ==============================================================
# START APPLICATION
# ==============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = RailwayGUI(
        root
    )

    root.mainloop()