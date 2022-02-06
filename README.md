# CI_exam_project_hanabi
The initial idea was to build a collaborative collaborative Multi-agent Reinforcement Q-learning framework for the Hanabi game.
This game can be modeled as Partially Observable Markov Decision Problem(PO-MDP). So I want to build a model capable of learning in a collaborative way the best joint action in order to maximize the Game score.

Then, due to my inexperience, I shrink down the problem into an easier version. 

## The Basic IDEA

Each Agent observe his environment and keep track of: 
- His actions;
- Other players action;
- The state of the table his card and other players cards.

An Agent, in order to pass from a state A to a state B, needs to know the list of all action that all player makes because his transition from state A to B does not depend on the single action of the player who does it.
Each time a player make an action each agent observe that action and assign a reward. The sum of all reward of all actions gives a total reward that will be putted in the reward Table.

Then we have to update the Q-table in order learn what future action will be the best from the current state.
In order to do that, I use the bellman equation for Q-learning but here I encouter a problem.

In order to perform the update I need the best Q-value from the next state but, at time T I don't have access to the next state because I don't know what it could be. I need to discover it first.
The next idea was to perform the update at posteriori. To do that I keep track of the past State and when I will be in the next state I perform the update. So the Formula became:

![Bellman Equation](./hanabi/images/bellman_equation.jpg)

## The Big Space of States
The difficulty of the game is to model his big space of game states.
An idea was to evaluate the states in a way that all similar state can have similar signature. So when I had exlpored enough the state space I can compute the distance between my state and the already known states and sobstitute the last founded state with an already discovered one.

To solve this problem the state evaluation is divided in three parts:
- We have 3 number for the table part:
  - number of blue token;
  - number of red token;
  - score of the table at time of evaluation;
- One number for each players hand in the game:
  - Each player is evaluated not using the cards that it have in his hand at evaluation time but the score that it can perform if play all his card
- One number to evaluate my hand:
  - Is evaluated based on a statistical version of my hand and then a score is computed in the same way of the other players


#Conclusion
My conclusion is that it doesn't work at all. I have a bug that ends the training session right in the middle and because of I cannot perform statistics on the results. I am not able to remove it.

I am not happy with that because I spent a lot of time and effort on this project.
