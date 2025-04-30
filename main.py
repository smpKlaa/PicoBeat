from machine import Pin, I2C
from menumanager import MenuManager
from historian import Historian
from networker import Networker
from hr_algo import HRA
from peripherals import RotaryEncoder
import time
import json
import ssd1306
import mip
import WIP_HRV
import introtext

SSID = "KMD657_Group_6"
PASSWORD = "Group0110"
BROKER_IP = "192.168.6.253"

SDA_PIN = 14
SCL_PIN = 15

class Main:
    def __init__(self):
        self.net = Networker(SSID, PASSWORD, BROKER_IP)
        
        # Initialize I2C pin and channel
        self.i2c = I2C(1, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
#         i2c.scan()
        # Initialize OLED with I2C pin
        self.OLED = ssd1306.SSD1306_I2C(128, 64, self.i2c)
        
        introtext.draw_splash_screen()
        
        # Initialize rotary encoder object
        self.re = RotaryEncoder(10, 11, scroll_speed=3)
        
        # Initialize HR algorithm object
        self.hra = HRA(display=self.OLED)
        
        # Initialize menu manager object
        self.menu = MenuManager(self.OLED, self.re)
        
        # Initialize historian object
        self.historian = Historian()
        
        # Connect to network and subscribe to MQTT
        self.net.connect_wifi()
#         self.net.install_mqtt()
        self.net.connect_mqtt("PicoBeat", "kubios-response", self.kubios_response)
        
        self.state = self.mainmenu
        self.previous_state = None
        self.message_received = False
    
    def execute(self):
        self.state()
        
    def change_state(self, _state):
        self.previous_state = self.state
        self.state = _state
        
    def mainmenu(self):
        selected = self.menu.run_main_menu()
        if selected == 0:
            self.change_state(self.measure_hr_0)
        elif selected == 1:
            self.change_state(self.measure_hr_1)
        elif selected == 2:
            self.change_state(self.measure_hr_2)
        elif selected == 3:
            self.change_state(self.history)
    
    def measure_hr_0(self):
        self.hra.start_recording(mode=0)
        self.change_state(self.previous_state)
    
    def measure_hr_1(self):
        peaks = self.hra.start_recording(mode=1)
#         print("PEAKS:", peaks)
        WIP_HRV.analyze_and_display(peaks, self.historian)
        self.change_state(self.mainmenu)
        
    def measure_hr_2(self):
        peaks = self.hra.start_recording(mode=2)
        if not peaks:
            self.change_state(self.mainmenu)
        
        print("PEAKS:", peaks)
        
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

    
    def history(self):
        self.historian.run_menu(self.menu)
        self.change_state(self.mainmenu)
        
    def kubios_response(self, topic, response):
#         self.message_received = True
        self.historian.add_measurement(response)
        print("Kubios results saved")
        

        
if __name__ == "__main__":
    main = Main()
    while True:
        main.execute()