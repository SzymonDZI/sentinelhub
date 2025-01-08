from map_date_selector import MapAndDateSelector

def main():
    selector = MapAndDateSelector()
    selector.run()

    if not selector.selected_coords or not selector.start_date or not selector.end_date:
        print("Nie wybrano współrzędnych lub zakresu dat.")
        return

if __name__ == "__main__":
    main()
