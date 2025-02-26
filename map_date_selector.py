import tkinter as tk
from tkintermapview import TkinterMapView
from tkcalendar import DateEntry
from satellite_downloader import SatelliteDataDownloader
from sentinelhub import BBox

class MapAndDateSelector:
    def __init__(self):
        self.selected_coords = None
        self.start_date = None
        self.end_date = None
        self.mode = "RGB"  # Domyślny tryb wyświetlania
        self.selected_band = None

    def on_map_click(self, event):
        lat, lon = self.map_widget.get_position()
        if lat and lon:
            self.selected_coords = (lat, lon)
            self.selected_coords_label.config(text=f"Wybrane współrzędne:\n {lat:.6f}, {lon:.6f}")
            print(f"Współrzędne zapisane: {self.selected_coords}")
        else:
            print("Błąd: Nie udało się pobrać współrzędnych.")

    def get_date_range(self):
        self.start_date = self.start_date_entry.get_date().strftime("%Y-%m-%d")
        self.end_date = self.end_date_entry.get_date().strftime("%Y-%m-%d")
        self.date_range_label.config(text=f"Zakres dat:\n {self.start_date} do {self.end_date}")
        print(f"Daty zapisane: {self.start_date} - {self.end_date}")

    def reset_mode_buttons(self):
        self.rgb_button.config(bg="lightgray")
        self.ndvi_button.config(bg="lightgray")
        self.ndwi_button.config(bg="lightgray")
        self.savi_button.config(bg="lightgray")


    def set_mode_rgb(self):
        self.mode = "RGB"
        self.reset_mode_buttons()
        self.rgb_button.config(bg="green")
        print("Tryb wyświetlania ustawiony na RGB")

    def set_mode_ndvi(self):
        self.mode = "NDVI"
        self.reset_mode_buttons()
        self.ndvi_button.config(bg="green")
        print("Tryb wyświetlania ustawiony na NDVI")

    def set_mode_ndwi(self):
        self.mode = "NDWI"
        self.reset_mode_buttons()
        self.ndwi_button.config(bg="green")
        print("Tryb wyświetlania ustawiony na NDWI")

    def set_mode_savi(self):
        self.mode = "SAVI"
        self.reset_mode_buttons()
        self.savi_button.config(bg="green")
        print("Tryb wyświetlania ustawiony na SAVI")

    def start_analysis(self):
        if self.selected_coords and self.start_date and self.end_date:
            print(f"Rozpoczynam analizę dla współrzędnych: {self.selected_coords} i zakresu dat: {self.start_date} - {self.end_date}")

            downloader = SatelliteDataDownloader(
                instance_id='d6d1603e-a6f9-407f-b473-90214c91d379',
                client_id='b293465d-c7a1-4065-8257-b68bd1812d9b',
                client_secret='NDhVObKWLQr4CdVuJYgCWn9yCEYQXeHF'
            )

            lat, lon = self.selected_coords
            bbox = BBox([lon-0.1, lat-0.1, lon+0.1, lat+0.1], crs="EPSG:4326")

            downloader.mode = self.mode
            if self.selected_band is not None:
                print(f"Używanie pasma: {self.selected_band}")
                downloader.selected_band = self.selected_band  # Przekazywanie wybranego pasma

            image, date_range, timestamp = downloader.download_image(bbox, (self.start_date, self.end_date))
            downloader.display_image(image, date_range, timestamp)
        else:
            print("Błąd: Nie wszystkie dane zostały wprowadzone.")

    def resize_map(self, event):
        if event.widget == event.widget.master:
            new_width = event.width - 20  
            new_height = event.height - 300  
            if new_width > 0 and new_height > 0:
                self.map_widget.config(width=new_width, height=new_height)
                
    def run(self): 
        root = tk.Tk()
        root.title("Wybór obszaru i daty")
        root.geometry("1200x800")
        root.minsize(1000, 800)

        root.bind("<Configure>", self.resize_map)

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=3)  

        # panel po lewej stronie okno
        left_panel = tk.Frame(root, bg="lightgray")
        left_panel.grid(row=0, column=0, sticky="nsew")
        left_panel.grid_rowconfigure(10, weight=1) 

        # panel mapy
        self.map_widget = TkinterMapView(root, width=800, height=600)
        self.map_widget.set_position(50.0607, 19.9384)
        self.map_widget.set_zoom(10)
        self.map_widget.grid(row=0, column=1, sticky="nsew")
        self.map_widget.bind("<Button-1>", self.on_map_click)

        # Selected coordinates label
        self.selected_coords_label = tk.Label(left_panel, text="Kliknij na mapie, aby wybrać współrzędne", 
                                            font=("Arial", 12, "bold"), bg="lightgray", wraplength=250, justify="left", anchor="w", height=2)
        self.selected_coords_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Coordinates input frame
        coords_frame = tk.LabelFrame(left_panel, text="Wprowadzanie współrzędnych", font=("Arial", 12, "bold"), padx=10, pady=10, bg="lightgray")
        coords_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        tk.Label(coords_frame, text="Wklej współrzędne:", font=("Arial", 12), bg="lightgray").grid(row=0, column=0, padx=5, pady=5)
        self.coords_entry = tk.Entry(coords_frame, width=30, font=("Arial", 12))
        self.coords_entry.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        copy_coords_button = tk.Button(coords_frame, text="Zatwierdź współrzędne", font=("Arial", 10, "bold"), command=self.copy_coords, bg="lightgreen", relief="raised")
        copy_coords_button.grid(row=2, column=0, pady=5)

        # Reserve space for dynamic coordinates
        self.copied_coords_label = tk.Label(left_panel, text="Wprowadzone współrzędne: -", font=("Arial", 12, "bold"), bg="lightgray", 
                                            wraplength=250, justify="left", anchor="w", height=2)
        self.copied_coords_label.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # Date selection frame
        date_frame = tk.LabelFrame(left_panel, text="Wybór zakresu dat", font=("Arial", 12, "bold"), padx=10, pady=10, bg="lightgray")
        date_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        tk.Label(date_frame, text="Data początkowa:", font=("Arial", 12), bg="lightgray").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, 
                                        date_pattern="dd.MM.yyyy")
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(date_frame, text="Data końcowa:", font=("Arial", 12), bg="lightgray").grid(row=1, column=0, padx=5, pady=5)
        self.end_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, 
                                        date_pattern="dd.MM.yyyy")
        self.end_date_entry.grid(row=1, column=1, padx=5, pady=5)

        date_button = tk.Button(date_frame, text="Zatwierdź daty", font=("Arial", 10, "bold"), command=self.get_date_range, bg="lightblue", relief="raised")
        date_button.grid(row=2, column=0, columnspan=2, pady=5)

        # Reserve space for dynamic date range
        self.date_range_label = tk.Label(left_panel, text="Zakres dat: -", font=("Arial", 12, "bold"), bg="lightgray", wraplength=250, 
                                        justify="left", anchor="w", height=2)
        self.date_range_label.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        # Mode selection frame
        mode_frame = tk.LabelFrame(left_panel, text="Tryb wyświetlania", font=("Arial", 12, "bold"), padx=10, pady=10, bg="lightgray")
        mode_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        self.rgb_button = tk.Button(mode_frame, text="RGB", font=("Arial", 10, "bold"), command=self.set_mode_rgb, bg="lightgray", relief="raised")
        self.rgb_button.grid(row=0, column=0, padx=5, pady=5)

        self.ndvi_button = tk.Button(mode_frame, text="NDVI", font=("Arial", 10, "bold"), command=self.set_mode_ndvi, bg="lightgray", relief="raised")
        self.ndvi_button.grid(row=0, column=1, padx=5, pady=5)

        self.ndwi_button = tk.Button(mode_frame, text="NDWI", font=("Arial", 10, "bold"), command=self.set_mode_ndwi, bg="lightgray", relief="raised")
        self.ndwi_button.grid(row=0, column=2, padx=5, pady=5)

        self.savi_button = tk.Button(mode_frame, text="SAVI", font=("Arial", 10, "bold"), command=self.set_mode_savi, bg="lightgray", relief="raised")
        self.savi_button.grid(row=0, column=3, padx=5, pady=5)

        self.rgb_button.config(bg="green")  # Set RGB button as default active

        # Analyze button
        analyze_button = tk.Button(left_panel, text="Rozpocznij analizę", font=("Arial", 12, "bold"), command=self.start_analysis, bg="orange", relief="raised")
        analyze_button.grid(row=7, column=0, padx=10, pady=20, sticky="ew")

        root.mainloop()

    

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
