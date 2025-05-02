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

SDA_PIN = 14
SCL_PIN = 15

PW_LED = Led(20)
WIFI_LED = Led(21)
        
PW_LED.on()

class Main:
    def __init__(self):
        self.state = self.mainmenu
        self.previous_state = None

        self.net = Networker(SSID, PASSWORD, BROKER_IP)
        
        self.wifi_check_timer = Piotimer(mode = Piotimer.PERIODIC,
                                     freq = 0.25,
                                     callback = self.wifi_check_callback)
        
        # Initialize I2C pin and channel
        self.i2c = I2C(1, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
#         i2c.scan()
        # Initialize OLED with I2C pin
        self.OLED = ssd1306.SSD1306_I2C(128, 64, self.i2c)
        
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
        # REMOVE WHEN ROTARY BUTTON IS IMPLEMENTED
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)
        
        # Connect to network and subscribe to MQTT
        self.connected_to_wifi = self.net.connect_wifi()
        if not self.wifi_check():
            self.display_error("WIFICONN")
        else: 
#         	self.net.install_mqtt()
            self.net.sync_time()
            self.net.connect_mqtt("PicoBeat",
                                  "kubios-response",
                                  self.kubios_response)
        self.state = self.mainmenu
        
    
    def execute(self): # -------------------------------------------------------
        self.state()
        
        
    def wifi_check(self):
        self.connected_to_wifi = self.net.wifi_connected()
        if self.connected_to_wifi:
            WIFI_LED.on()
            return True
        else:
            WIFI_LED.off()
            return False
        
    def wifi_check_callback(self, _):
        self.wifi_check()
        
    def change_state(self, _state): # ------------------------------------------
        self.previous_state = self.state
        self.state = _state
        
        
    def mainmenu(self): # ------------------------------------------------------
        selected = self.menu.run_main_menu()
        if selected == 0:
            self.change_state(self.measure_hr_0)
        elif selected == 1:
            self.change_state(self.measure_hr_1)
        elif selected == 2:
            self.change_state(self.measure_hr_2)
        elif selected == 3:
            self.change_state(self.history)
            
    
    def measure_hr_0(self): # --------------------------------------------------
        self.hra.start_recording(mode=0)
        self.change_state(self.previous_state)
        
    
    def measure_hr_1(self): # --------------------------------------------------
        peaks = self.hra.start_recording(mode=1)
        if not peaks:
            print("WARNING: Not enough data for HRV analysis")
            self.change_state(self.mainmenu)
            return
        WIP_HRV.analyze_and_display(peaks, self.historian)
        self.change_state(self.mainmenu)
        
        
    def measure_hr_2(self): # --------------------------------------------------
        if not self.connected_to_wifi:
            self.display_error("NOWIFICONN")
            return
        peaks = self.hra.start_recording(mode=2)
        if not peaks:
            print("WARNING: Not enough data for Kubios HRV analysis")
            self.change_state(self.mainmenu)
            return
        payload = {
            "id": time.time(),
            "type": "RRI",
            "data": peaks,
            "analysis": {
                "type": "readiness"
                }
            }
        self.net.publish("kubios-request", json.dumps(payload))
        self.net.wait_for_message()
        self.change_state(self.mainmenu)

    
    def history(self): # -------------------------------------------------------
        self.historian.run_menu(self.menu)
        self.change_state(self.mainmenu)
        
        
    def kubios_response(self, topic, response): # ------------------------------
        response = json.loads(response)
        if response.data == "Invalid request":
            print("ERROR: Kubios invalid request")
            self.display_error("INVALIDREQUEST")
            return
        self.historian.add_measurement(response)
        print("Kubios results saved")
        
        
    def display_error(self, error_message): # ----------------------------------
        self.OLED.fill(0)
        self.OLED.text(f"E:{error_message}", 1, 1, 1)
        self.OLED.show()
        if self.button() == 1:
            while True:
                if self.button() == 0:
                    time.sleep(0.05)
                    if self.button.value() == 1:
                        self.change_state(self.mainmenu)
                        break

        
if __name__ == "__main__":
    main = Main()
    while True:
        main.execute()