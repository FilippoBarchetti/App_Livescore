from pymongo import MongoClient
import json
import asyncio


""" Setup Topics """
# Uso un codice univoco per rendere i topic univoci
codice_univoco = "1ab3e67d9d8e3247"

broker = "test.mosquitto.org"

# Uso un topic per ogni match
topic_hockey_1 = f"{codice_univoco}/sport/hockey/1"
topic_hockey_2 = f"{codice_univoco}/sport/hockey/2"
topic_hockey_3 = f"{codice_univoco}/sport/hockey/3"
topic_hockey_4 = f"{codice_univoco}/sport/hockey/4"
topic_hockey_5 = f"{codice_univoco}/sport/hockey/5"



""" Setup Database """
# Creazione Database
client = MongoClient("mongodb://localhost:27017/")
db = client["AppLivescore_db"]
teams = db["teams"]

# Lettura file coi dati da inserire nel Database
file = "hockey_teams.json"
with open(file) as f:
    try:
        dict_teams = json.load(f)
    except FileNotFoundError:
        dict_teams = {}

# Inserimento dati nel Database
async def
ris = await teams.insert_many()

