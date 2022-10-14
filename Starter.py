import os ; 

n_player = ["agent", "luca"]

os.remove("./game.log")

os.system('start cmd /K python server.py')
for player_name in n_player:
    if player_name == "agent":
        os.system(f'start cmd /K python agent_client.py 127.0.0.1 1024 {player_name}')
    else:
        os.system(f'start cmd /K python client.py 127.0.0.1 1024 {player_name}')