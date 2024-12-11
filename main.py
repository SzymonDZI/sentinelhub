from map_date_selector import MapAndDateSelector
from satellite_downloader import SatelliteDataDownloader
from sentinelhub import BBox

def main():
    selector = MapAndDateSelector()
    selector.run()

    if not selector.selected_coords or not selector.start_date or not selector.end_date:
        print("Nie wybrano współrzędnych lub zakresu dat.")
        return

    # Debugowanie współrzędnych
    print(f"Współrzędne: {selector.selected_coords}")
    print(f"Daty: {selector.start_date} do {selector.end_date}")

    # Test bbox
    lat, lon = selector.selected_coords
    bbox = BBox([lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05], crs="EPSG:4326")
    print(f"BBOX: {bbox}")

if __name__ == "__main__":
    main()
