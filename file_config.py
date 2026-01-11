from pymongo import AsyncMongoClient
import json
import asyncio
import aiofiles


""" General Setup """
# Variabile configurare la velocità di simulazione del codice
# 1 <= simulation_speed <= 1000
simulation_speed = 1
file_teams = "hockey_teams.json"


""" Setup Database """
# Setup generale Database
client = AsyncMongoClient("mongodb://localhost:27017/")
db = client["AppLivescore_db"]
teams = db["teams"]
general = db["general_info"]
l_teams = []

async def setup_db():
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
    await general.insert_one({"teams": l_teams})
asyncio.run(setup_db())