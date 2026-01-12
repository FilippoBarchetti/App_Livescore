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
from file_config import simulation_speed, teams, general, l_teams

# Lista utilizzata per creare i threads che simulato le partite, quando tutti i threads sono partiti
# la lista è vuota ma quando terminano tutti sarà riempita con i nomi dei vincitori, quindi
# la sua lunghezza sarà dimezzata
l_winners = l_teams
stop_event = threading.Event()

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


class MatchRandomizerThread(threading.Thread):
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


class MasterThread(threading.Thread):
    def __init__(self, stop_event):
        super().__init__()
        self.stop_event = stop_event

    def run(self):
        global l_winners
        n_threads = 16
        while not self.stop_event.is_set():
            n_threads /= 2
            local_l_teams = general.find({"teams"})
            for i in range(n_threads):
                ws.write({})

                team1 = l_winners.pop(random.randint(0, l_teams - 1))
                team2 = l_winners.pop(random.randint(0, l_teams - 1))

                t_match = MatchRandomizerThread(
                    i + 1,
                    stop_event,
                    team1,
                    team2
                )

                t_match.start()

                while len(threading.enumerate()) != 2:
                    pass

                # Campionato finito, riparto da capo
                if n_threads == 2:
                    n_threads = 16
                l_winners = l_teams



""" Main """
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

    MasterThread(stop_event).start()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())