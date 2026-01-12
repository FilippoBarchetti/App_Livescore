#import sys
import asyncio
import threading
import random
import time

# Ho dovuto specificare questa condizione perchè
# altrimenti, usando Windows, vi erano problemi
"""if sys.platform.startswith("win"):
    from asyncio import WindowsSelectorEventLoopPolicy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())"""

import logging
import tornado.web
import tornado.websocket
import json
from file_config import simulation_speed, teams, general, l_teams

# Lista utilizzata per creare i threads che simulato le partite, quando tutti i threads sono partiti
# la lista è vuota ma quando terminano tutti sarà riempita con i nomi dei vincitori, quindi
# la sua lunghezza sarà dimezzata
l_winners = l_teams.copy()
connected_clients = set()


def broadcast_message(message):
    """Invia un messaggio JSON a tutti i client connessi"""
    for client in connected_clients:
        try:
            client.write_message(json.dumps(message))
        except Exception as e:
            logging.error(f"Errore invio: {e}")
    print("Invio")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")


class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        connected_clients.add(self)
        print("WebSocket aperto")


    def on_close(self):
        connected_clients.discard(self)
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
                "teams": f"{self.team1} vs {self.team2}",
                "new": "no"
            }
            broadcast_message(payload)

            time.sleep(simulation_speed)
            print(payload, f"match {self.team1} vs {self.team2}")
            self.seconds += 1


class MasterThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stop_master_event = stop_master_event
        self.stop_simulation_event = stop_simulation_event

    def run(self):
        global l_winners
        n_threads = 16
        blocked = False
        while not self.stop_master_event.is_set():
            if not blocked:
                n_threads //= 2
                print(f"n_threads: {n_threads}")
                for i in range(n_threads):
                    team1 = l_winners.pop(random.randrange(len(l_winners)))
                    team2 = l_winners.pop(random.randrange(len(l_winners)))
                    print(f"MasterThread match {i}   n_threads: {n_threads}, team1: {team1}, team2: {team2}")
                    broadcast_message({"teams": f"{team1} vs {team2}", "new": "yes"})
                    t_match = MatchRandomizerThread(
                        i + 1,
                        stop_simulation_event,
                        team1,
                        team2
                    )
                    t_match.start()
                    print(f"Avviato thread {i}")

                # Campionato finito, riparto da capo
                if n_threads == 2:
                    n_threads = 16
                l_winners = l_teams

                print("blocco thread master")
                blocked = True
            else:
                print("bloccato")
                if len(threading.enumerate()) == 2:
                    blocked = False



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

    app.listen(8000)
    print("Server Tornado avviato su http://localhost:8000")

    MasterThread().start()
    print("AvviaTO MasterThread")

    await asyncio.Event().wait()


if __name__ == "__main__":
    stop_master_event = threading.Event()
    stop_simulation_event = threading.Event()
    asyncio.run(main())