import os ; 

n_player = ["agent", "luca"]

if os.path.isfile("./game.log"):
    os.remove("./game.log")

os.system('start cmd /K python server.py')
for player_name in n_player:
    if "agent" in player_name:
        os.system(f'start cmd /K python agent_client.py 127.0.0.1 1024 {player_name}')
    else:
        os.system(f'start cmd /K python client.py 127.0.0.1 1024 {player_name}')