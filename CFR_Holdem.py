import io
import sys
import string
import math
import random

def test():
    print('py succ')
test()

# CFR Python 有限下注德扑扑克 20BB 5张牌

PASS = 0
BET = 1
NUM_ACTIONS = 2
r = random.random()
nodeMap = {}

infoSet = ''
regretSum = [NUM_ACTIONS]
strategy = [NUM_ACTIONS]
strategySum = [NUM_ACTIONS]