import sys
import asyncio
import threading
import random

# Ho dovuto specificare questa condizione perchè
# altrimenti, usando Windows, vi erano problemi
if sys.platform.startswith("win"):
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

#import json
import logging
import tornado.web
import tornado.websocket
#import aiomqtt
from file_config import simulation_speed, teams
# Import broker e topics
# from file_config import broker, topic_hockey_1, topic_hockey_2, topic_hockey_3, topic_hockey_4, topic_hockey_5

#clients = set()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")


class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket aperto")
        #clients.add(self)

    def on_close(self):
        print("WebSocket chiuso")
        #clients.remove(self)


"""
async def mqtt_listener():

    logging.info("Connessione al broker MQTT...")

    async with aiomqtt.Client(broker) as client:
        # Ho dovuto usare una lista di tuple (topic, QoS)
        # QoS sta per quality of service e con QoS = 0
        # non ci sono conferme della ricezione del messaggio
        # ma la comunicazione è più veloce
        await client.subscribe([
            (topic_hockey_1, 0),
            (topic_hockey_2, 0),
            (topic_hockey_3, 0),
            (topic_hockey_4, 0),
            (topic_hockey_5, 0)
        ])
        logging.info(f"Iscritto ai topic: "
                     f"{topic_hockey_1}, "
                     f"{topic_hockey_2}, "
                     f"{topic_hockey_3}, "
                     f"{topic_hockey_4}, "
                     f"{topic_hockey_5}")

        async for message in client.messages:
            payload = message.payload.decode()
            data = json.loads(payload)

            ws_message = json.dumps({
                "type": "sensor",
                "data": data
            })

            # inoltro ai client WebSocket
            for c in list(clients):
                await c.write_message(ws_message)
"""

class MatchRandomizer(threading.Thread):
    def __init__(self, i, stop_event):
        super().__init__(name=f"match_{i}")
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            value = round(random.uniform(18, 40), 2)

            payload = {
                "sensor": self.sensor,
                "value": value,
                "unit": self.unit,
                "time_stamp": datetime.datetime.now().strftime("%H:%M:%S")
            }

""" MAIN """
async def main():
    logging.basicConfig(level=logging.INFO)

    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/ws", WSHandler),
        ],
        template_path="templates",
    )

    app.listen(8888)
    print("Server Tornado avviato su http://localhost:8888")

    #asyncio.create_task(mqtt_listener())

    cursor_teams = await teams.find_one({"name"})

    await asyncio.Event().wait()

""" START THREADS """
async def start_threads(n_threads, stop_event):
    # Setup e start threads
    for i in range(n_threads):
        await asyncio.sleep(random.randint(100, 10000)//simulation_speed)
        goalie = await teams.find_one({"name": "Sara Neri"})

        t_match = MatchRandomizer(
            i + 1,
            stop_event,)



if __name__ == "__main__":
    list_teams = []
    stop_event = threading.Event()
    asyncio.run(main())
    asyncio.run(start_threads(8, stop_event))

