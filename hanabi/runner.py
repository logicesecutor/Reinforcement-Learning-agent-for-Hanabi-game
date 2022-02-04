import os
from subprocess import Popen


MAX_TRAINING_EPOCH = 1
directoryName = "python ./hanabi/"
numPlayer = 5
epsylon = 1

if os.path.exists("game.log"):
    os.remove("game.log")

for i in range(MAX_TRAINING_EPOCH):
    
    playersProcess = []
    

    server = Popen(directoryName + "server.py "+str(numPlayer))    
    
    for i in range(numPlayer):
        playersProcess.append(Popen(directoryName+"myClient.py Agent_"+str(i+1)+" "+str(epsylon)))

    for p in playersProcess:
        p.wait()

    server.kill()