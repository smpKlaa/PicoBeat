import time
import json

class Historian:
    # Class to manage saved HRV measurements
    def __init__(self):
        self.saved_measurements = []
        self.filename = "/history.txt"
        self.max_entries = 50  # Keep only the last 50 measurements
        self.load_history()

    def create_history(self):
        # Create empty history file if it doesn't exist
        try:
            with open(self.filename, "x") as f:
                pass
        except FileExistsError:
            pass
        except Exception as e:
            print("Error creating history file:", e)

    def load_history(self):
        # Load saved measurements from file
        self.saved_measurements = []
        try:
            with open(self.filename, "r") as f:
                for line in f:
                    if line.strip():
                        self.saved_measurements.append(json.loads(line))
        except Exception:
            self.saved_measurements = []
            self.create_history()
        
        # Sort from newest to oldest
        self.saved_measurements.sort(key=lambda x: x["time"], reverse=True)

    def add_measurement(self, measurement):
        # Append new measurement to history file and reload
        try:
            with open(self.filename, "a") as f:
                json.dump(measurement, f)
                f.write("\n")
        except Exception as e:
            print("Error appending to history:", e)

        self.load_history()

        if len(self.saved_measurements) > self.max_entries:
            self.saved_measurements = self.saved_measurements[-self.max_entries:]

    def run_menu(self, menu_manager):
        # Display the measurement history menu
        self.load_history()
        oled = menu_manager.oled
        encoder = menu_manager.encoder
        print("Event from encoder:", encoder.check_button_event())

        if not self.saved_measurements:
            oled.fill(0)
            oled.text("No measurements!", 2, 25)
            oled.show()
            time.sleep(2)
            return

        selected = 0

        def draw_measurement_list():
            # Draw scrolling list of saved HRV measurements
            total = len(self.saved_measurements)
            oled.fill(0)
            oled.text("HRV Records:", 2, 0)

            start = max(0, selected - 1)
            end = min(start + 4, total)

            for i, index in enumerate(range(start, end)):
                ts = time.localtime(self.saved_measurements[index]["time"])
                label = "{:02d}:{:02d}, {:02d}/{:02d}/{:02d}".format(
                    ts[3], ts[4], ts[2], ts[1], ts[0] % 100)
                y = (i + 1) * 12
                if index == selected:
                    oled.fill_rect(0, y, 128, 12, 1)
                    oled.text(label, 2, y + 2, 0)
                else:
                    oled.text(label, 2, y + 2, 1)
            oled.show()

        draw_measurement_list()

        # Delay to prevent accidental misclick
        time.sleep(0.5)
        while encoder.check_button_event() is not None:
            time.sleep(0.01)

        while True:
            move = encoder.get()
            if move is not None:
                if move == 1:
                    selected = (selected + 1) % len(self.saved_measurements)
                    draw_measurement_list()
                elif move == -1:
                    selected = (selected - 1) % len(self.saved_measurements)
                    draw_measurement_list()

            event = encoder.check_button_event()
            
            if event == "short":
                self.view_details(oled, self.saved_measurements[selected], encoder)
                draw_measurement_list()
            elif event == "long":
                return  # Go back to main menu

            time.sleep(0.01)

    def view_details(self, oled, measurement, encoder):
        # Display a single HRV measurement's details
        oled.fill(0)
        ts = time.localtime(measurement['time'])

        oled.text("{:02d}:{:02d} {:02d}/{:02d}/{:04d}".format(
            ts[3], ts[4], ts[2], ts[1], ts[0]), 0, 0)
        oled.text(f"HR: {measurement['mean_hr']} bpm", 0, 12)
        oled.text(f"PPI: {measurement['mean_ppi']} ms", 0, 24)
        oled.text(f"RMSSD: {measurement['rmssd']} ms", 0, 36)
        oled.text(f"SDNN: {measurement['sdnn']} ms", 0, 48)
        oled.show()

        # Wait until long hold to exit back to list
        while True:
            event = encoder.check_button_event()
            if event == "long":
                return
            time.sleep(0.01)