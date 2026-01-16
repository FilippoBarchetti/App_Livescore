from motor.motor_asyncio import AsyncIOMotorClient
import json
import asyncio
import aiofiles


""" General Setup """
# Variabile configurare la velocità di simulazione del codice
# 1000: 1s (tempo normale) - 500: 0,5s (2x) - 2000: 2s (doppiamente lento)
simulation_speed = 1000 #1s
file_teams = "hockey_teams.json"
start_together = True

""" Setup Database """
# Setup generale Database
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["AppLivescore_db"]
teams = db["teams"]
l_teams = []

async def setup_db():
    await client.drop_database("AppLivescore_db")
    # Setup teams collection
    # Lettura file coi dati da inserire nel Database (teams)
    async with aiofiles.open(file_teams) as f:
        try:
            string_teams = await f.read()
        except FileNotFoundError:
            return
    # Inserimento dati nel Database (teams)
    dict_teams = json.loads(string_teams)
    await teams.insert_many(dict_teams)

    # Setup general_info collection
    for team in dict_teams:
        l_teams.append(team["name"])