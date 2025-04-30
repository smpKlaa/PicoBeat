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
        try:
            with open(self.filename, "x") as f:  # Create only if it doesn't exist
                pass  # Just create an empty file
        except FileExistsError:
            pass  # File already exists — do nothing
        except Exception as e:
            print("Error creating history file:", e)

    def load_history(self):
        self.saved_measurements = []
        try:
            with open(self.filename, "r") as f:
                for line in f:
                    if line.strip():
                        self.saved_measurements.append(json.loads(line))
        except Exception:
            self.saved_measurements = []
            self.create_history()
        #load from newest to oldest
        self.saved_measurements.sort(key=lambda x: x["time"], reverse=True)

    def add_measurement(self, measurement):
    # Ensure file exists
        try:
            with open(self.filename, "r"):
                pass
        except OSError:
            self.create_history()

        # Append to file
        try:
            with open(self.filename, "a") as f:
                json.dump(measurement, f)
                f.write("\n")
        except Exception as e:
            print("Error appending to history:", e)

        # ✅ Refresh in-memory list from file
        self.load_history()

        # Trim to max entries
        if len(self.saved_measurements) > self.max_entries:
            self.saved_measurements = self.saved_measurements[-self.max_entries:]

    def run_menu(self, menu_manager):
        self.load_history()
        oled = menu_manager.oled
        encoder = menu_manager.encoder
        button = menu_manager.button

        if not self.saved_measurements:
            oled.fill(0)
            oled.text("No measurements!", 2, 25)
            oled.show()
            time.sleep(2)
            return

        selected = 0

        def draw_measurement_list():
            total = len(self.saved_measurements)
            oled.fill(0)
            oled.text("HRV Records:", 2, 0)

            # Determine start index to scroll
            start = max(0, selected - 1)
            end = min(start + 4, total)

            for i, index in enumerate(range(start, end)):
                ts = time.localtime(self.saved_measurements[index]["time"])
                label = "{:02d}:{:02d}, {:02d}/{:02d}/{:02d}".format(
                    ts[3], ts[4], ts[2], ts[1], ts[0] % 100)  # ts[0] % 100 gives 2-digit year
                y = (i + 1) * 12
                if index == selected:
                    oled.fill_rect(0, y, 128, 12, 1)
                    oled.text(label, 2, y + 2, 0)
                else:
                    oled.text(label, 2, y + 2, 1)
            oled.show()

        draw_measurement_list()

        time.sleep(0.5)
        while button.value() == 0:
            time.sleep(0.01)

        last_button = 1
        button_pressed_time = None
        held_long_enough = False

        while True:
            move = encoder.get()
            if move is not None:
                if move == 1:
                    selected = (selected + 1) % len(self.saved_measurements)
                    draw_measurement_list()
                elif move == -1:
                    selected = (selected - 1) % len(self.saved_measurements)
                    draw_measurement_list()

            button_state = button.value()

            if button_state == 0:  # Button is pressed
                if button_pressed_time is None:
                    button_pressed_time = time.ticks_ms()
                elif time.ticks_diff(time.ticks_ms(), button_pressed_time) >= 1000:
                    held_long_enough = True
            else:  # Button is released
                if button_pressed_time is not None:
                    # On release, decide what to do
                    if held_long_enough:
                        return  # Exit to main menu
                    else:
                        self.view_details(oled, self.saved_measurements[selected], button)
                        draw_measurement_list()
                    # Reset timing
                    button_pressed_time = None
                    held_long_enough = False

            last_button = button_state
            time.sleep(0.01)

    def view_details(self, oled, measurement, button):
        oled.fill(0)
        ts = time.localtime(measurement['time'])

        # Format: HH:MM  DD/MM/YYYY
        oled.text("{:02d}:{:02d} {:02d}/{:02d}/{:04d}".format(
            ts[3], ts[4], ts[2], ts[1], ts[0]), 0, 0)

        oled.text(f"HR: {measurement['mean_hr']} bpm", 0, 12)
        oled.text(f"PPI: {measurement['mean_ppi']} ms", 0, 24)
        oled.text(f"RMSSD: {measurement['rmssd']} ms", 0, 36)
        oled.text(f"SDNN: {measurement['sdnn']} ms", 0, 48)

        oled.show()

        button_pressed_time = None
        held_long_enough = False

        while True:
            if button.value() == 0:  # Button is pressed
                if button_pressed_time is None:
                    button_pressed_time = time.ticks_ms()
                elif time.ticks_diff(time.ticks_ms(), button_pressed_time) >= 1000:
                    held_long_enough = True
            else:  # Button is released
                if held_long_enough:
                    return  # Exit only after release, and if held long enough
                else:
                    button_pressed_time = None  # Reset if not held long enough

            time.sleep(0.01)

