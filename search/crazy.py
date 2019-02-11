
import numpy as np
import math
from random import choices
import lcztools
from lcztools import LeelaBoard
import chess
from collections import OrderedDict


class CRAZYNode():
    def __init__(self, board=None, parent=None, move=None, prior=0):
        self.board = board
        self.move = move
        self.is_expanded = False
        self.parent = parent  # Optional[UCTNode]
        self.children = []   # Dict[move, UCTNode]
        self.prior = prior
        if parent is None:
            self.val = 0.  # float
        else:
            self.val = -parent.val  # float
        self.Q2 = 0. #float
        self.number_visits = 0  # int
    
    def Q(self):
        return self.val
        
    def var(self):
        return self.Q2 / self.number_visits
    
    def __repr__(self):
        return f'CRAZYNode: q={self.val} n={self.number_visits}'
        
    def __lt__(self, other):
        return (self.val, self.number_visits) <= (other.val, other.number_visits)
        
    def get_best_weight(self, best, second, remaining_visits):
        ni = best.number_visits
        if ni == 0:
            return 1-best.prior
        return 2*remaining_visits*(best.Q)/ni*math.e**(-1.37*ni*(good_q - bad.val)**2)
        
    def get_weight(self, good_val, bad, remaining_visits):
        ni = bad.number_visits
        if ni == 0:
            return bad.prior
        return 2*remaining_visits*(1-good_val)/ni*math.e**(-1.37*ni*(good_val - bad.val)**2)
        
    def select_child(self, remaining_visits):
        #return max(self.children.values(),
        #           key=lambda node: node.Q() + C*node.U())
        children = self.children
        children.sort()
        best_q = children[-1].val
        result = children[-1]
        result_voi = self.get_weight(children[-2].val, children[-1], remaining_visits)
        for child in children[:-1]:
            child_voi = self.get_weight(best_q, child, remaining_visits)
            
            if child_voi > result_voi:
                result, result_voi = child, child_voi
        #print(result)
        return result

    def select_leaf(self, remaining_visits):
        current = self
        while current.is_expanded and current.children:
            current = current.select_child(remaining_visits)
        
        if not current.board:
            current.board = current.parent.board.copy()
            current.board.push_uci(current.move)
        return current
        
    def expand(self, child_priors):
        self.is_expanded = True
        for move, prior in child_priors.items():
            self.add_child(move, prior)

    def add_child(self, move, prior):
        self.children.append(CRAZYNode(parent=self, move=move, prior=prior))

    def build_child(self, move):
        board = self.board.copy()
        board.push_uci(move)
        return board
    
    def backup(self, reward: float):
        current = self
        # Child nodes are multiplied by -1 because we want max(-opponent eval)
        while current.parent is not None:
            reward *= -1
            current.number_visits += 1
            delta = reward - current.val
            current.val += delta / current.number_visits
            delta2 = reward - current.val
            current.Q2 += delta * delta2
            current = current.parent
            
def CRAZY_search(board, num_reads, net=None, C=1.0):
    assert(net != None)
    root = CRAZYNode(board)
    for i in range(num_reads):
        leaf = root.select_leaf(num_reads-i)
        child_priors, reward = net.evaluate(leaf.board)
        leaf.expand(child_priors)
        leaf.backup(float(reward))
        
    #assert -1<=root.Q()<=1, [c.value for c in root.children.values()]
    #assert 0<=root.U()
    total = 0
    #print(total/root.number_visits)
    #print(root.Q())
    best_node =  max(root.children)
    print(best_node)
    return best_node.move, best_node
