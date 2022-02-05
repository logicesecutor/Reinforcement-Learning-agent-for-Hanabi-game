#!/usr/bin/env python3

from sys import argv, stdout
from threading import Thread, Lock, Event

import GameData
import socket
from constants import *
from agent import Agent
import os


wait_operations_finish = Event()

getInput_event = Event()
getInput_event.set()

if len(argv) == 3:
    playerName = argv[1]
    epsilon = float(argv[2])
    ip = HOST
    port = PORT

elif len(argv) == 1:
    print("You need the player name to start the game.")
    #exit(-1)
    playerName = "Test" # For debug
    ip = HOST
    epsilon = 1.0
    port = PORT

else:
    playerName = argv[3]
    ip = argv[1]
    port = float(argv[2])

run = True


agent = Agent(playerName, epsilon)
chosen_action = 'None'
statuses = ["Lobby", "Game", "GameHint"]

status = statuses[0]

hintState = ("", "")

def manageInput():
    global run
    global status
    global agent
    global statuses

    global wait_operations_finish
    global chosen_action
    global getInput_event
    

    while run:
        #===================
        # The input is required olnly when is my turn
        # So I wait for the event
        getInput_event.wait()

        if agent.otherPlayerEnded == 0:
            command = agent.getCommand(status, wait_operations_finish)

        getInput_event.clear()
        #===================

        # Choose data to send
        if command == "exit":
            run = False
            os._exit(0)
        elif command == "ready" and status == statuses[0]:
            s.send(GameData.ClientPlayerStartRequest(playerName).serialize())
        elif command == "show" and status == statuses[1]:
            s.send(GameData.ClientGetGameStateRequest(playerName).serialize())
        elif command.split(" ")[0] == "discard" and status == statuses[1]:
            try:
                cardStr = command.split(" ")
                cardOrder = int(cardStr[1])

                chosen_action = cardOrder
                s.send(GameData.ClientPlayerDiscardCardRequest(playerName, cardOrder).serialize())
                
            except:
                print("Maybe you wanted to type 'discard <num>'?")
                getInput_event.set()
                continue
        elif command.split(" ")[0] == "play" and status == statuses[1]:
            try:
                cardStr = command.split(" ")
                cardOrder = int(cardStr[1])

                chosen_action = cardOrder
                s.send(GameData.ClientPlayerPlayCardRequest(playerName, cardOrder).serialize())

            except:
                print("Maybe you wanted to type 'play <num>'?")
                getInput_event.set()
                continue
        elif command.split(" ")[0] == "hint" and status == statuses[1]:
            try:
                destination = command.split(" ")[2]
                t = command.split(" ")[1].lower()
                if t != "colour" and t != "color" and t != "value":
                    print("Error: type can be 'color' or 'value'")
                    continue
                value = command.split(" ")[3].lower()
                if t == "value":
                    value = int(value)
                    if int(value) > 5 or int(value) < 1:
                        print("Error: card values can range from 1 to 5")
                        continue
                else:
                    if value not in ["green", "red", "blue", "yellow", "white"]:
                        print("Error: card color can only be green, red, blue, yellow or white")
                        continue
                s.send(GameData.ClientHintData(playerName, destination, t, value).serialize())

            except:
                print("Maybe you wanted to type 'hint <type> <destinatary> <value>'?")
                getInput_event.set()
                continue
        elif command == "":
            print("[" + playerName + " - " + status + "]: ", end="")
            getInput_event.set()
        else:
            print("Unknown command: " + command)
            getInput_event.set()
            continue
        stdout.flush()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    request = GameData.ClientPlayerAddData(playerName)
    s.connect((HOST, PORT))
    s.send(request.serialize())
    data = s.recv(DATASIZE)
    data = GameData.GameData.deserialize(data)
    if type(data) is GameData.ServerPlayerConnectionOk:
        print("Connection accepted by the server. Welcome " + playerName)
    print("[" + playerName + " - " + status + "]: ", end="")
    Thread(target=manageInput).start()
    while run:
        dataOk = False
        data = s.recv(DATASIZE)

        if not data:
            continue
        data = GameData.GameData.deserialize(data)

        if type(data) is GameData.ServerPlayerStartRequestAccepted:
            dataOk = True
            print("Ready: " + str(data.acceptedStartRequests) + "/"  + str(data.connectedPlayers) + " players")
            data = s.recv(DATASIZE)
            data = GameData.GameData.deserialize(data)

        if type(data) is GameData.ServerStartGameData:
            dataOk = True
            print("Game start!")
            s.send(GameData.ClientPlayerReadyData(playerName).serialize())
            status = statuses[1]

            getInput_event.set()

        # Satisfy the show request
        if type(data) is GameData.ServerGameStateData:
            # Turn is not changed
            dataOk = True

            agent.set_data(data)
                
            print("Current player: " + data.currentPlayer)
            print("Player hands: ")
            for p in data.players:
                print(p.toClientString())
            print("Table cards: ")
            for pos in data.tableCards:
                print(pos + ": [ ")
                for c in data.tableCards[pos]:
                    print(c.toClientString() + " ")
                print("]")
            print("Discard pile: ")
            for c in data.discardPile:
                print("\t" + c.toClientString())            
            print("Note tokens used: " + str(data.usedNoteTokens) + "/8")
            print("Storm tokens used: " + str(data.usedStormTokens) + "/3")

            # If is my turn
            if data.currentPlayer == playerName:
                getInput_event.set()

        #=========================================================================
        # Data Update Request
        if type(data) is GameData.ServerGameStateDataUpdate:
            # This is an update packet that each agent receives each time another agent
            # make an action
            dataOk = True
            agent.update_data(data)
            agent.update_players_action(data.players_action)

            agent.myturn = True if data.currentPlayer == agent.name else False
            if agent.myturn:
                getInput_event.set()
        #=========================================================================

        # An action not accomplished
        if type(data) is GameData.ServerActionInvalid:
            #This not change the turn so i need to perform another action
            dataOk = True
            print("Invalid action performed. Reason:")
            print(data.message)
            
            # Reset the event to obtain a new action
            getInput_event.set()

        # A discard succesfully make
        if type(data) is GameData.ServerActionValid:
            dataOk = True
            print("Action valid!")
            print("Current player: " + data.player)

            if data.lastPlayer == agent.name:
                s.send(GameData.ClientGetGameStateUpdateRequest(data.lastPlayer, "discard", chosen_action).serialize())

        # A play succesfully make
        if type(data) is GameData.ServerPlayerMoveOk:
            dataOk = True
            print("Nice move!")
            print("Current player: " + data.player)
             
            if data.lastPlayer == agent.name:
                s.send(GameData.ClientGetGameStateUpdateRequest(data.lastPlayer, "play good").serialize())

        # A play un-succesfully make
        if type(data) is GameData.ServerPlayerThunderStrike:
            dataOk = True
            print("OH NO! The Gods are unhappy with you!")

            if data.lastPlayer == agent.name:
                s.send(GameData.ClientGetGameStateUpdateRequest(data.lastPlayer, "play bad", chosen_action).serialize())

        if type(data) is GameData.ServerHintData:
            dataOk = True
 
            print("Hint type: " + data.type)
            print("Player " + data.destination + " cards with value " + str(data.value) + " are:")
            for i in data.positions:
                print("\t" + str(i))

            #==========================================
            quality = " bad"
            if len(data.positions) > 0:
                if data.destination == agent.name:
                    agent.update_my_cards_knowledge(data)
                else:
                    agent.update_other_players_knowledge(data)
                
                quality = " good" 

            assert quality
            # I sent the other players the update packet but only if I am the generator of the hint 
            # I forward to all of them, indeed tha agent will only update his info
            if data.source == agent.name:
                s.send(GameData.ClientGetGameStateUpdateRequest(data.source, "hint"+quality).serialize()) 
            #==========================================

        if type(data) is GameData.ServerInvalidDataReceived:
            # Turn is not changed
            dataOk = True
            print(data.data)
            # Reset the event to obtain another input from the agent
            getInput_event.set()

        if type(data) is GameData.ServerWaitOtherPlayer:
            dataOk=True
            agent.otherPlayerEnded += 1

            if agent.otherPlayerEnded == agent.num_players:
                wait_operations_finish.set()
                getInput_event.set()
            
        if type(data) is GameData.ServerGameOver:
            dataOk = True
            print(data.message)
            print(data.score)
            print(data.scoreMessage)
            stdout.flush()

            print("Ready for a new game!")

            agent.gameOver = True
            #status = "Lobby"

            #s.send(GameData.WaitOtherPlayerRequest(agent.name).serialize())
            getInput_event.set()
            

        if not dataOk:
            print("Unknown or unimplemented data type: " +  str(type(data)))
        print("[" + playerName + " - " + status + "]: ", end="")
        stdout.flush()

