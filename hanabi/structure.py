# %% [markdown]
# ### Quantized Q-learning

# %%
from pickle import INST
import numpy as np
import networkx as nx
from game import Card, MyCard, Player
import GameData
from typing import *

from collections import Counter

class State(object):

    def __init__(self, table:int, others:List[Counter], mine: Counter) -> None:
        super().__init__()
        self.table = table
        self.others = others
        self.mine = mine

    def __hash__(self)->tuple:
        return (self.table, self.others, self.mine)

class Q_learner:
    
    actions = {"play": 0, "discard": 1, "hint-value": 2, "hint-color": 3}
    N_ACTIONS = len(actions)
    MAX_N_STATES = 5000
    discount_factor = 0.8
    color_value = {"blue": 0, "green": 1, "red": 2, "white": 3, "yellow": 4}
    value_color = {0: "blue", 1: "green", 2: "red", 3: "white", 4: "yellow"}

    

    CG = nx.Graph()


    def __init__(self, data: GameData.ServerStartGameData) -> None:

        self.local_Q_table = dict() # np.array((0, N_ACTIONS))
        # self.actions_table = np.array((0, self.N_ACTIONS))

        self.reward_table = dict() # np.array((len(self.q_table), self.N_ACTIONS))
        self.state_graph = nx.DiGraph()
        
    
        self.values_occurences = [3,2,2,2,1]
        self.color_occurrences = 10
        self.num_of_colors = 5
        self.num_players = len(data.players)

        self.my_cards_info = [{"color": None, "value": None, "position":None } for _ in range(5 if self.num_players>=4 else 4)]

        #======================
        self.old_state = None
        self.new_state = None
        #======================

        # self.card_in_pile = {
        #     "red":[3,2,2,2,1],
        #     "green":[3,2,2,2,1],
        #     "blue":[3,2,2,2,1],
        #     "yellow":[3,2,2,2,1],
        #     "white":[3,2,2,2,1]
        # }


    def build_collaboration_graph(self, players: List[Player])-> nx.Graph:
        """
            Create an undirected full connected graph where each edge rapresent 
            what other agents need to be taken into account
        """
        for i, player_1 in enumerate(players):
            for player_2 in players[i+1]:
                self.CG.add_edge(player_1, player_2)

        assert len(self.CG) == self.num_players * (self.num_players-1) / 2

    def add_state_graph(self, data: GameData.ServerGameStateData):
        """Add a new state to the data structures"""
        if self.new_state not in self.state_graph.nodes:
            self.local_Q_table[self.new_state] = [0 for _ in self.N_ACTIONS]
            self.reward_table = [0 for _ in self.N_ACTIONS]
            self.update_reward_table(data)


        if not self.state_graph.has_edge(self.old_state, self.new_state):
            self.state_graph.add_edge(self.old_state, self.new_state)
        
        
    def update_reward_table(self, data: GameData.ServerGameStateData):
        """For each possibile action compute the immediate reward"""
        for action, index in self.actions.items():
            self.reward_table[self.new_state][index] = self.compute_reward(data, action)
    
    def pick_an_action(self, random: bool):
        pass

    def retireve_global_Q_table(self):
        pass

    def update_local_Q_table(self):
        global_Q_table = self.retireve_global_Q_table()

    
    def learn(self, data: GameData.ServerGameStateData, learning=True) -> None:
        # TODO: Capire come gestire exploitation and exploration
        self.old_state = self.new_state
        self.new_state = self.evaluate_state(data)

        self.add_state_graph(data)

        self.update_local_Q_table()

        action = self.pick_an_action(learning)


        return action



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
    











    def get_color_from_index(self, index:int)->str:
        return self.value_color[index]

    def compute_reward(self, data:GameData.ServerGameStateData, action) -> int:

        if action == "hint":
            if data.usedNoteTokens == 0:
                return -10
        elif action == "discard":
            if data.usedNoteTokens == 8:
                return -10
            if self.count_played_cards(data) == 50:
                return self.table_score(data)
            else:
                return 10

        elif action == "play":
            if data.usedStormTokens == 3:
                return -10 
            if self.evaluate_table_state(data) == 25:
                return 25
            if self.last_correctly_played_card(data) == 5:
                return 10 
        
        return 0


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

        

    def get_probability_given_color(self, data, card_color)-> List[int]:
        # Sapendo che e' rosso probabilita' che sia un 1
        # Numero di 1 rossi nel mazzo / totale di carte rosse nel mazzo
        prob = []
        for card_value in range(1,6):
            den = self.get_numCard_per_color(data, card_color)
            if den == 0: 
                print("Division by zero")
                exit(0)
            prob.append((card_value, card_color,
                self.get_numCard_per_value_and_color(data, card_value, card_color)
                /
                den
            ))
        return max(prob, key=lambda x:x[2])


    def get_probability_given_value(self, data, card_value)-> List[int]:
        # Sapendo che e' un 1 probabilita' che sia rosso
        # Numero di 1 rossi nel mazzo / totale di 1 nel mazzo
        """
            Compute the conditional probability of being a specific color given the card value.
            Return a list with the probable card and its evaluation.
        """
        prob = []
        for card_color in ["red","green","blue","yellow","white"]:
            
            num = self.get_numCard_per_value_and_color(data, card_value, card_color)
            if num != 0:
                den = self.get_numCard_per_value(data, card_value)
                if den != 0: 
                    prob.append((card_value, card_color, num / den))
                    continue

            prob.append((card_value, card_color, 0))

        return prob #max(prob, key=lambda x:x[2])

    
    def received_hint(self, hint: GameData.ServerHintData):
        """
            Save the hint on the player hand. 
            The knowledge on the hand can be completed during the play and the probability evaluation change as consequence.
        """
        h_type = "color" if hint.type == "colour" else hint.type

        for i in hint.positions:
            self.my_cards_info[i-1][h_type] = hint.value
                
        
                
    def evaluate_my_state(self, data:GameData.ServerGameStateData):
        
        # If i have no information at all, no evaluation can be performed
        # if all([True if elem["position"] == None else False for elem in self.my_cards_info]):
        #     return 0

        # s = 0

        probable_hand = []
        # Questo ciclo genera un mazzo di carte probabile per poi essere valutato
        for my_card in self.my_cards_info:
            # Se non so nulla su questa carta non aggiungo punteggio
            if not my_card["color"] and not my_card["value"]:
                probable_hand.append(0)
                continue
            
            if not my_card["color"] and my_card["value"]:
                probable_hand.append((my_card["value"], -1))

            elif my_card["color"] and not my_card["value"]:
                probable_hand.append((-1, my_card["color"]))
            
            else:
                probable_hand.append((my_card["value"], my_card["color"]))

        # for color in data.tableCards:
        #     if not data.tableCards[color]: 
        #         max_val = 0
        #     else:
        #         max_val = max([card.value for card in data.tableCards[color]])

        #     res = []
        #     # Questo ciclo genera un mazzo di carte probabile per poi essere valutato
        #     for my_card in self.my_cards_info:
        #         # Se non so nulla su questa carta non aggiungo punteggio
        #         if not my_card["position"]:
        #             continue
                
        #         # Se so solo il valore o il colore calcolo il punteggio che ottengo considerando
        #         # di avere la carta con la probabilita' piu' alta di uscire
        #         if not my_card["color"] and my_card["value"]:
        #             res.append(self.get_probability_given_value(my_card["value"]))

        #         elif my_card["color"] and not my_card["value"]:
        #             res.append(self.get_probability_given_color(my_card["color"]))
                
        #         else:
        #             res.append((my_card["value"], my_card["color"], 1))

        #     # TODO: Creare una funzione che valuta delle carte in base alle carte sul tavolo

        #     # Faccio un sorting sul valore delle carte
        #     res.sort(key=lambda x:x[0])
        #     saved_prob = 0
        #     for card in res:
        #         if color == card[1] and max_val + 1 == card[0]:
        #             max_val = card[0]
        #             saved_prob = card[2]

        #     # Sommo il valore probabile moltiplicato per la probabilita' di accadere
        #     s += max_val #* saved_prob
        
        return Counter(probable_hand)


    def evaluate_other_players_state(self, data:GameData.ServerGameStateData):
        s = []
        # s = 0
        # discount = 1 / self.num_players

        # for i, player in enumerate(data.players):
            
        #     playerCards = sorted([(elem.value,elem.color) for elem in player.hand],key=lambda x: x[0])
        #     for color in data.tableCards:
        #         if not data.tableCards[color]: continue

        #         max_val = data.tableCards[color][0]
        #         for p_value, p_color in playerCards:
        #             if color != p_color:
        #                 continue
        #             if max_val + 1 == p_value:
        #                 max_val = p_value

        #         # Il punteggio degli altri diminuisce in base alla distanza che hanno da me
        #         s += max_val #* (self.num_players-i+1) * discount

        for player in data.players:
            s.append(Counter((card.value, self.color_value[card.color]) for card in player.hand))
        
        return s


    def evaluate_table_state(self, data:GameData.ServerGameStateData) -> int:
        """ Encode the table state in a BRCC integer where:
            - B is an integer that encode the number of used blue token [0. 8]
            - R is an integer that encode the number of used red token [0, 3]
            - CC is the score of the table in that particular observation [0, 25]
            The function return a number in the range [0, 8325]
        """
        
        return (8 - data.usedNoteTokens) * 10 + (3 - data.usedStormTokens)* 100 + self.table_score(data)
    

    def table_score(self, data:GameData.ServerGameStateData):
        s = 0
        for color in data.tableCards:
            s += max([v.value for v in data.tableCards[color]])
        
        assert s >=0 and s <= 25

        return s

