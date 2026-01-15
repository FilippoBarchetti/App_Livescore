import asyncio
import random
import logging
from asyncio import gather

import tornado.web
import tornado.websocket
import json
from file_config import simulation_speed, teams, general, l_teams, start_together

logger = logging.getLogger(__name__)

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

async def choose_players(team):
    players = {
        "goalkeeper": "",
        "reserve_goalkeeper": "",
        "forwards": "",
        "reserve_forwards": "",
        "defenders": "",
        "reserve_defenders": "",
    }
    # Goalkeepers
    goalkeepers = await team.find_one({"name": team})["goalkeepers"]
    players["goalkeeper"] = goalkeepers.pop(random.randrange(len(goalkeepers)))
    players["reserve_goalkeeper"] = goalkeepers.pop(random.randrange(len(goalkeepers)))

    # Forwards
    forwards_cursor = await team.find({"name": team})["forwards"]
    forwards = await forwards_cursor.to_list(length=None)
    for _ in range(2):
        players["forwards"] = forwards.pop(random.randrange(len(forwards)))
    for _ in range(4):
        players["reserve_forwards"] = forwards.pop(random.randrange(len(forwards)))

    # Defenders
    defenders_cursor = await team.find({"name": team})["defenders"]
    defenders = await defenders_cursor.to_list(length=None)
    for _ in range(2):
        players["defenders"] = defenders.pop(random.randrange(len(defenders)))
    for _ in range(4):
        players["reserve_defenders"] = defenders.pop(random.randrange(len(defenders)))

    return players


class Match():
    def __init__(self, id, team1, team2):
        self.team1 = team1
        self.team2 = team2
        self.punteggio1 = 0
        self.punteggio2 = 0
        self.id = id
        self.loop = True
        self.time_out = False
        self.seconds = 0
        self.players1 = asyncio.run(choose_players(self.team1))
        self.players2 = asyncio.run(choose_players(self.team2))

    async def simulate(self):
        while self.loop:
            # Formattazione messaggio orologio
            string_minutes = f"{self.seconds // 60}"
            string_seconds = f"{self.seconds % 60}"
            if self.seconds // 60 < 10:
                string_minutes = f"0{self.seconds // 60}"
            if self.seconds % 60 < 10:
                string_seconds = f"0{self.seconds % 60}"


            # Simulazione punteggio
            random_n = random.randint(0, 10000)
            if random_n < 10:
                self.punteggio1 += 1
            elif 9 < random_n < 20:
                self.punteggio2 += 1


            # Creazione e invio payload
            payload = {
                "phase_terminated": False,
                "id": {self.id},
                "time": f"{string_minutes}:{string_seconds}",
                "team1": self.team1,
                "team2": self.team2,
                "points": f"[{self.punteggio1} - {self.punteggio2}]",
                "players1": self.players1,
                "players2": self.players2
            }
            broadcast_message(payload)

            # Controllo se è ora del time-out (dopo 20 min)
            if self.seconds == 1200:
                # Aspetto 10 minuti = 600s -> (sim_speed//1000)*600 = (sim_speed*3)//5
                await asyncio.sleep(simulation_speed*3/5)

            # Controllo se la partita è finita
            if self.seconds == 2400:
                if self.punteggio1 > self.punteggio2:
                    l_winners.append(self.team1)
                else:
                    l_winners.append(self.team2)
                self.loop = False

            # Attesa e incremento timer
            await asyncio.sleep(simulation_speed/1000)
            print(payload, f"match {self.team1} vs {self.team2}")
            self.seconds += 1

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")


class DetailHandler(tornado.web.RequestHandler):
    def get(self, id):
        self.render("detail.html", id=id)


class WSHandler(tornado.websocket.WebSocketHandler):
    task_manager = ""
    task_match_simulator = ""
    loop_manager = False
    loop_match_simulator = False
    n_teams = 16

    def check_origin(self, origin):
        return True

    def open(self):
        connected_clients.add(self)
        print("WebSocket aperto")
        self.loop_manager = True
        self.task_manager = asyncio.create_task(self.manager())

    async def manager(self):
        global l_winners, concluded_matches, running_tasks
        while self.loop_manager:
            self.n_teams //= 2

            payload = {
                "phase_terminated": True,
                "n_matches": self.n_teams}
            broadcast_message(payload)

            for i in range(self.n_teams):
                team1 = l_winners.pop(random.randrange(len(l_winners)))
                team2 = l_winners.pop(random.randrange(len(l_winners)))
                print(f"MasterThread match {i}   n_threads: {self.n_teams}, team1: {team1}, team2: {team2}")
                match = Match(i + 1, team1, team2)
                if not start_together:
                    await asyncio.sleep(random.randint(0, 10)*simulation_speed/1000) # Range da 0s a 10s
                self.task_match_simulator = asyncio.create_task(match.simulate())
                running_tasks.append(self.task_match_simulator)
                print(f"Avviata task {i}")
            await asyncio.gather(*running_tasks)
            await asyncio.sleep(simulation_speed/200) # Aspetto 5s prima di fare partire il giro dopo
            print("finito primo giro")

            # Concluso campionato
            if self.n_teams == 1:
                l_winners = l_teams.copy()
                concluded_matches = 0
                running_tasks.clear()
                self.n_teams = 16



    def on_close(self):
        connected_clients.discard(self)
        print("WebSocket chiuso")


""" Main """
async def main():
    logging.basicConfig(level=logging.INFO)

    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/detail/([0-9]+)", DetailHandler),
            (r"/ws", WSHandler),
        ],
        template_path="templates",
        static_path="static"
    )

    app.listen(8000)
    print("Server Tornado avviato su http://localhost:8000")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
