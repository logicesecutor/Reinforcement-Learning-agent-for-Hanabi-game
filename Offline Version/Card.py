import itertools

class Card(object):

    idCounter = itertools.count()

    def __init__(self, value, color) -> None:
        super().__init__()
        self.value = value
        self.color = color
        
        self.id = next(Card.idCounter)


    def toString(self):
        return ("Card " + str(self.id) + "; value: " + str(self.value) + "; color: " + str(self.color))

    def toClientString(self):
        return ("Card " + str(self.value) + " - " + str(self.color))

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id


