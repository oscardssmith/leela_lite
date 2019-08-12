import numpy as np
from math import sqrt, floor
import lcztools
from lcztools import LeelaBoard
import chess
from collections import OrderedDict
import random
from . import UCTNode

L=10**37

delta = .05

class BAINode():
    def __init__(self, board=None, parent=None, move=None, n=0):
        self.board = board
        self.move = move
        self.parent = parent
        self.children = [] # Dict[move, Node]
        self.UB = 0
        self.LB = 0
        self.n = n
        self.num_BAI_children = 0
    
    def pick_best_optim_child(self):
        best = None
        score = -100.0
        for child in self.children:
            if child.UB > score:
                best = child
                score = child.UB
        if best==None:
            print(self.children)
        return best
    
    def pick_best_pesim_child(self):
        best = None
        score = -100.0
        for child in self.children:
            if child.LB > score:
                best = child
                score = child.LB
        return best 
            
    def BAI_select(self):
        ''' Returns represetnative child of '''
        bt = self.pick_best_pesim_child()
        l1 = bt.get_representative_leaf()
        
        ct = None
        best = -1
        l2 = None
        for child in self.children:
            if child.UB > best:
                leaf = child.get_representative_leaf()
                if leaf != l1:
                    ct = child
                    l2 = leaf
                    best = child.UB
        if ct == bt:
            print('hi')
        ct = self.pick_best_optim_child()
        #print(l1,l2)
        if bt.UB - bt.LB >= ct.UB-ct.LB:
            return l1
        return l2
        
    def get_representative_leaf(self):
        node = self
        while type(node) is BAINode:
            node = node.pick_best_optim_child()
        return node
    
    def get_Is(self, depth):
        return self.n/(self.num_BAI_children+1)/depth
        
    def backup(self):
        self.UB = max(-node.UB for node in self.children)
        self.LB = max(-node.LB for node in self.children)
        self.n += 1
        if self.parent is not None:
            self.parent.backup()
    
    def __gt__(self, other):
        return self.LB > other.LB
    
    def __repr__(self):
        return 'BAINode: ' + str(self.n)

def BAI_find(node, depth):
    if node.num_BAI_children == len(node.children):
        max_Is = -1000
        ret = None
    else:
        max_Is = node.get_Is(depth)
        ret = node
    for child in node.children:
        if type(child) == BAINode and child.num_BAI_children > 0:
            c, Is = BAI_find(child, depth+1)
            if Is > max_Is:
                max_Is = Is
                ret = c
    #print(node.children, node.num_BAI_children)
    return ret, max_Is

def BAI_add(node):
    to_expand, _ = BAI_find(node, 1)
    assert type(to_expand) is BAINode
    for i, child in enumerate(to_expand.children):
        if type(child) != BAINode and child.is_expanded:
            new_child = BAINode(board=child.board, move=child.move, parent=to_expand, n=int(child.number_visits))
            new_child.children = child.children
            node.children[i] = new_child
            del child
            for child in new_child.children:
                child.parent = new_child
            to_expand.num_BAI_children += 1
            return
            
def BAI_DAG_search(board, num_reads, net=None, b=.5):
    assert(net != None)
    
    root = BAINode(board)
    child_priors, value_estimate = net.evaluate(board)
    
    for move, prior in child_priors.items():
        root.children.append(UCTNode(move=move, parent=root))
        
    for t in range(num_reads):
        # print(t)
        if floor((t+1)**b)-floor(t**b) == 1:
            BAI_add(root)
        selected = root.BAI_select()
        leaf = selected.select_leaf(3.0)
        child_priors, value_estimate = net.evaluate(leaf.board)
        leaf.expand(child_priors)
        leaf.backup(value_estimate)
        
        selected.parent.backup()
    choice = root.pick_best_pesim_child()
    return choice.move, choice
