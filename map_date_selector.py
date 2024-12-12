import tkinter as tk
from tkintermapview import TkinterMapView
from tkcalendar import DateEntry
from satellite_downloader import SatelliteDataDownloader
from sentinelhub import BBox, bbox_to_dimensions

class MapAndDateSelector:
    def __init__(self):
        self.selected_coords = None
        self.start_date = None
        self.end_date = None
        self.mode = "RGB"  # Domyślny tryb wyświetlania

    def on_map_click(self, event):
        lat, lon = self.map_widget.get_position()
        if lat and lon:
            self.selected_coords = (lat, lon)
            self.selected_coords_label.config(text=f"Wybrane współrzędne: {lat:.6f}, {lon:.6f}")
            print(f"Współrzędne zapisane: {self.selected_coords}")
        else:
            print("Błąd: Nie udało się pobrać współrzędnych.")

    def get_date_range(self):
        self.start_date = self.start_date_entry.get_date().strftime("%Y-%m-%d")
        self.end_date = self.end_date_entry.get_date().strftime("%Y-%m-%d")
        self.date_range_label.config(text=f"Zakres dat: {self.start_date} do {self.end_date}")
        print(f"Daty zapisane: {self.start_date} - {self.end_date}")

    def set_mode_rgb(self):
        self.mode = "RGB"
        self.rgb_button.config(bg="green")  # RGB button to green
        self.ndvi_button.config(bg="lightgray")  # NDVI button to default color
        print("Tryb wyświetlania ustawiony na RGB")

    def set_mode_ndvi(self):
        self.mode = "NDVI"
        self.ndvi_button.config(bg="green")  # NDVI button to green
        self.rgb_button.config(bg="lightgray")  # RGB button to default color
        print("Tryb wyświetlania ustawiony na NDVI")

    def start_analysis(self):
        if self.selected_coords and self.start_date and self.end_date:
            print(f"Rozpoczynam analizę dla współrzędnych: {self.selected_coords} i zakresu dat: {self.start_date} - {self.end_date}")

            downloader = SatelliteDataDownloader(
                instance_id='3463381a-2429-4be7-a992-4238930c44a6',
                client_id='bd25de5b-c246-4c2a-bffa-0142d1dbb16c',
                client_secret='4bkP2kZ7rNin8mB6VdWsTYQdjwqFIUig'
            )

            lat, lon = self.selected_coords
            bbox = BBox([lon-0.1, lat-0.1, lon+0.1, lat+0.1], crs="EPSG:4326")

            # Ustawienie trybu w downloaderze
            downloader.mode = self.mode

            image, date_range = downloader.download_image(bbox, (self.start_date, self.end_date))
            downloader.display_image(image, date_range)
        else:
            print("Błąd: Nie wszystkie dane zostały wprowadzone.")

    def run(self):
        root = tk.Tk()
        root.title("Wybór obszaru i daty")
        root.geometry("1100x700")
        root.minsize(800, 600)

        # Configure grid weights for resizing
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=0)
        root.grid_rowconfigure(2, weight=0)
        root.grid_rowconfigure(3, weight=0)
        root.grid_rowconfigure(4, weight=0)
        root.grid_rowconfigure(5, weight=0)
        root.grid_rowconfigure(6, weight=0)
        root.grid_columnconfigure(0, weight=1)

        # Map widget
        self.map_widget = TkinterMapView(root, width=800, height=500)
        self.map_widget.set_position(52.2297, 21.0122)
        self.map_widget.set_zoom(10)
        self.map_widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.map_widget.bind("<Button-1>", self.on_map_click)

        # Frame for selected coordinates and other options
        options_frame = tk.Frame(root)
        options_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        options_frame.grid_columnconfigure(1, weight=1)

        # Label for selected coordinates
        self.selected_coords_label = tk.Label(options_frame, text="Kliknij na mapie, aby wybrać współrzędne", font=("Arial", 12, "bold"))
        self.selected_coords_label.grid(row=0, column=0, columnspan=2, pady=5)

        # Date selection frame
        date_frame = tk.LabelFrame(root, text="Wybór zakresu dat", font=("Arial", 12, "bold"), padx=10, pady=10)
        date_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        date_frame.grid_columnconfigure(4, weight=1)

        tk.Label(date_frame, text="Data początkowa:", font=("Arial", 14)).grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(date_frame, text="Data końcowa:", font=("Arial", 14)).grid(row=0, column=2, padx=5, pady=5)
        self.end_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5)

        date_button = tk.Button(date_frame, text="Zatwierdź daty", font=("Arial", 12, "bold"), command=self.get_date_range, bg="lightblue", relief="raised")
        date_button.grid(row=0, column=4, padx=10, pady=5)

        self.date_range_label = tk.Label(root, text="Zakres dat: -", font=("Arial", 12, "bold"))
        self.date_range_label.grid(row=3, column=0, pady=5)

        # Coordinates input frame
        coords_frame = tk.LabelFrame(root, text="Wprowadzanie współrzędnych", font=("Arial", 12, "bold"), padx=10, pady=10)
        coords_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        coords_frame.grid_columnconfigure(1, weight=1)

        tk.Label(coords_frame, text="Wklej współrzędne (lat lon):", font=("Arial", 14)).grid(row=0, column=0, padx=5, pady=5)
        self.coords_entry = tk.Entry(coords_frame, width=30, font=("Arial", 14))
        self.coords_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        copy_coords_button = tk.Button(coords_frame, text="Zatwierdź współrzędne", font=("Arial", 12, "bold"), command=self.copy_coords, bg="lightgreen", relief="raised")
        copy_coords_button.grid(row=0, column=2, padx=10, pady=5)

        self.copied_coords_label = tk.Label(root, text="Wprowadzone współrzędne: -", font=("Arial", 12, "bold"))
        self.copied_coords_label.grid(row=5, column=0, pady=5)

        # Mode selection frame
        mode_frame = tk.LabelFrame(root, text="Tryb wyświetlania", font=("Arial", 12, "bold"), padx=10, pady=10)
        mode_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=10)

        self.rgb_button = tk.Button(mode_frame, text="RGB", font=("Arial", 12, "bold"), command=self.set_mode_rgb, bg="lightgray", relief="raised")
        self.rgb_button.grid(row=0, column=0, padx=10, pady=5)

        self.ndvi_button = tk.Button(mode_frame, text="NDVI", font=("Arial", 12, "bold"), command=self.set_mode_ndvi, bg="lightgray", relief="raised")
        self.ndvi_button.grid(row=0, column=1, padx=10, pady=5)

        # Set RGB button to green initially
        self.rgb_button.config(bg="green")

        # Analysis button
        analyze_button = tk.Button(root, text="Rozpocznij analizę", font=("Arial", 14, "bold"), command=self.start_analysis, bg="orange", relief="raised")
        analyze_button.grid(row=7, column=0, pady=20)

        # Adjust map widget dynamically
        root.bind("<Configure>", self.resize_map)

        root.mainloop()

    def resize_map(self, event):
        if event.widget == event.widget.master:
            new_width = event.width - 20  # Adjust for padding
            new_height = event.height - 300  # Account for other widgets
            if new_width > 0 and new_height > 0:
                self.map_widget.config(width=new_width, height=new_height)

    def copy_coords(self):
        coords_text = self.coords_entry.get()
        try:
            lat, lon = map(float, coords_text.split())
            self.selected_coords = (lat, lon)
            self.copied_coords_label.config(text=f"Wprowadzone współrzędne: {lat:.6f}, {lon:.6f}")
            print(f"Wprowadzone współrzędne zapisane: {self.selected_coords}")
        except ValueError:
            self.copied_coords_label.config(text="Błąd: Niepoprawny format współrzędnych.")
            print("Błąd: Niepoprawny format współrzędnych.")
