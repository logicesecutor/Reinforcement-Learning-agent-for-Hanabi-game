from agent import Agent

class SuperAgent:

    def __init__(self, target_players) -> None:
        self.agents = dict()
        self.target_players = target_players

    def append_agent(self):
        self.agents["agent_"+len(self.agents)] = Agent()

    
    def update_agent(self, action):

        for agent in self.agents:

            agent.update_players_action(action)
