import asyncio
import random
import logging
from asyncio import gather
import tornado.web
import tornado.websocket
import json
from file_config import simulation_speed, teams, l_teams, start_together, setup_db



# Lista usata per creare tasks che simulano le partite, la lista viene svuotata durante la creazione
# delle tasks e riempita con i nomi dei vincitori al termine delle medesime tasks
l_winners = []
connected_clients = set() # Clients connessi
running_tasks = [] # Lista contenente le task attive
concluded_matches = 0 # Contatore per match terminati
current_id = None # id del match mostrato in details.html
logger = logging.getLogger(__name__)



def broadcast_message(message, id=None):
    """Invia un messaggio JSON a tutti i client connessi"""
    # Quando sono nella pagina di dettaglio, mando solo il messaggio relativo a quella partita
    print(current_id)
    if current_id and id != current_id:
        return
    # Non ho specificato l'id quindi sono nella pagina principale e mando a tutti
    print("invio")
    for client in connected_clients:
        try:
            client.write_message(json.dumps(message))
        except Exception as e:
            logger.error(e)



async def choose_players(team):
    players = {
        "goalkeeper": [],
        "reserve_goalkeeper": [],
        "forwards": [],
        "reserve_forwards": [],
        "defenders": [],
        "reserve_defenders": [],
    }
    """    doc_team = await teams.find_one({"name": team})
    goalkeepers = doc_team["players"]["goalkeepers"].copy()
    forwards = doc_team["players"]["forwards"].copy()
    defenders = doc_team["players"]["defenders"].copy()"""

    doc_team = await teams.find_one({"name": team})
    print("ok")
    players_data = doc_team.get("players", {})
    # Creiamo COPIE degli array per non modificare il documento originale
    goalkeepers = players_data.get("goalkeepers", []).copy()
    forwards = players_data.get("forwards", []).copy()
    defenders = players_data.get("defenders", []).copy()

    # Goalkeepers
    players["goalkeeper"].append(goalkeepers.pop(random.randrange(len(goalkeepers))))
    players["reserve_goalkeeper"].append(goalkeepers.pop(random.randrange(len(goalkeepers))))

    # Forwards
    for _ in range(2):
        players["forwards"].append(forwards.pop(random.randrange(len(forwards))))
    for _ in range(4):
        players["reserve_forwards"].append(forwards.pop(random.randrange(len(forwards))))

    # Defenders
    for _ in range(2):
        players["defenders"].append(defenders.pop(random.randrange(len(defenders))))
    for _ in range(4):
        players["reserve_defenders"].append(defenders.pop(random.randrange(len(defenders))))

    return players



class Match():
    def __init__(self, id, team1, team2):
        self.team1 = team1
        self.team2 = team2
        self.punteggio1 = 0
        self.punteggio2 = 0
        self.players1 = {}
        self.players2 = {}
        self.id = id
        self.loop = True
        self.seconds = 0

    async def init_players(self):
        self.players1 = await choose_players(self.team1)
        self.players2 = await choose_players(self.team2)

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
                "id": self.id,
                "time": f"{string_minutes}:{string_seconds}",
                "team1": self.team1,
                "team2": self.team2,
                "points": f"[{self.punteggio1} - {self.punteggio2}]",
                "players1": self.players1,
                "players2": self.players2
            }
            broadcast_message(payload, self.id)

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
            print(current_id, payload, f"match {self.team1} vs {self.team2}")
            self.seconds += 1



class MainHandler(tornado.web.RequestHandler):
    """ MainHandler """
    def get(self):
        global current_id
        self.render("main.html")
        current_id = None



class DetailHandler(tornado.web.RequestHandler):
    """ DetailHandler """
    def get(self, id):
        global current_id
        self.render("detail.html")
        current_id = id



class WSHandler(tornado.websocket.WebSocketHandler):
    """ Ws Handler """
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

            # Messaggio
            payload = {
                "phase_terminated": True,
                "n_matches": self.n_teams
            }
            broadcast_message(payload)
            print("messaggio inviato")

            # Creazione e avvio match (task)
            for i in range(self.n_teams):
                print(i)
                print(l_winners)
                print(random.randrange(len(l_winners)))
                # Prendo ranodmicamente 2 team a caso
                team1 = l_winners.pop(random.randrange(len(l_winners)))
                print("fatto?")
                team2 = l_winners.pop(random.randrange(len(l_winners)))
                match = Match(str(i + 1), team1, team2) # Creo oggetto match
                # Richiamo metodo per generare randomicamente i giocatori dei match
                print("gg1")
                await match.init_players()
                print("gg2")
                if not start_together:
                    await asyncio.sleep(random.randint(0, 10)*simulation_speed/1000) # Range da 0s a 10s
                # Creo e avvio task col metodo simulate dell'oggetto match (avvio simulazione partita)
                self.task_match_simulator = asyncio.create_task(match.simulate())
                running_tasks.append(self.task_match_simulator)
                logger.info("Avviata task {i}")


            # Attendo che i match siano conclusi
            await asyncio.gather(*running_tasks)
            await asyncio.sleep(simulation_speed/200) # Aspetto 5s prima di fare partire il giro dopo
            running_tasks.clear()

            # Concluso campionato
            if self.n_teams == 1:
                l_winners = l_teams.copy()
                concluded_matches = 0
                self.n_teams = 16

    def on_close(self):
        connected_clients.discard(self)
        print("WebSocket chiuso")



async def main():
    """ Main """
    global l_winners
    logging.basicConfig(level=logging.INFO)

    # Setup database
    await setup_db()
    l_winners = l_teams.copy()

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
    #await asyncio.Future()



if __name__ == "__main__":
    asyncio.run(main())