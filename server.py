import os
import GameData
import socket
from game import Game
from game import Player
import threading
from constants import *
#from signal import signal, SIGPIPE, SIG_DFL
import logging
import sys

mutex = threading.Lock()
# SERVER
playerConnections = {}
game = Game()

mutex = threading.Lock()

playersOk = []

statuses = [
    "Lobby",
    "Game"
]
status = statuses[0]

commandQueue = {}
numPlayers = 2


def manageConnections(conn: socket, addr):
    global status
    global game

    with conn:
        logging.info("Connected by: " + str(addr))
        keepActive = True
        playerName = ""
        while keepActive:
            print("SERVER WAITING")
            data = conn.recv(DATASIZE)

            mutex.acquire(True)

            if not data:
                #del playerConnections[playerName]
                logging.warning("Player disconnected: " + playerName)
                logging.info("Shutting down server")

                os._exit(0)

                game.removePlayer(playerName)
                if len(playerConnections) == 0:
                    logging.info("Shutting down server")
                keepActive = False
            else:
                print(f"SERVER PROCESSING {GameData.GameData.deserialize(data)}")
                data = GameData.GameData.deserialize(data)
                print(f"SERVER RECEIVED {type(data)} from {data.sender}")

                if status == "Lobby":
                    if type(data) is GameData.ClientPlayerAddData:
                        playerName = data.sender
                        commandQueue[playerName] = []
                        
                        # Control if the player name already exist in the game 
                        if playerName in playerConnections.keys() or playerName == "" and playerName is None:
                            logging.warning("Duplicate player: " + playerName)
                            conn.send(GameData.ServerActionInvalid("Player with that name already registered.").serialize())
                            mutex.release()
                            return
                        
                        # If it is ok add the player and send the Connection AcK to the player
                        playerConnections[playerName] = (conn, addr)
                        logging.info("Player connected: " + playerName)
                        game.addPlayer(playerName)
                        conn.send(GameData.ServerPlayerConnectionOk(playerName).serialize())

                    elif type(data) is GameData.ClientPlayerStartRequest:
                        # Player says that is Ok to start the game
                        game.setPlayerReady(playerName)
                        logging.info("Player ready: " + playerName)

                        # Sent to the player that the request is accepted
                        conn.send(GameData.ServerPlayerStartRequestAccepted(len(game.getPlayers()), game.getNumReadyPlayers()).serialize())
                        
                        # If all the player are ready we can start the game
                        if len(game.getPlayers()) == game.getNumReadyPlayers() and len(game.getPlayers()) >= numPlayers:
                            listNames = []
                            for player in game.getPlayers():
                                listNames.append(player.name)

                            logging.info("Game start! Between: " + str(listNames))
                            # Send to all the players that we are starting the game
                            for player in playerConnections:
                                playerConnections[player][0].send(GameData.ServerStartGameData(listNames).serialize())

                            game.start()

                    # This ensures every player is ready to send requests
                    # This message is sent from the client in response to the "ServerStartGameData" 
                    elif type(data) is GameData.ClientPlayerReadyData:
                        playersOk.append(1)

                    # If every player is ready to send requests, then the game can start
                    if len(playersOk) == len(game.getPlayers()):
                        status = "Game"

                        # Each player have a Queue of commands and inside the game interface we give a command
                        # and return the action we have to perform
                        # Some actions needs to be sended to all players other to only a specific one
                        for player in commandQueue:
                            for cmd in commandQueue[player]:
                                singleData, multipleData = game.satisfyRequest(cmd, player)

                                if singleData is not None:
                                    playerConnections[player][0].send(singleData.serialize())

                                if multipleData is not None:
                                    for id in playerConnections:
                                        playerConnections[id][0].send(multipleData.serialize())

                                        if game.isGameOver():
                                            # TODO: implement a game Over message to be sent to all players
                                            os._exit(0)

                        # Clear the queue for the game start
                        commandQueue.clear()

                    elif type(data) is not GameData.ClientPlayerAddData and \
                         type(data) is not GameData.ClientPlayerStartRequest and \
                         type(data) is not GameData.ClientPlayerReadyData:
                        commandQueue[playerName].append(data)

                # In game
                elif status == "Game":
                    singleData, multipleData = game.satisfyRequest(data, playerName)

                    if singleData is not None:
                        conn.send(singleData.serialize())
                        
                    if multipleData is not None:
                        for id in playerConnections:
                            playerConnections[id][0].send(multipleData.serialize())

                            if game.isGameOver():
                                logging.info("Game over")
                                logging.info("Game score: " + str(game.getScore()))
                                # os._exit(0)
                                players = game.getPlayers()
                                game = Game()
                                for player in players:
                                    logging.info("Starting new game")
                                    game.addPlayer(player.name)
                                game.start()
            mutex.release()



def manageNetwork():
    # Lauch a thread to listen for a the connection requests
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        logging.info("Hanabi server started on " + HOST + ":" + str(PORT))
        while True:
            s.listen()
            conn, addr = s.accept()
            threading.Thread(target=manageConnections, args=(conn, addr)).start()



if __name__ == '__main__':

    print("Type 'exit' to end the program")
    if len(sys.argv) > 1:
        if int(sys.argv[1]) > 1:
            numPlayers = int(sys.argv[1])

    logging.basicConfig(filename="game.log", 
                        level=logging.INFO, 
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt="%m/%d/%Y %I:%M:%S %p"
                        )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    network_thread = threading.Thread(target=manageNetwork)
    network_thread.start()

    # Start Terminal input Loop routine
    while True:
        data = input()
        if data == "exit":
            logging.info("Closing the server...")
            os._exit(0)
