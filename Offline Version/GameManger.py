from Card import Card
from Player import Player

from random import shuffle
from copy import deepcopy

import logging


class GameManager(object):

    __MAX_NOTE_TOKENS = 8
    __MAX_STORM_TOKENS = 3
    __MAX_FIREWORKS = 5

    # Cards for everyone
    cards = []
    colors = [
        "red",
        "yellow",  
        "green",  
        "blue",  
        "white", 
        "firework" 
              ]

    def __init__(self) -> None:
        super().__init__()

        self.discardPile = []
        self.gameOver = False
        # Init cards
        self.cards = self.__initDeck()
        self.cardsToDraw = deepcopy(self.cards)

        self.cardsOnTable = {
            "red": [],
            "yellow": [],
            "green": [],
            "blue": [],
            "white": []
        }

        # Init tokens
        self.__noteTokens = 0
        self.__stormTokens = 0

        # Init players
        self.__players = []
        self.__currentPlayer = 0

        # Score
        self.__score = 0

        # Add actions for each class of data
        self.__dataActions["PlayerDiscard"] = self.__satisfyDiscardRequest
        self.__dataActions["GameState"] = self.__satisfyShowCardRequest
        # self.__dataActions["PlayerPlayCard"] = self.__satisfyPlayCardRequest
        # self.__dataActions["Hint"] = self.__satisfyHintRequest
        

    def __getCurrentPlayer(self) -> Player:
        return self.__players[self.__currentPlayer]

    def __satisfyDiscardRequest(self, senderName: str):
        player = self.__getCurrentPlayer()

        # It's the right turn to perform an action
        if player.name == senderName:
            if len(player.hand) == 0:
                return logging(f"Player {player.name}: don't have that many cards!")
            card: Card = player.hand
            if not self.__discardCard(card.id, player.name):
                logging.warning(
                    "Impossible discarding a card: there is no used token available")
                return (GameData.ServerActionInvalid("You have no used tokens"), None)
            else:
                self.__drawCard(player.name)
                logging.info("Player: " + self.__getCurrentPlayer().name +
                             ": card " + str(card.id) + " discarded successfully")
                self.__nextTurn()
                # ! ADDED last param. see GameData relative comment in ServerActionValid
                return (None, GameData.ServerActionValid(self.__getCurrentPlayer().name, player.name, "discard", card, data.handCardOrdered, len(player.hand)))
        else:
            return (GameData.ServerActionInvalid("It is not your turn yet"), None)

    
    def __satisfyShowCardRequest(self, senderName: str):
        logging.info("Showing hand to: " + data.sender)
        currentPlayer, playerList = self.__getPlayersStatus(data.sender)
        return (GameData.ServerGameStateData(currentPlayer, playerList, self.__noteTokens, self.__stormTokens, self.__tableCards, self.__discardPile), None)

    # =========================================================
    def __discardCard(self, cardID: int, playerName: str) -> bool:
        # Ok only if you already used at least 1 token
        if self.__noteTokens < 1:  
            return False
        
        self.__noteTokens -= 1
        endLoop = False
        # find player
        for p in self.__players:
            if endLoop:
                break
            if p.name == playerName:
                # find card
                for card in p.hand:
                    if endLoop:
                        break
                    if card.id == cardID:
                        self.__discardPile.append(card)  # discard
                        p.hand.remove(card)  # remove from hand
                        endLoop = True
        return True

    def __initDeck(self):

        cardsList = []

        for color in self.colors:
            for _ in range(3):
                cardsList.append(Card(1, color))

            for _ in range(2):
                cardsList.append(Card(2, color))
                cardsList.append(Card(3, color))
                cardsList.append(Card(4, color))
            
            cardsList.append(Card(5, color))

        return cardsList


    def start(self):
        shuffle(self.__cardsToDraw)

    

