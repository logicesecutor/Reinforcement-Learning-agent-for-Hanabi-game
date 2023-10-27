class Token(object):
    def __init__(self, type) -> None:
        super().__init__()
        self.type = type
        self.flipped = False

    def toString(self):
        return ("Token " + self.type + "; Flipped: " + str(self.flipped))