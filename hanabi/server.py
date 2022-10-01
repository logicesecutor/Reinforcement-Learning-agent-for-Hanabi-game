import os
import socket
import threading
import logging
import sys

import GameData
from game import Game
from constants import *
from argparse import ArgumentParser



mutex = threading.Lock()

# SERVER
playerConnections = {}
activeThreads = []
game = Game()

playersOk = []

statuses = ["Lobby", "Game"]

status = statuses[0]
commandQueue = {}
defaultNumPlayers = 2

sck_time_to_listen = 1.0 # Seconds
kill_threads = threading.Event()


def manageConnection(sck_connection: socket, addr):
    global status
    global game
    global playersOk
    global commandQueue
    
    with sck_connection:
        logging.info("Connected by: " + str(addr))
        keepActive = True

        playerName = ""
        while keepActive:

            print("SERVER WAITING")
            data = sck_connection.recv(DATASIZE)

            mutex.acquire(True)
            # If one player disconnect we have to chose
            if not data:
                del playerConnections[playerName]
                logging.warning("Player disconnected: " + playerName)
                if status=="Game":
                    logging.info("Game already started. Cant update all players.\nClosing Game")
                    os._exit(0)

                game.removePlayer(playerName)
                if len(playerConnections) == 0:
                    logging.info("Not enough player.\nShutting down server")
                    os._exit(0)

                # keepActive = False
            else:

                # Valid data need to be deserialized and managed
                print(f"SERVER PROCESSING {GameData.GameData.deserialize(data)}")
                data = GameData.GameData.deserialize(data)
                print(f"SERVER RECEIVED {type(data)} from {data.sender}")

                if status == "Lobby":
                    if type(data) is GameData.ClientPlayerAddData:

                        playerName = data.sender

                        if playerName in playerConnections.keys() or playerName == "" or playerName is None:
                            logging.warning("Duplicate player: " + playerName)
                            sck_connection.send(GameData.ServerActionInvalid("Player with that name already registered.").serialize())
                            mutex.release()
                            return

                        commandQueue[playerName] = []
                        playerConnections[playerName] = (sck_connection, addr)

                        logging.info("Player connected: " + playerName)
                        game.addPlayer(playerName)

                        # Send to the player that he connected succesfully
                        sck_connection.send(GameData.ServerPlayerConnectionOk(playerName).serialize())

                    elif type(data) is GameData.ClientPlayerStartRequest:
                        game.setPlayerReady(playerName)
                        logging.info("Player ready: " + playerName)
                        sck_connection.send(GameData.ServerPlayerStartRequestAccepted(len(game.getPlayers()), game.getNumReadyPlayers()).serialize())
                        if len(game.getPlayers()) == game.getNumReadyPlayers() and len(game.getPlayers()) >= numPlayers:
                            listNames = []
                            for player in game.getPlayers():
                                listNames.append(player.name)
                            logging.info(
                                "Game start! Between: " + str(listNames))
                            for player in playerConnections:
                                playerConnections[player][0].send(
                                    GameData.ServerStartGameData(listNames).serialize())
                            game.start()
                    # This ensures every player is ready to send requests
                    elif type(data) is GameData.ClientPlayerReadyData:
                        playersOk.append(1)
                    # If every player is ready to send requests, then the game can start
                    if len(playersOk) == len(game.getPlayers()):
                        status = "Game"
                        for player in commandQueue:
                            for cmd in commandQueue[player]:
                                singleData, multipleData = game.satisfyRequest(
                                    cmd, player)
                                if singleData is not None:
                                    playerConnections[player][0].send(
                                        singleData.serialize())
                                if multipleData is not None:
                                    for id in playerConnections:
                                        playerConnections[id][0].send(
                                            multipleData.serialize())
                                        if game.isGameOver():
                                            os._exit(0)
                        commandQueue.clear()
                    elif type(data) is not GameData.ClientPlayerAddData and type(
                            data) is not GameData.ClientPlayerStartRequest and type(
                            data) is not GameData.ClientPlayerReadyData:
                        commandQueue[playerName].append(data)
                # In game
                elif status == "Game":
                    singleData, multipleData = game.satisfyRequest(
                        data, playerName)
                    if singleData is not None:
                        #====================================
                        if type(singleData) is list:
                            for i, id in enumerate(playerConnections):
                                playerConnections[id][0].send(
                                    singleData[i].serialize())
                        #====================================
                        else:
                            conn.send(singleData.serialize())

                    if multipleData is not None:
                        for id in playerConnections:
                            playerConnections[id][0].send(
                                multipleData.serialize())

                            if game.isGameOver():# and game.playerEnded == len(game.getPlayers()):
                                logging.info("Game over")
                                logging.info("Game score: " +
                                             str(game.getScore()))
                                # os._exit(0)
                                #=============================
                                # players = game.getPlayers()
                                # status = "Lobby"
                                # playersOk.clear()
                                # #game.playerEnded = 0
                                # game = Game()
                                # for player in players:
                                #     logging.info("Starting new game")
                                #     player.ready = False
                                #     game.addPlayer(player.name)
                                #     commandQueue[player.name] = []
                                #==============================
                                # game.start()
            mutex.release()


def manageNetwork():

    global activeThreads

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
        # sck.settimeout(sck_time_to_listen)
        sck.bind((HOST, PORT))
        logging.info("Hanabi server started on " + HOST + ":" + str(PORT))

        counter = 0
        while True:
            sck.listen()
            conn, addr = sck.accept()

            connectionManager = threading.Thread(name=f"connectionManager_{counter}", target=manageConnection, args=(conn, addr))
            connectionManager.start()

            activeThreads.append(connectionManager)
            counter += 1


def manageServerInput():
    print("Type 'exit' to end the program\n",
          "Type 'restart' to restart the Game")

    while True:
        #Take the input Server-Side
        data = input()

        if data == "exit":
            logging.info("Closing the server...")
            # os._exit(0)
            return data

        elif data == "restart":
            logging.info("Restarting the server...")
            return data
        else:
            logging.info("INVALID INPUT!")
            continue


def start_server():

    logging.basicConfig(filename="game.log", level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt="%m/%d/%Y %I:%M:%S %p")
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    
    # Starting 
    while True:
        networkThread = threading.Thread(name="networkThread", target=manageNetwork)
        networkThread.start()
        activeThreads.append(networkThread)
        
        ret_value = manageServerInput()
        
        if  ret_value == "restart": break#continue
        elif ret_value == "exit": sys.exit("Server Closed")
        



if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-p', "--numPlayer", type=int, help="Number of player to add")
    args = parser.parse_args()

    numPlayers = args.numPlayer if args.numPlayer is not None else defaultNumPlayers
    start_server()
