from machine import Pin, I2C
from menumanager import MenuManager
from historian import Historian
from networker import Networker
from hr_algo import HRA
from peripherals import RotaryEncoder
from led import Led
from piotimer import Piotimer
import time
import json
import ssd1306
import mip
import WIP_HRV
import introtext

SSID = "KMD657_Group_6"
PASSWORD = "Group0110"		# Lol
BROKER_IP = "192.168.6.253"

# Display pins
SDA_PIN = 14
SCL_PIN = 15

# Status LED objects.
PW_LED = Led(20)
WIFI_LED = Led(21)
    
PW_LED.on()


# Main state machine
class Main:
    def __init__(self):
        # Default startup state is mainmenu.
        self.state = self.mainmenu
        # Last state is stored for back tracking navigation.
        self.previous_state = None

        # Define networker object.
        self.net = Networker(SSID, PASSWORD, BROKER_IP)
        
        # Wifi connection check every 4 seconds.
        self.wifi_check_timer = Piotimer(mode = Piotimer.PERIODIC,
                                     freq = 0.25,
                                     callback = self.wifi_check_callback)
        
        # Initialize I2C pin and channel
        self.i2c = I2C(1, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
        # Initialize OLED object with I2C pin
        self.OLED = ssd1306.SSD1306_I2C(128, 64, self.i2c)
        
        # Draw statrup splash screen.
        introtext.draw_splash_screen()
        
        # Initialize rotary encoder object
        self.re = RotaryEncoder(10, 11, 12, scroll_speed=3)
        
        # Initialize HR algorithm object
        self.hra = HRA(display=self.OLED)
        # Initialize menu manager object
        self.menu = MenuManager(self.OLED, self.re)
        # Initialize historian object
        self.historian = Historian()
        
        # DEBUG
        # Maybe remove if rotary button is implemented
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)
        
        # Connect to network and subscribe to MQTT
        self.connected_to_wifi = self.net.connect_wifi()
        
        if not self.wifi_check():
            self.display_error("WIFICONN")
        else:
            self.net.sync_time() 	# Sync time with NTP
            self.net.connect_mqtt("PicoBeat",
                                  "kubios-response",
                                  self.kubios_response)
        

    def execute(self): # -------------------------------------------------------
        # Execute current state function.
        self.state()
        
    def wifi_check(self): # ----------------------------------------------------
        # wifi_check checks if WiFi is connected. Updates status variable and
        # status LED.
        self.connected_to_wifi = self.net.wifi_connected()
        if self.connected_to_wifi:
            WIFI_LED.on()
            return True
        else:
            WIFI_LED.off()
            return False
    
    def wifi_check_callback(self, _): # ----------------------------------------
        # Wrapper for interrupt callback function.
        self.wifi_check()
    
    
    def change_state(self, _state): # ------------------------------------------
        # Called to change state machine state. Saves previous state and updates
        # current state.
        self.previous_state = self.state
        self.state = _state
        
        
    def mainmenu(self): # ------------------------------------------------------
        # Displays the main menu with selection functionality.
        selected = self.menu.run_main_menu()
        
        # If-elif mess since python doesn't have switch-case.
        if selected == 0:	# 0 > Measure HR
            self.change_state(self.measure_hr_0)
        elif selected == 1:	# 1 > Basic HRV analysis
            self.change_state(self.measure_hr_1)
        elif selected == 2:	# 2 > Kubios HRV analysis
            self.change_state(self.measure_hr_2)
        elif selected == 3:	# 3 > History menu
            self.change_state(self.history)
            
    
    def measure_hr_0(self): # --------------------------------------------------
        # Start Heart Rate Algorithm, mode 0, no returned data.
        self.hra.start_recording(mode=0)
        # After measurement is stopped. Go back to main menu.
        self.change_state(self.previous_state)
        
    
    def measure_hr_1(self): # --------------------------------------------------
        # Start Heart Rate Algorithm, mode 1, PPI data is returned as array.
        peaks = self.hra.start_recording(mode=1)
        
        # Warning if PPI data is missing.
        if not peaks:
            print("WARNING: Not enough data for HRV analysis")
            self.change_state(self.mainmenu)
            return
        # Analyze and display results.
        WIP_HRV.analyze_and_display(peaks, self.historian)
        # Change state back to main menu.
        self.change_state(self.mainmenu)
        
        
    def measure_hr_2(self): # --------------------------------------------------
        # Check WiFi connection. Kubios analysis starts only if WiFi is
        # connected.
        if not self.connected_to_wifi:
            self.display_error("NOWIFICONN")
            return
        
        # Start Heart Rate Algorithm, mode 2, PPI data is returned as array.
        peaks = self.hra.start_recording(mode=2)
        
        # Warning if PPI data is missing.
        if not peaks:
            print("WARNING: Not enough data for Kubios HRV analysis")
            self.change_state(self.mainmenu)
            return
        # Define MQTT payload.
        payload = {
            "id": time.time(),	# Current time as ID
            "type": "RRI",
            "data": peaks,
            "analysis": {
                "type": "readiness"
                }
            }
        # Send data for analyzing.
        self.net.publish("kubios-request", json.dumps(payload))
        # Wait for MQTT response.
        self.net.wait_for_message()
        # Change state to main menu.
        self.change_state(self.mainmenu)

    
    def history(self): # -------------------------------------------------------
        # Display history menu.
        self.historian.run_menu(self.menu)
        # When history menu is closed. Go back to main menu.
        self.change_state(self.mainmenu)
        
        
    def kubios_response(self, topic, response): # ------------------------------
        # Callback function for MQTT responses.
        response = json.loads(response)
        if response["data"] == "Invalid request":
            print("ERROR: Kubios invalid request")
            self.display_error("INVALIDREQUEST")
            return
        self.historian.add_measurement(response)
        print("Kubios results saved")
        
        
    def display_error(self, error_message): # ----------------------------------
        # Basic error display.
        self.OLED.fill(0)
        self.OLED.text(f"E:{error_message}", 1, 1, 1)
        self.OLED.show()
        
        # When rotary button is clicked. Close error screen
        if self.button() == 1:
            while True:
                if self.button() == 0:
                    time.sleep(0.05)
                    if self.button.value() == 1:
                        self.change_state(self.mainmenu)
                        break

# Start main state machine.
if __name__ == "__main__":
    main = Main()
    while True:
        main.execute()
