import sys
import asyncio

# Ho dovuto specificare questa condizione perchè
# altrimenti, usando Windows, vi erano problemi
if sys.platform.startswith("win"):
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

import asyncio
import json
import logging
import tornado.web
import tornado.websocket
import aiomqtt

# Import broker e topics
from file_config import broker, topic_hockey_1, topic_hockey_2, topic_hockey_3, topic_hockey_4, topic_hockey_5

clients = set()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")


class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket aperto")
        clients.add(self)

    def on_close(self):
        print("WebSocket chiuso")
        clients.remove(self)


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

    asyncio.create_task(mqtt_listener())

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())