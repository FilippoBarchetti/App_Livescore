from pymongo import AsyncMongoClient
import json
import asyncio
import aiofiles


""" General Setup """
# Variabile configurare la velocità di simulazione del codice
# 1 <= simulation_speed <= 1000
simulation_speed = 1


""" Setup Topics """
# Uso un codice univoco per rendere i topic univoci
codice_univoco = "1ab3e67d9d8e3247"

broker = "test.mosquitto.org"

# Uso un topic per ogni match
topic_list = []
for i in range(8):
    topic_list.append(f"{codice_univoco}/sport/hockey/{i + 1}")
"""
topic_hockey_1 = f"{codice_univoco}/sport/hockey/1"
topic_hockey_2 = f"{codice_univoco}/sport/hockey/2"
topic_hockey_3 = f"{codice_univoco}/sport/hockey/3"
topic_hockey_4 = f"{codice_univoco}/sport/hockey/4"
topic_hockey_5 = f"{codice_univoco}/sport/hockey/5"
"""


""" Setup Database """
# Creazione client
client = AsyncMongoClient("mongodb://localhost:27017/")

# Se il Database esiste già lo elimina
async def drop_db():
    await client.drop_database("AppLivescore_db")
asyncio.run(drop_db())

# Creazione Database
db = client["AppLivescore_db"]
teams = db["teams"]
general = db["general_info"]

""" Setup teams collection """
async def setup_teams():
    # Lettura file coi dati da inserire nel Database (teams)
    file = "hockey_teams.json"
    async with aiofiles.open(file) as f:
        try:
            string_teams = await f.read()
            dict_teams = json.loads(string_teams)
        except FileNotFoundError:
            dict_teams = {}
    print(dict_teams)
    # Inserimento dati nel Database (teams)
    await teams.insert_many(dict_teams)
asyncio.run(setup_teams())

""" Setup general_info collection """
l_teams = []
def setup_general_info():
    cursor_teams = teams.find()
    async for team in cursor_teams:
        l_teams.append(team["name"])
    general.insert_one({"teams": l_teams})
setup_general_info()