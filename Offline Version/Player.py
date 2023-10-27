


class Player(object):
    def __init__(self, name) -> None:
        super().__init__()
        self.name = name
        self.ready = False
        self.hand = []

    def takeCard(self, cards):
        self.hand.append(cards.pop())

    def toString(self):
        c = "[ \n\t"
        for card in self.hand:
            c += "\t" + card.toString() + " \n\t"
        c += " ]"
        return ("Player " + self.name + " { \n\tcards: " + c + "\n}")

    def toClientString(self):
        c = "[ \n\t"
        for card in self.hand:
            c += "\t" + card.toClientString() + " \n\t"
        c += " ]"
        return ("Player " + self.name + " { \n\tcards: " + c + "\n}")