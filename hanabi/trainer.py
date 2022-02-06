import os
from subprocess import Popen
import networkx as nx
import pickle
import matplotlib.pyplot as plt

MAX_TRAINING_EPOCH = 100
PENALTY_INCREMENT_CONDITION = 100
directoryName = "python ./hanabi/"
numPlayer = 2
epsylon = 1

clean_all_training = False

penality = 0
if os.path.exists("game.log"):
    os.remove("game.log")


for i in range(MAX_TRAINING_EPOCH):
    
    if i%PENALTY_INCREMENT_CONDITION == 0 and i != 0:
        penality += PENALTY_INCREMENT_CONDITION/MAX_TRAINING_EPOCH

    playersProcess = []
    

    server = Popen(directoryName + "server.py "+str(numPlayer))    
    
    for i in range(numPlayer):
        playersProcess.append(Popen(directoryName+"myClient.py Agent_"+str(i+1)+" "+str(epsylon - penality)))

    for p in playersProcess:
        p.wait()

    server.kill()




# grp = None

# directory_name = "H:/Universita/Computationa Intelligence/Exam project/CI_exam_project_hanabi/hanabi/models/Agent_1/"

# with open(directory_name + "state_graph.pkl", "rb") as f:
#     grp = pickle.load( f)

# print(nx.is_directed_acyclic_graph(grp))
# print(f"The graph has discovered {len(grp.nodes)} states")

# nx.draw(grp, nodelist=dict(nx.degree(grp)).keys(), node_size=2)
# plt.show()