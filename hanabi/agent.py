from copy import deepcopy 
import networkx as nx
import GameData
from collections import Counter
from random import random, randrange
import pickle

clustering = 5

class State:

    def __init__(self, tableCards=[], playersHand=[], myHand=[], empty=False) -> None:
        super().__init__()
        self.tableCards = tableCards
        self.playersHand = playersHand
        self.myHand = myHand
        self.empty = empty

    def __hash__(self)->tuple:
        return hash(tuple(self.tableCards + self.playersHand + self.myHand))


    def distance(self, state_to_compare):
        res = 0 
        res += sum([abs(self.tableCards[i] - state_to_compare.tableCards[i]) for i in range(len(self.tableCards))])
        res += sum([abs(self.playersHand[i] - state_to_compare.playersHand[i]) for i in range(len(self.playersHand))])
        res += sum([abs(self.myHand[i] - state_to_compare.myHand[i]) for i in range(len(self.myHand))])

        return res


class Agent:

    actions = {"play": 0, "discard": 1, "hint": 2}
    N_ACTIONS = len(actions)

    MAX_NO_STATES = 10000
    MAX_TRAINING_EPOCH = 1

    color_value = {"blue": 0, "green": 1, "red": 2, "white": 3, "yellow": 4}
    value_color = {0: "blue", 1: "green", 2: "red", 3: "white", 4: "yellow"}

    agent_game_states = ["Lobby","Game","Learning"]
    values_occurences = [3,2,2,2,1]
    color_occurrences = 10
    num_of_colors = 5

    alpha = 0.2 
    epsylon = 1 # Exploration
    exploit_explore_rate = (1 / MAX_TRAINING_EPOCH) * 2
    gamma = 0.9 # Importance of future actions

    def __init__(self, epsylon=1) -> None:

        self.Q_table = dict() 

        self.reward_table = dict()
        self.state_graph = nx.DiGraph()
        
        self.agent_current_game_state = "Lobby"
                
        #======================
        self.num_players = None
        self.my_cards_info = None
        self.other_players_cards_info = dict()
        self.myturn = False

        self.probable_hand = []

        self.data = None
        self.name = None

        #======================
        self.old_state = State(empty=True) #Generate empty State
        self.new_state = State(empty=True) #Generate empty State
        self.otherPlayerEnded = 0

        self.players_actions = []
        self.total_reward = 0

        self.epsylon = epsylon
        self.gameOver = False

        self.matchCounter = 0
        #======================

    def find_nearest_state(self, state:State, states_table) -> State:
        """Finds a near state to the given state"""
        minim = 10000000
        saved_state = None
        global clustering

        for s in states_table:
            dist = state.distance(s)

            if dist < clustering and dist < minim:
                minim = dist
                saved_state = s
        
        return saved_state


    def compute_reward(self, data, action) -> int:
        """
        This function compute the immediate reward for a given state simulating each possible action
        """
        if "hint" in action:
            if data.usedNoteTokens == 0:
                return -10
            if "bad" in action:
                return -10
            if "good" in action:
                return 0

        elif action == "discard":
            if "bad" in action:
                return -10
            elif self.count_played_cards(data) == 50:
                return self.table_score(data)
            
        elif "play" in action:
            if "bad" in action:
                return -10 
            #if data.usedStormTokens == 3:
                
            elif self.table_score(data) == 25:
                return 100
            else:
                return self.table_score(data)
                    
        return 0


    def count_played_cards(self,data:GameData.ServerGameStateData):
        accum = 0
        for player in data.players:
            accum += len(player.hand)
        accum += len(self.my_cards_info)

        return len(data.discardPile) + accum

    def set_data(self, data:GameData.ServerGameStateData, playerName):
        if not self.num_players or self.num_players != len(data.players): 
            self.data = data
            self.num_players = len(data.players)
            self.name = playerName

            self.myturn = True if data.currentPlayer == self.name else False

            self.my_cards_info = [{"color": None, "value": None, "position":None,"age":0 } for _ in range(5)] #if self.num_players>=4 else 4)]
            for player in self.data.players:
                if player.name != self.name:
                    self.other_players_cards_info[player.name] = [{"color": None, "value": None, "position":None } for _ in range(5)] # if self.num_players>=4 else 4)]


    def update_data(self, data):
        self.data = data

        if data.players_action == "discard" or data.players_action == "play bad":
            # If the player who discard is this player delete the actual info on this card and add a new one
            if data.currentPlayer == self.name:
                self.my_cards_info.pop(data.index)
                if len(data.tableCards)>0:
                    self.my_cards_info.append({"color": None, "value": None, "position":None,"age":0 })

            # Else delete from my knowledge of other cards this card with a new one
            else:
                self.other_players_cards_info[data.currentPlayer].pop(data.index)
                if len(data.tableCards)>0:
                    self.other_players_cards_info[data.currentPlayer].append({"color": None, "value": None, "position":None })



    def update_players_action(self, other_player_action: str):

        if "play" in other_player_action:
            action = 0
        elif "hint" in other_player_action:
            action = 1
        elif "discard" in other_player_action:
            action = 2
        else:
            assert False # Debug

        assert type(action) is int

        self.total_reward += self.compute_reward(self.data, other_player_action)
        self.players_actions.append(action)


    def update_my_cards_knowledge(self, data):
        for position in data.positions:
            self.my_cards_info[position]["position"] = position

            self.my_cards_info[position][data.type] = data.value
            

    def update_other_players_knowledge(self, data):
        for position in data.positions:
            self.other_players_cards_info[data.destination][position]["position"] = position

            self.other_players_cards_info[data.destination][position][data.type] = data.value
            

    def learn(self) -> str:

        assert self.data
        assert len(self.players_actions) <= self.num_players

        # Update the action and reward ==========
        if self.old_state.empty:
            self.reward_table[self.old_state] = dict()
            self.Q_table[self.old_state] = dict()

        self.reward_table[self.old_state][tuple(self.players_actions)] = self.total_reward           

        #========================================

        
        self.new_state = self.evaluate_state(self.data)

        # Discover a state and Update the DS which contains the states
        if self.new_state not in self.state_graph.nodes:
        
            if len(self.Q_table) > self.MAX_NO_STATES:
                self.new_state = self.find_nearest_state(self.new_state, self.Q_table)
            else:
                # Add the new state row in the table
                if self.new_state not in self.Q_table.keys():
                    self.Q_table[self.new_state] = dict()
                # Update the immediate reward table with the new rewars for this state
                self.reward_table[self.new_state] = dict()
                # Add the new edge in the graph of reachable state
                if not self.state_graph.has_edge(self.old_state, self.new_state):
                    self.state_graph.add_edge(self.old_state, self.new_state)

            
        # Update the local Q-function at the previous time (T-1)
        self.update_Q_table_Previous(self.new_state, self.old_state, tuple(self.players_actions))
        new_action = self.pick_an_action(self.new_state)
        
        # In order to discard the useless card i need to increment the counter "age"
        # which keeps track of how many time that card remains in my hand
        self.ageMyCardsBelief()
        self.old_state = self.new_state     

        # Reset the set of actions that bring us to this State
        self.players_actions.clear()
        self.total_reward = 0

        return self.buildReadableAction(new_action)


    def ageMyCardsBelief(self):
        """
            In order to discard the oldest card in the hand i need to increment the age at each 
        """
        for card in self.my_cards_info:
            card["age"] += 1


    def buildReadableAction(self, action):
        assert type(action) is int
        
        #return self.UsefullHintToAnyone()

        if action == 0:
            return self.playCard()
            
        if action == 2:
            return self.UsefullHintToAnyone()
            
        if action == 1:
            return self.discardOldest()
            
        else:
            print("Not valid action available")

    
    def playCard(self):
        """ Play the card with the highest probability"""
        for card in self.probable_hand:
            if self.isPlayable(card["value"], card["color"]):
                return "play "+str(card["position"] )
        
        return "play "+str(randrange(len(self.my_cards_info)))

    def isPlayable(self, value, card_color) -> bool:
        for color_pile, cards in self.data.tableCards.items():
            max_val = len(cards)
            if color_pile == card_color and max_val + 1 == value :
                return True
        return False

    def UsefullHintToAnyone(self):
        """ Give an hint to a next player that maximize the quotient: score_of_the_card/knowledge """
        
        saved_player = None
        saved_value = None
        max_value = 0
        action = None

        for p in self.data.players:
            if p.name == self.name: continue

            for i, card in enumerate(p.hand):
                if self.isPlayable(card.value, card.color):
                    if not self.other_players_cards_info[p.name][i]["color"]:
                        if card.value > max_value: 
                            max_value = card.value
                            action = "color"
                            saved_player = p.name
                            saved_value = card.color

                    elif not self.other_players_cards_info[p.name][i]["value"]:
                        if card.value > max_value: 
                            max_value = card.value
                            action = "value"
                            saved_player = p.name
                            saved_value = card.value
        
        # That mean that:
        # - the all players have all the info about their cards (very unlikely)
        # - the all players does not have playable cards in their hands
        # So I give the hint for the card which have the max value
        if max_value == 0 :
            for p in self.data.players:
                if p.name == self.name: continue

                for i, card in enumerate(p.hand):
                    if not self.other_players_cards_info[p.name][i]["color"]:
                        if card.value > max_value: 
                            max_value = card.value
                            action = "color"
                            saved_player = p.name
                            saved_value = card.color

                    elif not self.other_players_cards_info[p.name][i]["value"]:
                        if card.value > max_value: 
                            max_value = card.value
                            action = "value"
                            saved_player = p.name
                            saved_value = card.value

        #TODO: workaround TO FIX
        if action == None: 
            action="color" 
            saved_player = self.data.players[0].name
            saved_value = "red"
        return "hint "+action+" "+saved_player+" "+str(saved_value)
               

    def discardOldest(self):
        res = max(self.my_cards_info, key=lambda x:x["age"])
        if not res["position"]:
            return "discard "+str(randrange(len(self.my_cards_info)))

        return "discard " + str(res["position"])
            

    def update_Q_table_Previous(self, new_state, old_state, set_of_action):
        
    
        current_q_value = 0 if not set_of_action or not set_of_action in self.Q_table[old_state].keys() else self.Q_table[old_state][set_of_action]  #self.Q_table[old_state][set_of_action] or 0

        R = self.reward_table[old_state][set_of_action]

        Q_value_for_joint_action = max(self.Q_table[new_state].values(), default=0)
        
        LOSS = self.gamma * Q_value_for_joint_action - current_q_value

        
        # Bellman equation for reinforcement learning 
        self.Q_table[old_state][set_of_action] = (1-self.alpha) * current_q_value + self.alpha * (R + LOSS)
        


    def pick_an_action(self, state) -> int:
        """Epsylon greedy exploration"""
        if random()>self.epsylon:
            # Choose exploitation
            res = max(self.Q_table[state], key=self.Q_table[state].get, default=0)
            if res == 0:
                # In this case choose exploration because we have too few experience
                return randrange(len(self.actions))

            return res[0]
            
        else:
            # Choose exploration
            return randrange(len(self.actions))

    
    def getCommand(self, status, wait_operations_finish):

        res = ""

        if self.agent_current_game_state == "Lobby" and status == "Lobby":
            self.agent_current_game_state = "Game"
            res = "ready"

        elif self.agent_current_game_state == "Game" and status == "Game":
            self.agent_current_game_state = "Learning"
            res = "show"

        elif self.agent_current_game_state == "Learning" and status == "Game" and not self.gameOver:
            res = self.learn()

        # if self.gameOver and self.matchCounter < self.MAX_TRAINING_EPOCH:
            
        #     self.resetStates()
        #     self.agent_current_game_state = "Game"
        #     status = "Lobby"
        #     res = "ready"
        #     self.epsylon -= self.exploit_explore_rate
            # wait_operations_finish.wait()
            # wait_operations_finish.clear()

        elif self.gameOver:# and self.matchCounter >= self.MAX_TRAINING_EPOCH:
            res= "exit"

        return res

    
    def resetStates(self):

        self.old_state = State(empty=True)
        self.new_state = State(empty=True)

        directory_name = "H:/Universita/Computationa Intelligence/Exam project/CI_exam_project_hanabi/hanabi/models/"+self.name+"/"
        with open(directory_name + "q_table.pkl","wb") as f:
            pickle.dump(self.Q_table, f)
        with open(directory_name+ "reward_table.pkl","wb") as f:
            pickle.dump(self.reward_table, f)
        with open(directory_name+"state_graph.pkl","wb") as f:
            pickle.dump(self.state_graph, f)

        self.players_actions = []
        self.other_players_cards_info = dict()
        self.my_cards_info = None
        self.total_reward = 0
        self.num_players = None
        self.matchCounter += 1
        self.probable_hand = []
        self.otherPlayerEnded = 0 

        self.gameOver = False

         

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
        """
            Make an estimation of a probable hand based on the info that I have.
            Than I evaluate my hand as the maximum score that i can make if i play all the card.
            The idea behind is that different cards can have the same total score and I want to 
            make similar choice for similar scores. Similar state leads to similar actions
        """
        self.probable_hand = [] 
        my_card_info_copy = deepcopy(self.my_cards_info)

        # Genero il mazzo di carte piu' probabile per poi valutarlo
        for i, my_card in enumerate(self.my_cards_info):
            # Se non so nulla su questa carta non aggiungo la carta al mazzo (punteggio tendenzialmente minore)
            if not my_card["color"]:
                continue
            
            # Se so solo il valore o il colore metto nel mazzo la carta con piu' probabilita' di uscire
            if not my_card["color"] and my_card["value"]:
                color, probability = self.get_color_with_max_probability_given_value(self.data, my_card["value"], my_card_info_copy)
                my_card_info_copy[i]["color"] = color
                self.probable_hand.append({
                    "color": color, 
                    "value": my_card["value"], 
                    "probability": probability,
                    "position":i })

            elif my_card["color"] and not my_card["value"]:
                value, probability = self.get_value_with_max_probability_given_color(self.data, my_card["color"], my_card_info_copy)
                my_card_info_copy[i]["value"] = value
                self.probable_hand.append({
                    "color": my_card["color"], 
                    "value": value, 
                    "probability": probability,
                    "position":i })
            
            else:
                self.probable_hand.append({
                    "color": my_card["color"], 
                    "value": my_card["value"], 
                    "probability": 1,
                    "position": i })

        # If i have no information at all, no evaluation can be performed
        if not self.probable_hand:
            return []


        # Current player-hand evaluation
        s = 0
        # Sorting the probable hand by cards value 
        sorted_hand = sorted([(elem["value"], elem["color"]) for elem in self.probable_hand], key=lambda x: x[0])
        for color, cards in data.tableCards.items():
            
            max_val = len(cards)

            for p_value, p_color in sorted_hand:
                if color != p_color:
                    continue
                if max_val + 1 == p_value:
                    max_val = p_value
            s += max_val
            # An IDEA can be to Multiply the max value for the probability of having this card but the introduction of
            # real number leads to a solution space too big to be evaluated
        # s.append(max_val)  #* saved_prob
        
        return [s]


    def evaluate_other_players_state(self, data:GameData.ServerGameStateData, mode="score", discounted=False):
        """ 
            Two possible modes:
            - card_type: we use as evaluator the state number and the type of card that each player have -> dict of information 
            - score: we use the max score that the player could perform with his hand in that specific time -> list of scores
        """

        if mode=="score":
            state = []
            accum = 0
            discount = 1 / self.num_players

            for i, player in enumerate(data.players):
                if player.name == self.name: continue
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

                    accum += max_val if not discounted else round(max_val * (self.num_players-i+1) * discount)
                    # Il punteggio degli altri diminuisce in base alla distanza nel giro che gli altri hanno da me
                state.append(accum)
                accum = 0

        elif mode=="card_type":
            state = []
            for player in data.players:
                state.append(Counter((card.value, self.color_value[card.color]) for card in player.hand))

        else:
            print("Mode is not valid!\n")
            return None
        
        return state


    def get_numCard_per_color(self, data:GameData.ServerGameStateData, color, my_card_info_copy):
        num_counter = 0
        
        # All the card of that color in the other players hand
        for player in data.players:
            if player.name == self.name: continue
            for card in player.hand:
                if card.color == color:
                    num_counter += 1

        # All the card of that color in the discard pile
        for card in data.discardPile:
            if card.color == color:
                    num_counter += 1
        
        # All the card of that color in my hand
        for card in my_card_info_copy:
            if card["color"] is not None:
                if card["color"] == color:
                    num_counter += 1

        return self.color_occurrences - num_counter # Cards in the deck with color == "color"


    def get_numCard_per_value(self, data:GameData.ServerGameStateData, number, my_card_info_copy):

        num_counter = 0

        for player in data.players:
            if player.name == self.name: continue
            for card in player.hand:
                if card.value == number:
                    num_counter += 1
        
        for card in data.discardPile:
            if card.value == number:
                    num_counter += 1
        
        for card in my_card_info_copy:
            if card["value"] is not None:
                if card["value"] == number:
                    num_counter += 1

        return self.values_occurences[number-1] * 5 - num_counter  # Cards in the deck with value == "value"


    def get_numCard_per_value_and_color(self, data:GameData.ServerGameStateData, number, color, my_card_info_copy):
        num_counter = 0
        
        for player in data.players:
            if player.name == self.name: continue
            for card in player.hand:
                if card.value == number and card.color == color:
                    num_counter += 1
        
        for card in data.discardPile:
            if card.value == number and card.color == color:
                    num_counter += 1
        
        for card in my_card_info_copy:
            if card["value"] is not None and card["color"] is not None:
                if card["value"] == number and card["color"] == color:
                    num_counter += 1
        

        return self.values_occurences[number-1] - num_counter 

        
    def get_value_with_max_probability_given_color(self, data, card_color, my_card_info_copy):
        # Sapendo che e' rosso, probabilita' che sia un 1
        # Numero di 1 rossi nel mazzo / totale di carte rosse nel mazzo
        """
            Compute the conditional probability of being a specific value given the card color.
            Return the value of the card with the highest probability or the first one in the case of equal probability.
        """
        card_prob = []
        for card_value in range(1,6):

            den = self.get_numCard_per_color(data, card_color, my_card_info_copy)
            if den != 0: 
                num = self.get_numCard_per_value_and_color(data, card_value, card_color, my_card_info_copy)
                card_prob.append((card_value, num / den ))
                continue

            card_prob.append((card_value, 0))

        return max(card_prob, key=lambda x:x[1])


    def get_color_with_max_probability_given_value(self, data, card_value, my_card_info_copy):
        # Sapendo che e' un 1, probabilita' che sia rosso
        # Numero di 1 rossi nel mazzo / totale di 1 nel mazzo
        """
            Compute the conditional probability of being a specific color given the card value.
            Return the color of the card with the highest probability or the first one in the case of equal probability.
        """
        card_prob = []
        for card_color in ["red","green","blue","yellow","white"]:
     
            den = self.get_numCard_per_value(data, card_value, my_card_info_copy)
            if den != 0: 
                num = self.get_numCard_per_value_and_color(data, card_value, card_color, my_card_info_copy)
                card_prob.append(tuple(card_color, num / den))
                continue

            card_prob.append((card_color, 0))

        return max(card_prob, key=lambda x:x[1])


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
            s += max([v.value for v in data.tableCards[color]], default=0)
        
        assert s >=0 and s <= 25

        return s