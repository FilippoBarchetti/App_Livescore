import time
import random
import json
import datetime
import paho.mqtt.client as mqtt
import threading


from file_config import broker, topic_hockey_1, topic_hockey_2, topic_hockey_3, topic_hockey_4, topic_hockey_5

client = mqtt.Client()
client.connect(broker, 1883)
client.loop_start()

print("Sensori simulati avviati")

class Publisher(threading.Thread):
    def __init__(self, stop_event, sensor, unit):
        super().__init__(name=f"{sensor}_thread")
        self.stop_event = stop_event
        self.topic = f"sensor/{sensor}"
        self.sensor = sensor
        self.unit = unit

    def run(self):
        while not self.stop_event.is_set():
            value = round(random.uniform(18, 40), 2)

            payload = {
                "sensor": self.sensor,
                "value": value,
                "unit": self.unit,
                "time_stamp": datetime.datetime.now().strftime("%H:%M:%S")
            }

            client.publish(self.topic, json.dumps(payload))
            print("Pubblicato:", payload)

            time.sleep(1)

if __name__ == "__main__":
    stop_event = threading.Event()

    # Setup threads
    temperature_thread = Publisher(stop_event, "temperature", "°C")
    humidity_thread = Publisher(stop_event, "humidity", "%")
    pressure_thread = Publisher(stop_event, "pressure", "atm")

    # Start threads
    temperature_thread.start()
    humidity_thread.start()
    pressure_thread.start()

    # Loop e stop
    try:
        while True:
            pass
    except KeyboardInterrupt:
        stop_event.set()