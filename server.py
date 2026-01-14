import asyncio
import random
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

running_tasks = []
concluded_matches = 0

def broadcast_message(message):
    """Invia un messaggio JSON a tutti i client connessi"""
    for client in connected_clients:
        try:
            client.write_message(json.dumps(message))
        except Exception as e:
            logging.error(f"Errore invio: {e}")
    print("Invio")

class Match():
    def __init__(self, n, team1, team2):
        self.team1 = team1
        self.team2 = team2
        self.name = f"Match {n}"
        self.loop = True
        self.seconds = 0

    async def simulate(self):
        while self.loop:
            payload = {
                "time": f"{self.seconds // 60}:{self.seconds % 60}",
                "teams": f"{self.team1} vs {self.team2}",
                "new": "no"
            }
            broadcast_message(payload)
            await asyncio.sleep(simulation_speed)
            print(payload, f"match {self.team1} vs {self.team2}")
            self.seconds += 1

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")


class WSHandler(tornado.websocket.WebSocketHandler):
    task_manager = ""
    task_match_simulator = ""
    loop_manager = False
    loop_match_simulator = False
    manager_is_blocked = False
    n_teams = 16

    def check_origin(self, origin):
        return True

    def open(self):
        connected_clients.add(self)
        print("WebSocket aperto")
        self.loop_manager = True
        self.task_manager = asyncio.create_task(self.manager())

    async def manager(self):
        global l_winners, concluded_matches
        while self.loop_manager:
            if not self.manager_is_blocked:
                self.n_teams //= 2
                for i in range(self.n_teams):
                    team1 = l_winners.pop(random.randrange(len(l_winners)))
                    team2 = l_winners.pop(random.randrange(len(l_winners)))
                    print(f"MasterThread match {i}   n_threads: {self.n_teams}, team1: {team1}, team2: {team2}")
                    await self.write_message({"teams": f"{team1} vs {team2}", "new": "yes"})
                    match = Match(i + 1, team1, team2)
                    self.task_match_simulator = asyncio.create_task(match.simulate())
                    print(f"Avviata task {i}")
                    self.manager_is_blocked = True

            else:
                # Conclusa una fase del campionato
                if concluded_matches == self.n_teams//2:
                    self.manager_is_blocked = False
                # Concluso campionato
                if self.n_teams == 2:
                    l_winners = l_teams.copy()
                    concluded_matches = 0
                    self.manager_is_blocked = False



    def on_close(self):
        connected_clients.discard(self)
        print("WebSocket chiuso")


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

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
