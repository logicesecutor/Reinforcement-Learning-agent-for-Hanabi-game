import os ; 

n_player = ["mario", "luca"]

os.system('start cmd /K python server.py')

for player_name in n_player:
    os.system(f'start cmd /K python client.py 127.0.0.1 1024 {player_name}')