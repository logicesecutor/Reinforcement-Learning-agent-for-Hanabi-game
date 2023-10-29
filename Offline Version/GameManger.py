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
    
    # Possible Actions
    __dataActions = {}

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
        self.__players = {}
        self.__currentPlayer = 0

        # Score
        self.__score = 0

        self.endGame = False

        # Add actions for each class of data
        self.__dataActions["PlayerDiscard"] = self.__satisfyDiscardRequest
        self.__dataActions["GameState"] = self.__satisfyShowCardRequest
        self.__dataActions["PlayerPlayCard"] = self.__satisfyPlayCardRequest
    #     self.__dataActions["Hint"] = self.__satisfyHintRequest


    # # Satisfy hint request
    # def __satisfyHintRequest(self, senderName: str):
    #     if self.__getCurrentPlayer().name != data.sender:
    #         return ("It is not your turn yet", None)
        
    #     if data.destination == data.sender:
    #         return ("You are giving a suggestion to yourself! Bad!", None)
        
    #     if self.__noteTokens == self.__MAX_NOTE_TOKENS:
    #         logging.warning("All the note tokens have been used. Impossible getting hints")
    #         return ("All the note tokens have been used", None)
        
    #     positions = []
    #     destPlayer: Player = None
    #     for p in self.__players:
    #         if p.name == data.destination:
    #             destPlayer = p
    #             break
    #     if destPlayer is None:
    #         return ("The selected player does not exist", None)

    #     for i in range(len(destPlayer.hand)):
    #         if data.type == "color" or data.type == "colour":
    #             if data.value == destPlayer.hand[i].color:
    #                 positions.append(i)
    #         elif data.type == "value":
    #             if data.value == destPlayer.hand[i].value:
    #                 positions.append(i)
    #         else:
    #             # Backtrack on note token
    #             self.__noteTokens -= 1
    #             return GameData.ServerInvalidDataReceived(data=data.type), None
    #         if data.sender == data.destination:
    #             self.__noteTokens -= 1
    #             return GameData.ServerInvalidDataReceived(data="Sender cannot be destination!"), None

    #     if len(positions) == 0:
    #         return GameData.ServerInvalidDataReceived(data="You cannot give hints about cards that the other person does not have"), None
    #     self.__nextTurn()
    #     self.__noteTokens += 1
    #     logging.info("Player " + data.sender + " providing hint to " + data.destination +
    #                  ": cards with " + data.type + " " + str(data.value) + " are in positions: " + str(positions))
    #     # ! ADDED last param. see GameData relative comment
    #     return None, GameData.ServerHintData(data.sender, data.destination, data.type, data.value, positions, self.__getCurrentPlayer().name)


    def manageInput(self):
        player = self.__getCurrentPlayer()
        input = input()


    # Play card request
    def __satisfyPlayCardRequest(self, senderName: str):
        player = self.__getCurrentPlayer()
        # it's the right turn to perform an action
        if player.name == senderName:
            if len(player.hand) == 0:
                return (f"{senderName} don't have that many cards!", None)
            
            card: Card = player.hand
            self.__playCard(player.name, data.handCardOrdered)
            ok = self.__checkTableCards()
            if not ok:
                self.__nextTurn()
                # ! ADDED last param. see GameData relative comment of GameData.ServerPlayerThunderStrike
                return (None,(self.__getCurrentPlayer().name, player.name, card, len(player.hand)))
            else:
                logging.info(self.__getCurrentPlayer().name +
                             ": card played and correctly put on the table")
                if card.value == 5:
                    logging.info(card.color + " pile has been filled.")
                    if self.__noteTokens > 0:
                        self.__noteTokens -= 1
                        logging.info("Giving 1 free note token.")
                self.__nextTurn()
                # ! ADDED last param. see GameData relative comment of GameData.ServerPlayerMoveOk
                return (None, self.__getCurrentPlayer().name, player.name, card, len(player.hand))
        else:
            return ("It is not your turn yet", None)
    

    def __playCard(self, playerName: str, cardPosition: int):
        player = self.__getPlayer(playerName)
        self.cardsOnTable[player.hand[cardPosition].color].append(player.hand[cardPosition])
        player.hand.pop(cardPosition)

        if len(self.cardsToDraw) > 0:
            player.hand.append(self.cardsToDraw.pop())


    def __getPlayer(self, currentPlayerName: str) -> Player:    
        return self.__players[currentPlayerName]


    def __getCurrentPlayer(self) -> Player:
        return self.__players[self.__currentPlayer]


    def printStatus(self):
        print(f"Current Player: {self.__getCurrentPlayer()}")


    def __satisfyDiscardRequest(self, senderName: str):
        player = self.__getCurrentPlayer()

        # It's the right turn to perform an action
        if player.name == senderName:
            if len(player.hand) == 0:
                return (f"{senderName} don't have that many cards!", None)
            
            card: Card = player.hand
            if not self.__discardCard(card.id, player.name):
                logging.warning("Impossible discarding a card: there is no used token available")
                return ("You have no used tokens", None)
            else:
                self.__drawCard(player.name)
                logging.info("Player: " + self.__getCurrentPlayer().name + ": card " + str(card.id) + " discarded successfully")
                self.__nextTurn()
                # ! ADDED last param. see GameData relative comment in ServerActionValid
                return (None, (self.__getCurrentPlayer().name, player.name, "discard", card, len(player.hand)))
        else:
            return ("It is not your turn yet", None)

    
    def __satisfyShowCardRequest(self, senderName: str):
        logging.info("Showing hand to: " + senderName)
        currentPlayer, playerList = self.__getPlayersStatus(senderName)
        return ((currentPlayer, playerList, self.__noteTokens, self.__stormTokens, self.__tableCards, self.__discardPile), None)


    def __getPlayersStatus(self, currentPlayerName):
        players = []
        for p in self.__players:
            #! I WANT ALSO THE ABSOLUTE ORDER OF PLAYERS
            if p.name == currentPlayerName:  # ! we don't want to cheat
                # ! so we build an 'empty' Player object for the requesting player
                tmp_player = Player(currentPlayerName)
                players.append(tmp_player)
            else:
                players.append(p)
        return (self.__players[self.__currentPlayer].name, players)
    

    # =========================================================
    def __discardCard(self, cardID: int, playerName: str) -> bool:
        # Ok only if you already used at least 1 token
        if self.__noteTokens < 1:  
            return False
        
        self.__noteTokens -= 1
        player : Player =  self.__players[playerName]

        for card in player.hand:
            if card.id == cardID:
                self.discardPile.append(card)  # discard
                player.hand.remove(card)  # remove from hand

        return True
    

    def __drawCard(self, playerName: str):
        if len(self.cardsToDraw) == 0:
            return
        
        player : Player =  self.__players[playerName]
        card = self.cardsToDraw.pop()

        if player.name == playerName:
            player.hand.append(card)


    def __nextTurn(self):
        self.__currentPlayer += 1
        self.__currentPlayer %= len(self.__players)
        

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


    def start(self, n_player):
        shuffle(self.cardsToDraw)
        self.__setPlayerNumber(n_player)


    def end(self):
        return self.endGame

    def __setPlayerNumber(self, n_player: int):
        for i in range(n_player):
            playerName = f"player_{i}"
            self.__players[playerName] = Player(name=playerName)