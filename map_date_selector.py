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

    def on_map_click(self, event):
        # Pobranie współrzędnych wskaźnika myszy na mapie
        lat, lon = self.map_widget.get_position()
        if lat and lon:
            self.selected_coords = (lat, lon)
            self.selected_coords_label.config(text=f"Wybrane współrzędne: {lat:.6f}, {lon:.6f}")
            print(f"Współrzędne zapisane: {self.selected_coords}")  # Wyświetlenie w konsoli
        else:
            print("Błąd: Nie udało się pobrać współrzędnych.")

    def get_date_range(self):
        self.start_date = self.start_date_entry.get_date().strftime("%Y-%m-%d")
        self.end_date = self.end_date_entry.get_date().strftime("%Y-%m-%d")
        self.date_range_label.config(text=f"Zakres dat: {self.start_date} do {self.end_date}")
        print(f"Daty zapisane: {self.start_date} - {self.end_date}")  # Wyświetlenie w konsoli

    def start_analysis(self):
        if self.selected_coords and self.start_date and self.end_date:
            print(f"Rozpoczynam analizę dla współrzędnych: {self.selected_coords} i zakresu dat: {self.start_date} - {self.end_date}")

            # Inicjalizacja klasy do pobierania zdjęć satelitarnych
            downloader = SatelliteDataDownloader(
                instance_id='3463381a-2429-4be7-a992-4238930c44a6',
                client_id='bd25de5b-c246-4c2a-bffa-0142d1dbb16c',
                client_secret='4bkP2kZ7rNin8mB6VdWsTYQdjwqFIUig'
            )

            # Stworzenie BBox z wybranymi współrzędnymi
            lat, lon = self.selected_coords
            bbox = BBox([lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05], crs="EPSG:4326")

            # Pobranie zdjęcia
            image, date_range = downloader.download_image(bbox, (self.start_date, self.end_date))

            # Wyświetlenie zdjęcia z datą
            downloader.display_image(image, date_range)

        else:
            print("Błąd: Nie wszystkie dane zostały wprowadzone.")

    def run(self):
        root = tk.Tk()
        root.title("Wybór obszaru i daty")

        self.map_widget = TkinterMapView(root, width=1000, height=600)
        self.map_widget.set_position(52.2297, 21.0122)  # Warszawa
        self.map_widget.set_zoom(10)
        self.map_widget.pack()

        self.map_widget.bind("<Button-1>", self.on_map_click)  # Obsługa kliknięcia na mapie

        self.selected_coords_label = tk.Label(root, text="Kliknij na mapie, aby wybrać współrzędne", font=("Arial", 12))
        self.selected_coords_label.pack(pady=5)

        date_frame = tk.Frame(root)
        date_frame.pack(pady=10)

        tk.Label(date_frame, text="Data początkowa:", font=("Arial", 12)).grid(row=0, column=0, padx=5)
        self.start_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.start_date_entry.grid(row=0, column=1, padx=5)

        tk.Label(date_frame, text="Data końcowa:", font=("Arial", 12)).grid(row=0, column=2, padx=5)
        self.end_date_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.end_date_entry.grid(row=0, column=3, padx=5)

        date_button = tk.Button(root, text="Zatwierdź daty", command=self.get_date_range)
        date_button.pack(pady=5)

        self.date_range_label = tk.Label(root, text="Zakres dat: -", font=("Arial", 12))
        self.date_range_label.pack(pady=5)

        # Dodanie sekcji do wklejania współrzędnych
        coords_frame = tk.Frame(root)
        coords_frame.pack(pady=10)

        tk.Label(coords_frame, text="Wklej współrzędne (lat lon):", font=("Arial", 12)).grid(row=0, column=0, padx=5)
        self.coords_entry = tk.Entry(coords_frame, width=30)
        self.coords_entry.grid(row=0, column=1, padx=5)

        copy_coords_button = tk.Button(coords_frame, text="Zatwierdź współrzędne", command=self.copy_coords)
        copy_coords_button.grid(row=0, column=2, padx=5)

        self.copied_coords_label = tk.Label(root, text="Wprowadzone współrzędne: -", font=("Arial", 12))
        self.copied_coords_label.pack(pady=5)

        # Dodanie przycisku do rozpoczęcia analizy
        analyze_button = tk.Button(root, text="Rozpocznij analizę", command=self.start_analysis)
        analyze_button.pack(pady=10)

        root.mainloop()

    def copy_coords(self):
        # Pobranie współrzędnych z pola tekstowego
        coords_text = self.coords_entry.get()
        try:
            lat, lon = map(float, coords_text.split())
            self.selected_coords = (lat, lon)
            self.copied_coords_label.config(text=f"Wprowadzone współrzędne: {lat:.6f}, {lon:.6f}")
            print(f"Wprowadzone współrzędne zapisane: {self.selected_coords}")
        except ValueError:
            self.copied_coords_label.config(text="Błąd: Niepoprawny format współrzędnych.")
            print("Błąd: Niepoprawny format współrzędnych.")
