import network
import time
import mip
import ntptime
from umqtt.simple import MQTTClient

class Networker:
    # Handles WiFi and MQTT connection
    def __init__(self, ssid, password, broker_ip):
        self.ssid = ssid
        self.password = password
        self.broker_ip = broker_ip
        self.client = None

    def connect_wifi(self):
        # Connect to WiFi network
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print("Connecting to WiFi...")
            self.wlan.connect(self.ssid, self.password)

            retry = 0
            while not self.wlan.isconnected() and retry < 5:
                time.sleep(1)
                print("Connecting...")
                retry += 1
            if retry >= 5:
                print("WARNING: Failed to connect to wifi. Offline mode on.")
                return False
        
        if self.wlan.isconnected():
            print("Connected to WiFi. IP:", self.wlan.ifconfig()[0])
            return True
        else:
            raise RuntimeError("Failed to connect to WiFi")
        
    def wifi_connected(self):
        if self.wlan:
            if self.wlan.isconnected():
                return True
            else:
                return False
        else:
            return False
        
    def sync_time(self):
        print("Syncing RTC")
        try:
            ntptime.settime()
        except Exception as e:
            print(f"WARNING: Time syncronation failed: {e}")
            return
        print(f"Time syncronation successful. {time.localtime()}")

    def install_mqtt(self):
        try:
            mip.install("umqtt.simple")
        except Exception as e:
            print(f"Could not install MQTT: {e}")

    def connect_mqtt(self, client_id, sub_topic=None, callback=None):
        # Connect to MQTT broker and subscribe to a topic
        self.client = MQTTClient(client_id, self.broker_ip, port=21883)

        if callback:
            self.client.set_callback(callback)

        print("Connecting to MQTT Broker...")
        self.client.connect()
        print("Connected to MQTT Broker.")

        if sub_topic:
            self.client.subscribe(sub_topic)
            print(f"Subscribed to topic: {sub_topic}")

    def publish(self, topic, payload):
        # Publish a message to a topic
        if self.client:
            print(f"Publishing to {topic}...")
            self.client.publish(topic, payload)

    def check_messages(self):
        # Check for incoming MQTT messages
        if self.client:
            self.client.check_msg()

    def wait_for_message(self):
        # Wait for a single incoming MQTT message
        if self.client:
            self.client.wait_msg()

    def disconnect(self):
        # Disconnect from MQTT broker
        if self.client:
            self.client.disconnect()
            print("Disconnected from MQTT.")
