import os
from subprocess import Popen


MAX_TRAINING_EPOCH = 300
directoryName = "python ./hanabi/"
numPlayer = 2
epsylon = 0.8

penality = 0
if os.path.exists("game.log"):
    os.remove("game.log")

for i in range(MAX_TRAINING_EPOCH):
    
    if i%100 == 0:
        penality += 0.2

    playersProcess = []
    

    server = Popen(directoryName + "server.py "+str(numPlayer))    
    
    for i in range(numPlayer):
        playersProcess.append(Popen(directoryName+"myClient.py Agent_"+str(i+1)+" "+str(epsylon - penality)))

    for p in playersProcess:
        p.wait()

    server.kill()