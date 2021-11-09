import io
import sys
import string
import math
import random
import array
# def test():
#     print('py succ')
# test()

# PASS = 0
# BET = 1
# NUM_ACTIONS = 2
# r = random.random()
# nodeMap = {}

# infoSet = ''
# regretSum = [NUM_ACTIONS]
# strategy = [NUM_ACTIONS]
# strategySum = [NUM_ACTIONS]

# CFR Lair Die，2个骰子，6个面，Python
# Action:Doubt and Accept
# Value: LastClaim RollRank(1) CurrentClaim

def roll():
    return random.randint(1,6)

def claim(lastClaim=0):
    return random.randint(lastClaim+1,6)

class Node:
    regretSum = []
    strategy = [] 
    strategySum = []

    u = 0.0
    pPlayer = 0.0 
    pOpponent = 0.0
    
    def __init__(self,numActions=1) -> None:
        self.regretSum = [numActions]
        self.strategy = [numActions]
        self.strategySum = [numActions]
        pass

    def getStrategy(self):
        normalizingSum = 0.0
        for a in range(0, len(self.strategy), 1):
            self.strategy[a] = max(self.regretSum[a], 0)
            normalizingSum += self.strategy[a]
        
        for a in range(0, len(self.strategy), 1):
            if normalizingSum > 0:
                self.strategy[a] /= normalizingSum
            else:
                self.strategy[a] = 1.0/len(self.strategy)
        
        for a in range(0, len(self.strategy), 1):
            self.strategySum[a] += self.pPlayer * self.strategy[a]
        return self.strategy

    def getAverageStrategy(self):
        normalizingSum = 0.0
        for a in range(0, len(self.strategy), 1):
            normalizingSum += self.strategySum[a]
        for a in range(0, len(self.strategy), 1):
            if (normalizingSum > 0):
                self.strategySum[a] /= normalizingSum
            else:
                self.strategySum[a] = 1.0 / len(self.strategySum)
        return self.strategySum

class LiarDieTrainer:
    Doubt = 0
    Accept = 1
    sides = 0
    randomNum = random.random()
    responseNodes = [[]]
    claimNodes = [[]]
    
    def LiarDieTrainer(self, sides):
        self.sides = sides
        # self.responseNodes = Node[sides][sides + 1]
        for myClaim in range(0,sides,1):
            for oppClaim in range(myClaim + 1, sides,1):
                if oppClaim == 0 or oppClaim == sides:
                    self.responseNodes[myClaim][oppClaim] = Node(1)
                else:
                    self.responseNodes[myClaim][oppClaim] = Node(2)
        # self.claimNodes = Node[sides][sides + 1]
        for oppClaim in range(0, sides - 1, 1):
            for roll in range(1, sides, 1):
                self.claimNodes[oppClaim][roll] = Node(sides - oppClaim)
    
    
