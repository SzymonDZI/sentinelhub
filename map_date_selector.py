import tkinter as tk
from tkintermapview import TkinterMapView
from tkcalendar import DateEntry

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

    def run(self):
        root = tk.Tk()
        root.title("Wybór obszaru i daty")

        self.map_widget = TkinterMapView(root, width=800, height=600)
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

        root.mainloop()



        #sprawdzanie w konsoli czy pobiera
        print(self.selected_coords)
        print(self.start_date, self.end_date)


#dorobić okno w GUI które wyświetla wybrane wcześniej współrzędne i stamtąd kopiować dopiero do kodu
#zapisywanie pobranego zdjęcia z sentinelhuba
