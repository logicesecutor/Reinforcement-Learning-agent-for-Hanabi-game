import random
import sys
from typing import List


CARDS_COLORS = ["red", "yellow", "white", "green", "blue"]
CARDS_VALUES = {1:3, 2:2, 3:2, 4:2, 5:1}


class Card:
    def __init__(self, color, value) -> None:
        self.color = color
        self.value = value

class Player:

    def __init__(self, name, hand: List[Card]) -> None:
        self.name = name
        self.hand = hand

class GameSession:

    def __init__(self) -> None:
        pass

class GameManager:

    def __init__(self, player_names: list) -> None:
        self.n_player = len(player_names)
        self.hint_token = 8
        self.group_life_token = 3
        self.card_pile = [
            Card(color=color, value=k)
                for color in CARDS_COLORS
                    for k, v in CARDS_VALUES.items()
                        for _ in range(v)]
        random.shuffle(self.card_pile)
        self.players = [Player(p, self.create_hand(self.n_player, self.card_pile)) for p in player_names]

        self.active_player = random.randrange(start=0, stop=len(player_names))


    def create_hand(self, n_player: int, card_pile: list):
        if n_player > 1 and n_player < 4:
            n_card_to_assign = 5
        elif n_player > 3 and n_player < 5:
            n_card_to_assign = 4
        else:
            print("Error on number of player", file=sys.stderr)
            return 

        return [card_pile.pop() for _ in range(n_card_to_assign) ]


    def StartGame(self):
        pass

    def Stop(self):
        pass


if  __name__ == "__main__":

    players_name = ["mario", "giovanni", "marco"]
    gm = GameManager(players_name)
    gm.StartGame()

    command = input()
    if command == "stop":
        gm.Stop()
