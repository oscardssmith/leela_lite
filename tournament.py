#!/usr/bin/python3

from collections import Counter
from itertools import permutations, cycle
import sys
import time

import chess
import chess.pgn
from lcztools import load_network, LeelaBoard
import search

GAMES = 4
NODES = 800
engines = [search.UCT_search, search.VOI_search]
weights = 'weights_9149.txt.gz'



net = load_network(backend='pytorch_cuda', filename=weights, policy_softmax_temp=2.2)
# net = load_network(backend='pytorch_cuda', filename=weights, policy_softmax_temp=1.0)
nn = search.NeuralNet(net=net)

scores = Counter()
for a, b in permutations(engines, 2):
    for _ in range(GAMES):
        board = LeelaBoard()
        for player in cycle((a,b)):
            print(board)
            best, node = player(board, NODES, net=nn, C=3.4)
            board.push_uci(best)
            print(player, " best: ", best, node.Q())
            print()
            
            if board.pc_board.is_game_over() or board.is_draw():
                result = board.pc_board.result(claim_draw=True)
                print(f"Game over... result is {result}")
                print(board)
                print(chess.pgn.Game.from_board(board.pc_board))
                    
                if result == '0-1':
                    scores[a] += 1
                elif result == "1/2-1/2":
                    scores[a] += .5
                    scores[b] += .5
                else:
                    scores[b] += 1
                
                print(scores)
                break

