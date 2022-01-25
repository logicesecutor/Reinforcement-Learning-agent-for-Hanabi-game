import networkx as nx
import GameData
from collections import Counter
from threading import Event


clustering = 5

class State:

    def __init__(self, tableCards, playersHand, myHand) -> None:
        super().__init__()
        self.tableCards = tableCards
        self.playersHand = playersHand
        self.myHand = myHand

    def __hash__(self)->tuple:
        return tuple(self.tableCards + self.playersHand + self.myHand)


    def distance(self, state_to_compare):
        res = 0 
        res += sum([abs(self.tableCards[i] - state_to_compare.tableCards[i]) for i in range(len(self.tableCards))])
        res += sum([abs(self.playersHand[i] - state_to_compare.playersHand[i]) for i in range(len(self.playersHand))])
        res += sum([abs(self.myHand[i] - state_to_compare.myHand[i]) for i in range(len(self.myHand))])

        return res




def find_nearest_state(state:State, states_table)-> State:
    """Questa funzione trova lo stato piu' vicino a quello dato"""
    minim = 10000000
    saved_state = None
    global clustering

    for s in states_table:
        dist = state.distance(s)

        if dist < clustering and dist < minim:
            minim = dist
            saved_state = s
     
    return saved_state


class Agent:

    def __init__(self) -> None:

        self.local_Q_table = dict() # np.array((0, N_ACTIONS))
        # self.actions_table = np.array((0, self.N_ACTIONS))

        self.reward_table = dict() # np.array((len(self.q_table), self.N_ACTIONS))
        self.state_graph = nx.DiGraph()
        
        self.agent_game_states = ["Lobby","Game","Learning"]
        self.agent_current_game_state = "Lobby"
        self.values_occurences = [3,2,2,2,1]
        self.color_occurrences = 10
        self.num_of_colors = 5
        self.num_players=None
        self.my_cards_info=None

        #======================
        self.old_state = None
        self.new_state = None
        #======================

    def empty(self):
        return not self.num_players
    
    def set_num_player(self, data):
        self.num_players = len(data.players)
        self.my_cards_info = [{"color": None, "value": None, "position":None } for _ in range(5 if self.num_players>=4 else 4)]

    def learn(self, data: GameData.ServerGameStateData, learning=True) -> None:
        # TODO: Capire come gestire exploitation and exploration
        self.old_state = self.new_state
        self.new_state = self.evaluate_state(data)

        # self.add_state_graph(data)

        # self.update_local_Q_table()

        # action = self.pick_an_action(learning)


        # return action
        return 

    def getCommand(self, status, takeInput:Event):

        res = ""
        takeInput.wait()

        if self.agent_current_game_state == "Lobby" and status == "Lobby":
            self.agent_current_game_state == "Game"
            res = "ready"

        if self.agent_current_game_state == "Game" and status == "Game":
            self.agent_current_game_state == "Learning"
            res = "show"
        

        if self.agent_current_game_state == "Learning" and status == "Game":
            res = self.learn()

        takeInput.clear()

        return res
         

    def evaluate_state(self, data:GameData.ServerGameStateData)-> State:
            """
                Try to univocly identifing the state of the game at time t:
                - Evaluate the cards on the table, the number of blue and red tokens.
                - Evaluate the card of the other players
                - Evaluate the hand this agent have        
            """

            table = self.evaluate_table_state(data)
            my_state = self.evaluate_my_state(data)
            others_state = self.evaluate_other_players_state(data)

            return State(table, others_state, my_state)


    def evaluate_my_state(self, data:GameData.ServerGameStateData):
        
        probable_hand = []
        # # Genero il mazzo di carte piu' probabile per poi valutarlo
        # for my_card in self.my_cards_info:
        #     # Se non so nulla su questa carta non aggiungo punteggio
        #     if not my_card["color"] and not my_card["value"]:
        #         probable_hand.append(0)
        #         continue
            
        #     if not my_card["color"] and my_card["value"]:
        #         probable_hand.append((my_card["value"], -1))

        #     elif my_card["color"] and not my_card["value"]:
        #         probable_hand.append((-1, my_card["color"]))
            
        #     else:
        #         probable_hand.append((my_card["value"], my_card["color"]))

        

        # Genero il mazzo di carte piu' probabile per poi valutarlo
        for i, my_card in enumerate(self.my_cards_info):
            # Se non so nulla su questa carta non aggiungo la carta al mazzo (punteggio tendenzialmente minore)
            if not my_card["color"]:
                continue
            
            # Se so solo il valore o il colore metto nel mazzo la carta con piu' probabilita' di uscire
            if not my_card["color"] and my_card["value"]:
                probable_hand.append({
                    "color": self.get_color_with_max_probability_given_value(my_card["value"]), 
                    "value": my_card["value"], 
                    "position":i })

            elif my_card["color"] and not my_card["value"]:
                probable_hand.append({
                    "color": my_card["color"], 
                    "value": self.get_value_with_max_probability_given_color(my_card["color"]), 
                    "position":i })
            
            else:
                probable_hand.append({
                    "color": my_card["color"], 
                    "value": my_card["value"], 
                    "position":i })

        # If i have no information at all, no evaluation can be performed
        if not probable_hand:
            return []


        # Current player-hand evaluation
        # TODO: Creare una funzione che valuta delle carte in base alle carte sul tavolo
        s = []
        # Faccio un sorting delle carte per valore
        sorted_hand = sorted([(elem.value,elem.color) for elem in probable_hand], key=lambda x: x[0])
        for color, cards in data.tableCards.items():
            
            max_val = len(cards)

            for p_value, p_color in sorted_hand:
                if color == p_color:
                    continue
                if max_val + 1 == p_value:
                    max_val = p_value

            # Moltiplico il valore probabile per la probabilita' di accadere
            s.append(max_val)  #* saved_prob
        
        return s#Counter(probable_hand)

    def compute_evaluation_of_player_hand(p_hand, data):
        res = []
        sorted_hand = sorted([(elem.value,elem.color) for elem in p_hand], key=lambda x: x[0])
        for color, cards in data.tableCards.items():
            
            max_val = len(cards)

            for p_value, p_color in sorted_hand:
                if color == p_color:
                    continue
                if max_val + 1 == p_value:
                    max_val = p_value

            # Sommo il valore probabile moltiplicato per la probabilita' di accadere
            res.append(max_val)  #* saved_prob

        return res


    def evaluate_other_players_state(self, data:GameData.ServerGameStateData, mode="score", discounted=False):
        """ 
            Two possible modes:
            - card_type: we use as evaluator the state number and the type of card that each player have -> dict of information 
            - scores: we use the max score that the player could perform with his hand in that specific time -> list of scores
        """

        if mode=="score":
            s = []
            discount = 1 / self.num_players

            for i, player in enumerate(data.players):
                # Faccio un sorting delle carte per valore
                playerCards = sorted([(elem.value,elem.color) for elem in player.hand], key=lambda x: x[0])

                for color, cards in data.tableCards.items():
                    # if that color on the table has no cards start with zero
                    max_val = len(cards)

                    for p_value, p_color in playerCards:
                        if color != p_color:
                            continue
                        if max_val + 1 == p_value:
                            max_val = p_value

                    # Il punteggio degli altri diminuisce in base alla distanza nel giro che gli altri hanno da me
                    s.append(max_val if not discounted else round(max_val * (self.num_players-i+1) * discount))

        elif mode=="card_type":
            s = []
            for player in data.players:
                s.append(Counter((card.value, self.color_value[card.color]) for card in player.hand))

        else:
            print("Mode is not valid!\n")
            return None
        
        return s


    def get_numCard_per_color(self, data:GameData.ServerGameStateData, color):
        num_counter = 0
        
        for name in data.players:
            for card in data.players[name]:
                if card.color == color:
                    num_counter += 1
        
        for card in data.discardPile:
            if card.color == color:
                    num_counter += 1
        
        for card in self.my_cards_info:
            if card["color"] == color:
                num_counter += 1

        return self.color_occurrences - num_counter # Carte nel mazzo di colore "color"


    def get_numCard_per_value(self, data:GameData.ServerGameStateData, number):

        num_counter = 0

        for name in data.players:
            for card in data.players[name]:
                if card.value == number:
                    num_counter += 1
        
        for card in data.discardPile:
            if card.value == number:
                    num_counter += 1
        
        for card in self.my_cards_info:
            if card["value"] == number:
                num_counter += 1

        return self.values_occurences[number-1] * 5 - num_counter  # Carte nel mazzo di valore "number"


    def get_numCard_per_value_and_color(self, data:GameData.ServerGameStateData, number, color):
        num_counter = 0
        
        for name in data.players:
            for card in data.players[name]:
                if card.value == number and card.color == color:
                    num_counter += 1
        
        for card in data.discardPile:
            if card.value == number and card.color == color:
                    num_counter += 1
        
        for card in self.my_cards_info:
            if card["value"] == number and card["color"] == color:
                num_counter += 1
        

        return self.values_occurences[number-1] - num_counter 

        

    def get_value_with_max_probability_given_color(self, data, card_color):
        # Sapendo che e' rosso, probabilita' che sia un 1
        # Numero di 1 rossi nel mazzo / totale di carte rosse nel mazzo
        """
            Compute the conditional probability of being a specific value given the card color.
            Return the value of the card with the highest probability or the first one in the case of equal probability.
        """
        card_prob = []
        for card_value in range(1,6):

            den = self.get_numCard_per_color(data, card_color)
            if den != 0: 
                num = self.get_numCard_per_value_and_color(data, card_value, card_color)
                card_prob.append((card_value, num / den ))
                continue

            card_prob.append(tuple(card_value, 0))

        return max(card_prob, key=lambda x:x[1])[0]


    def get_color_with_max_probability_given_value(self, data, card_value):
        # Sapendo che e' un 1, probabilita' che sia rosso
        # Numero di 1 rossi nel mazzo / totale di 1 nel mazzo
        """
            Compute the conditional probability of being a specific color given the card value.
            Return the color of the card with the highest probability or the first one in the case of equal probability.
        """
        card_prob = []
        for card_color in ["red","green","blue","yellow","white"]:
     
            den = self.get_numCard_per_value(data, card_value)
            if den != 0: 
                num = self.get_numCard_per_value_and_color(data, card_value, card_color)
                card_prob.append(tuple(card_color, num / den))
                continue

            card_prob.append(tuple(card_color, 0))

        return max(card_prob, key=lambda x:x[1])[0]


    def evaluate_table_state(self, data:GameData.ServerGameStateData) -> int:
        """ Encode the table state in a B-R-CC integer where:
            - B is an integer that encode the number of used blue token [0. 8]
            - R is an integer that encode the number of used red token [0, 3]
            - CC is the score of the table in that particular observation [0, 25]
            The function return a number in the range [0, 8325]
        """
        
        return [ 8 - data.usedNoteTokens, 3 - data.usedStormTokens, self.table_score(data) ]
    

    def table_score(self, data:GameData.ServerGameStateData):
        """Return the score of the card on the table at that istant t"""
        s = 0
        for color in data.tableCards:
            s += max([v.value for v in data.tableCards[color]])
        
        assert s >=0 and s <= 25

        return s