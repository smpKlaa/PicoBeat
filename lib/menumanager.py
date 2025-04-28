import time
from machine import Pin

class MenuManager:
    # Class for handling the Main Menu systen and simple screen messages.
    def __init__(self, oled, encoder, button_pin):
        self.oled = oled
        self.encoder = encoder
        self.button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
        self.last_button = 1

    def run_main_menu(self):
        # Draw and run the main menu. Return selected choice.
        menu_items = [
            "Measure HR",
            "Basic HRV Analysis",
            "Kubios",
            "History"
        ]

        selected = 0 # Start with the first menu item
        self._draw_menu(menu_items, selected) # Draw the initial menu
        
        
        # Delay after entering Main Menu
        time.sleep(0.5)
        while self.button.value() == 0:
            time.sleep(0.01)

        while True:
            move = self.encoder.get()
            if move is not None:
                if move == 1:
                    selected = (selected + 1) % len(menu_items) # Scroll down
                    self._draw_menu(menu_items, selected)
                elif move == -1:
                    selected = (selected - 1) % len(menu_items) # Scroll up
                    self._draw_menu(menu_items, selected)

            if self.button.value() == 0 and self.last_button == 1:
                time.sleep(0.05)  # Fast debounce
                return selected # Return selected meu index

            self.last_button = self.button.value()
            time.sleep(0.01) # Small loop delay

    def show_collecting_screen(self):
        # Show a 'Collecting HR...' screen with a loading animation.
        self.oled.fill(0)
        self.oled.text("Collecting HR...", 2, 10)
        self.oled.rect(10, 40, 108, 10, 1)
        self.oled.show()
        
        # Animate filling loading bar
        for progress in range(1, 108, 5):
            self.oled.fill_rect(11, 41, progress, 8, 1)
            self.oled.show()
            time.sleep(0.05)

    def show_analysis_screen(self, results):
        # Show HRV analysis results on the screen.
        self.oled.fill(0)
        self.oled.text(f"HR: {results['mean_hr']} bpm", 2, 0)
        self.oled.text(f"PPI: {results['mean_ppi']} ms", 2, 12)
        self.oled.text(f"RMSSD: {results['rmssd']} ms", 2, 24)
        self.oled.text(f"SDNN: {results['sdnn']} ms", 2, 36)
        self.oled.show()
        time.sleep(5)

    def show_simple_message(self, message):
        # Show a simple short message.
        self.oled.fill(0)
        self.oled.text(message, 2, 25)
        self.oled.show()
        time.sleep(2)

    def _draw_menu(self, items, selected):
        # Draw the menu screen.
        self.oled.fill(0)
        for i, item in enumerate(items):
            y = i * 16
            if i == selected:
                self.oled.fill_rect(0, y, 128, 16, 1)
                self.oled.text(item, 2, y + 4, 0) # Invert text
            else:
                self.oled.text(item, 2, y + 4, 1) # Normal text
        self.oled.show()