# Train with FSICFRi≡
    def train(self, iterations):
        regret =  [self.sides]
        rollAfterAcceptingClaim =  [self.sides]
        for iter in range(0,iterations,1):
            # Initialize rolls and starting probabilitiesi
            for  i in range(0,len(rollAfterAcceptingClaim),1):
                rollAfterAcceptingClaim[i] = random.nextInt(self.sides) + 1
                self.claimNodes[0][rollAfterAcceptingClaim[0]].pPlayer = 1
                self.claimNodes[0][rollAfterAcceptingClaim[0]].pOpponent = 1
            # Accumulate realization weights forwardi
            for oppClaim in range(0, self.sides, 1):
                # Visit response nodes forwardi
                if (oppClaim > 0):
                    for myClaim in range(0, oppClaim-1, 1): 
                        node = self.responseNodes[myClaim][oppClaim] 
                        actionProb = node.getStrategy()
                        if (oppClaim < self.sides) :
                            nextNode = self.claimNodes[oppClaim][rollAfterAcceptingClaim[oppClaim]]
                            nextNode.pPlayer += actionProb[1] * node.pPlayer
                            nextNode.pOpponent += node.pOpponent
            
                # Visit claim nodes forwardi
                if (oppClaim < self.sides):
                    node = self.claimNodes[oppClaim][rollAfterAcceptingClaim[oppClaim]]
                    actionProb = node.getStrategy()
                    for myClaim in range(oppClaim + 1, self.sides, 1):
                        nextClaimProb = actionProb[myClaim - oppClaim - 1]
                        if (nextClaimProb > 0) :
                            nextNode = self.responseNodes[oppClaim][myClaim]
                            nextNode.pPlayer += node.pOpponent
                            nextNode.pOpponent += nextClaimProb * node.pPlayer
            
            # Backpropagate utilities, adjusting regrets and strategiesi
            for oppClaim in reversed( range(0, self.sides, 1)):
                # Visit claim nodes backwardi
                if (oppClaim < self.sides):
                    node = self.claimNodes[oppClaim][rollAfterAcceptingClaim[oppClaim]]
                    actionProb = node.strategy
                    node.u = 0.0
                    for myClaim in range(oppClaim + 1, self.sides, 1):
                        actionIndex = myClaim - oppClaim - 1
                        nextNode = self.responseNodes[oppClaim][myClaim]
                        childUtil = - nextNode.u
                        regret[actionIndex] = childUtil
                        node.u += actionProb[actionIndex] * childUtil
                    for a in range(0,len(actionProb),1): 
                        regret[a] -= node.u
                        node.regretSum[a] += node.pOpponent * regret[a]
                    node.pPlayer = node.pOpponent = 0
                    
                # Visit response nodes backwardi
                if (oppClaim > 0):
                    for myClaim in range(0, oppClaim,1):
                        node = self.responseNodes[myClaim][oppClaim]
                        actionProb = node.strategy
                        node.u = 0.0
                        if (oppClaim > rollAfterAcceptingClaim[myClaim]):
                            doubtUtil = 1 
                        else: 
                            doubtUtil = -1
                        regret[DOUBT] = doubtUtil
                        node.u += actionProb[DOUBT] * doubtUtil
                        if (oppClaim < sides):
                            nextNode = self.claimNodes[oppClaim][rollAfterAcceptingClaim[oppClaim]]
                            regret[ACCEPT] = nextNode.u
                            node.u += actionProb[ACCEPT] * nextNode.u
                        for a in range(0, len(actionProb), 1):
                            regret[a] -= node.u
                            node.regretSum[a] += node.pOpponent * regret[a]
                        node.pPlayer = node.pOpponent = 0
                    
            # Reset strategy sums after half of trainingi
            if (iter == iterations / 2):
                for nodes in self.responseNodes:
                    for node in nodes:
                        if (node != None):
                            for a in range(0, len(node.strategySum), 1):
                                node.strategySum[a] = 0
                for nodes in self.claimNodes:
                    for node in nodes:
                        if (node != None):
                            for a in range(0, len(node.strategySum), 1):
                                node.strategySum[a] = 0
            
        # Print resulting strategyi
        for initialRoll in range(1, self.sides, 1):
            print(f"Initial claim policy with roll {initialRoll}: ")
            for prob in self.claimNodes[0][initialRoll].getAverageStrategy():
                print("%.2f ", prob)
            print("--------------------------")
        
        print("\nOld Claim\tNew Claim\tAction Probabilities")
        for myClaim in range(0, self.sides, 1):
            for oppClaim in range(myClaim + 1, self.sides, 1):
                print("\t%d\t%d\t%s\n", myClaim, oppClaim,Arrays.toString(self.responseNodes[myClaim][oppClaim].getAverageStrategy()))
                
        print("\nOld Claim\tRoll\tAction Probabilities")
        for oppClaim in range(0, self.sides, 1):
            for roll in range(1, self.sides, 1):
                print(f"{oppClaim}\t{roll}\t{Arrays.toString(self.claimNodes[oppClaim][roll].getAverageStrategy())}\n")
    
    def mian(self):
        trainer = LiarDieTrainer(6)
        trainer.train(1000000)
    

