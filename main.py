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


    # Inicjalizacja klasy do pobierania zdjęć satelitarnych
    downloader = SatelliteDataDownloader(
        instance_id="your-instance-id",  # Wprowadź swoje Instance ID
        client_id="your-client-id",      # Wprowadź swoje Client ID
        client_secret="your-client-secret"  # Wprowadź swoje Client Secret
    )

    # Pobieranie i wyświetlanie zdjęcia
    image = downloader.download_image(bbox, (selector.start_date, selector.end_date))
    downloader.display_image(image)

if __name__ == "__main__":
    main()
