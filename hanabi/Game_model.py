class Player:

    def __init__(self, name,  hand) -> None:
        self.name = name
        self.hand = hand


class GameManager:

    def __init__(self, player: list) -> None:
        self.n_player = len(player)
        self.players = [Player(p.name, p.hand) for p in player]
        self.

    def generate_game(self):


    def distribute_cards():
        pass



