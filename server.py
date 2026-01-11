import sys
import asyncio
import threading
import random
import time

# Ho dovuto specificare questa condizione perchè
# altrimenti, usando Windows, vi erano problemi
if sys.platform.startswith("win"):
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

import logging
import tornado.web
import tornado.websocket
from file_config import simulation_speed, teams, general


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")


class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket aperto")

    def on_close(self):
        print("WebSocket chiuso")


class MatchRandomizer(threading.Thread):
    def __init__(self, i, stop_event, team1, team2):
        super().__init__(name=f"match_{i}")
        self.stop_event = stop_event
        self.team1 = team1
        self.team2 = team2
        self.seconds = 0

    def run(self):
        while not self.stop_event.is_set():
            payload = {
                "time": f"{self.seconds//60}:{self.seconds%60}",
                "teams": f"{self.team1} vs {self.team2}"
            }
            time.sleep(1000/simulation_speed)
            self.seconds += 1


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

    cursor_teams = await general.find({"name"})

    await asyncio.Event().wait()

""" START THREADS """
async def start_threads(n_threads):
    # Setup e start threads
    for i in range(n_threads):
        await asyncio.sleep(random.randint(1000, 10000)//simulation_speed)
        team1 = l_teams.pop(random.randint(0, l_teams - 1))
        team2 = l_teams.pop(random.randint(0, l_teams - 1))

        t_match = MatchRandomizer(
            i + 1,
            stop_event,
            team1,
            team2
        )



if __name__ == "__main__":
    stop_event = threading.Event()
    asyncio.run(main())
    asyncio.run(start_threads(8))