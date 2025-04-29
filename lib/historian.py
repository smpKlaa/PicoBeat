import time
import json

class Historian:
    # Class to manage saved HRV measurements
    def __init__(self):
        self.saved_measurements = []
        self.filename = "/history.txt"
        self.max_entries = 50  # Keep only the last 50 measurements
        self.load_history()

    def save_history(self):
        # Save all saved_measurements to file
        try:
            with open(self.filename, "w") as f:
                json.dump(self.saved_measurements, f)
        except Exception as e:
            print("Error saving history:", e)

    def load_history(self):
        # Load saved_measurements from file
        try:
            with open(self.filename, "r") as f:
                self.saved_measurements = json.load(f)
        except Exception:
            # If file does not exist or error happens, start fresh
            self.saved_measurements = []

    def add_measurement(self, measurement):
        # Add a new HRV measurement, keeping the list size under limit
        self.saved_measurements.append(measurement)
        if len(self.saved_measurements) > self.max_entries:
            self.saved_measurements.pop(0)  # Remove oldest
        self.save_history()

    def run_menu(self, menu_manager):
        # Show the History submenu
        oled = menu_manager.oled
        encoder = menu_manager.encoder

        history_menu_items = [
            "Last Measurement",
            "All Measurements",
            "Back"
        ]

        selected = 0
        total = len(history_menu_items)

        def draw_history_menu():
            # Draw the history menu
            oled.fill(0)
            oled.text("History Menu:", 2, 0)
            for i in range(total):
                y = (i + 1) * 12
                label = history_menu_items[i]
                if i == selected:
                    oled.fill_rect(0, y, 128, 12, 1)
                    oled.text(label, 2, y + 2, 0)
                else:
                    oled.text(label, 2, y + 2, 1)
            oled.show()

        draw_history_menu()

        # Short delay to avoid button misclicks
        time.sleep(0.5)
        while menu_manager.button.value() == 0:
            time.sleep(0.01)

        last_button = 1

        while True:
            move = encoder.get()
            if move is not None:
                if move == 1:
                    selected = (selected + 1) % total
                    draw_history_menu()
                elif move == -1:
                    selected = (selected - 1) % total
                    draw_history_menu()

            button_state = menu_manager.button.value()

            # Detect button press (falling edge)
            if button_state == 0 and last_button == 1:
                time.sleep(0.05)
                return selected

            last_button = button_state
            time.sleep(0.01)

    def show_last(self, oled):
        # Show the latest saved HRV measurement
        if not self.saved_measurements:
            oled.fill(0)
            oled.text("No measurements!", 2, 25)
            oled.show()
            time.sleep(2)
            return

        last_result = self.saved_measurements[-1]

        oled.fill(0)
        oled.text(f"HR: {last_result['mean_hr']} bpm", 2, 0)
        oled.text(f"PPI: {last_result['mean_ppi']} ms", 2, 12)
        oled.text(f"RMSSD: {last_result['rmssd']} ms", 2, 24)
        oled.text(f"SDNN: {last_result['sdnn']} ms", 2, 36)
        oled.show()
        time.sleep(5)

    def show_all(self, oled, menu_manager):
        # Show list of all saved measurements
        if not self.saved_measurements:
            oled.fill(0)
            oled.text("No measurements!", 2, 25)
            oled.show()
            time.sleep(2)
            return

        encoder = menu_manager.encoder
        button = menu_manager.button

        selected = 0
        total = len(self.saved_measurements) + 1  # +1 for 'Back'

        def draw_id_list():
            # Draw list of measurements and an option for going back
            oled.fill(0)
            oled.text("Select Measurement:", 2, 0)
            for i in range(total):
                y = (i + 1) * 12
                if i < len(self.saved_measurements):
                    label = f"ID {self.saved_measurements[i]['id']}"
                else:
                    label = "Back"

                if i == selected:
                    oled.fill_rect(0, y, 128, 12, 1)
                    oled.text(label, 2, y + 2, 0)
                else:
                    oled.text(label, 2, y + 2, 1)
            oled.show()

        draw_id_list()

        # Delay to avoid button misclicks
        time.sleep(0.5)
        while button.value() == 0:
            time.sleep(0.01)

        last_button = 1

        while True:
            move = encoder.get()
            if move is not None:
                if move == 1:
                    selected = (selected + 1) % total
                    draw_id_list()
                elif move == -1:
                    selected = (selected - 1) % total
                    draw_id_list()

            button_state = button.value()

            if button_state == 0 and last_button == 1:
                time.sleep(0.05)

                if selected == len(self.saved_measurements):
                    self.run_menu(menu_manager)
                    return
                else:
                    self.view_details(oled, self.saved_measurements[selected])
                    draw_id_list()

            last_button = button_state
            time.sleep(0.01)

    def view_details(self, oled, measurement):
        # Show full HRV details for a selected measurement ID
        oled.fill(0)
        oled.text(f"HR: {measurement['mean_hr']} bpm", 2, 0)
        oled.text(f"PPI: {measurement['mean_ppi']} ms", 2, 12)
        oled.text(f"RMSSD: {measurement['rmssd']} ms", 2, 24)
        oled.text(f"SDNN: {measurement['sdnn']} ms", 2, 36)
        oled.show()
        time.sleep(5)
