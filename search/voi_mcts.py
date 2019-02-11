"""
    value of information search

    MCTS Based on Simple Regret
    David Tolpin, Solomon Eyal Shimony
    https://pdfs.semanticscholar.org/2a81/bfc05ddec612fd9bf0aafad0a86ad13b0361.pdf
"""
import math
import heapq
from collections import OrderedDict


class VOINode:
    def __init__(self, board=None, parent=None, move=None, prior=0):
        self.board = board
        self.move = move
        self.is_expanded = False
        self.parent = parent  # Optional[UCTNode]
        self.children = OrderedDict()  # Dict[move, UCTNode]
        self.prior = prior  # float
        self.total_value = 0  # float
        self.number_visits = 0  # int

    def Q(self):  # returns float
        return self.total_value / (1 + self.number_visits)

    def best_child(self):
        """
        Take care here: bear in mind that the rewards in the paper are in the region [0, 1]
        :return: best child
        """
        if len(self.children) < 2:
            return (list(self.children.values()))[0]

        alpha, beta = heapq.nlargest(2,
                                     self.children.values(),
                                     key=lambda node: node.Q()
                                     )
        result = None
        voi_max = -1
        for n in self.children.values():
            voi = n.prior / (1. + n.number_visits)
            if n == alpha:
                voi *= (1 + beta.Q()) * math.exp(-0.5 * alpha.number_visits * (alpha.Q() - beta.Q()) ** 2)
            else:
                voi *= (1 - alpha.Q()) * math.exp(-0.5 * n.number_visits * (alpha.Q() - n.Q()) ** 2)
            if voi > voi_max:
                voi_max = voi
                result = n

        return result

    def select_leaf(self):
        current = self
        while current.is_expanded and current.children:
            current = current.best_child()
        if not current.board:
            current.board = current.parent.board.copy()
            current.board.push_uci(current.move)
        return current

    def expand(self, child_priors):
        self.is_expanded = True
        for move, prior in child_priors.items():
            self.add_child(move, prior)

    def add_child(self, move, prior):
        self.children[move] = VOINode(parent=self, move=move, prior=prior)

    def backup(self, value_estimate: float):
        current = self
        # Child nodes are multiplied by -1 because we want max(-opponent eval)
        turnfactor = -1
        while current.parent is not None:
            current.number_visits += 1
            current.total_value += (value_estimate *
                                    turnfactor)
            current = current.parent
            turnfactor *= -1
        current.number_visits += 1

    def dump(self, move):
        print("---")
        print("move: ", move)
        print("total value: ", self.total_value)
        print("visits: ", self.number_visits)
        print("prior: ", self.prior)
        print("Q: ", self.Q())
        print("---")


def VOI_search(board, num_reads, net=None):
    assert(net is not None)
    root = VOINode(board)
    for _ in range(num_reads):
        leaf = root.select_leaf()
        child_priors, value_estimate = net.evaluate(leaf.board)
        leaf.expand(child_priors)
        leaf.backup(value_estimate)

    pv = sorted(root.children.items(), key=lambda item: (item[1].Q(), item[1].number_visits), reverse=True)

    print('pv:', [(n[0], n[1].Q(), n[1].number_visits) for n in pv])
    return max(root.children.items(),
               key=lambda item: (item[1].Q(), item[1].number_visits))
