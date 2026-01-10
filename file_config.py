from pymongo import MongoClient
import json
import asyncio



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
client = MongoClient("mongodb://localhost:27017/")

# Se il Database esiste già lo elimina
client.drop_database("AppLivescore_db")

# Creazione Database
db = client["AppLivescore_db"]
teams = db["teams"]

# Lettura file coi dati da inserire nel Database
file = "hockey_teams.json"
with open(file) as f:
    try:
        dict_teams = json.load(f)
    except FileNotFoundError:
        dict_teams = {}
print(dict_teams)
# Inserimento dati nel Database
ris = teams.insert_many(dict_teams)
