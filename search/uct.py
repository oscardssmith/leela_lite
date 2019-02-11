import numpy as np
import math
import lcztools
from lcztools import LeelaBoard
import chess
from collections import OrderedDict
import random

class UCTNode():
    def __init__(self, board=None, parent=None, move=None, prior=0):
        self.board = board
        self.move = move
        self.is_expanded = False
        self.parent = parent  # Optional[UCTNode]
        self.children = [] # Dict[move, UCTNode]
        self.prior = prior  # float
        if parent == None:
            self.total_value = 0.  # float
        else:
            self.total_value = -1.0
        self.number_visits = 0  # int
        
    def Q(self):  # returns float
        if not self.number_visits:
            return 0 # FPU reduction, parent value like lc0???
        else:
            return self.total_value / self.number_visits

    def U(self, pvsqrt):  # returns float
        return pvsqrt * self.prior / (1 + self.number_visits)

    def best_child(self, C):
        pvsqrt = self.number_visits ** 0.5
        def eval_node(node):
            return node.Q() + C*node.U(pvsqrt)
        return max(self.children, key=eval_node)

    def select_leaf(self, C):
        current = self
        while current.is_expanded and current.children:
            current = current.best_child(C)
        if not current.board:
            current.board = current.parent.board.copy()
            current.board.push_uci(current.move)
        return current

    def expand(self, child_priors):
        self.is_expanded = True
        for move, prior in child_priors.items():
            self.add_child(move, prior)

    def add_child(self, move, prior):
        self.children.append(UCTNode(parent=self, move=move, prior=prior))
    
    def backup(self, value_estimate: float):
        current = self
        while current.parent is not None:    
            # Child nodes are multiplied by -1 because we want max(-opponent eval)
            value_estimate *= -1        
            current.number_visits += 1
            current.total_value += value_estimate
            current = current.parent
        current.number_visits += 1

def UCT_search(board, num_reads, net=None, C=1.0):
    assert(net != None)
    root = UCTNode(board)
    for _ in range(num_reads):
        leaf = root.select_leaf(C)
        child_priors, value_estimate = net.evaluate(leaf.board)
        leaf.expand(child_priors)
        leaf.backup(value_estimate)

    #for m, node in sorted(root.children.items(),
    #                      key=lambda item: (item[1].number_visits, item[1].Q())):
    #    node.dump(m, C)
    best_node =  max(root.children,
               key=lambda node: (node.number_visits, node.Q()))
    return best_node.move, best_node
