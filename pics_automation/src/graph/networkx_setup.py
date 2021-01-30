import networkx as nx
from src.graph.node_types import StartNode, EndNode, ClickNode, FunctionNode, ImageSearchAndClickNode, ImageSearchNode


class PicsaInitGraph(nx.DiGraph):
    def __init__(self, nodes, ensure_no_cycles=False):
        super(PicsaInitGraph, self).__init__()
        self.add_nodes_from(nodes)
        self.start_node = None
        self.end_node = None
        self.ensure_no_cycles = ensure_no_cycles

    def set_dependant(self, u, v):

        if type(u) == StartNode:
            self.start_node = u
        elif type(u) == EndNode:
            self.end_node = u

        if u not in self.nodes or v not in self.nodes:
            raise ValueError("Nodes must be in the Graph before you add an edge between them")
        if type(u) == EndNode:
            raise ValueError("An EndNode must not have dependants")
        if type(v) == StartNode:
            raise ValueError("A StartNode must not have dependencies")

        self.add_edge(u, v)
        try:
            if list(map(type, self.nodes)).count(EndNode) > 1:
                raise ValueError("A pics automation graph must not include more than one EndNode")
            if list(map(type, self.nodes)).count(StartNode) > 1:
                raise ValueError("A pics automation graph must not include more than one StartNode")
            if self.ensure_no_cycles and not nx.is_directed_acyclic_graph(self):
                raise ValueError("This pics automation graph must not contain cycles")
            if list(map(lambda node: node.no_decidable_criteria, list(self.neighbors(u)))).count(True) > 1:
                raise ValueError("A node cannot be the dependency of more than one no_decidable_criteria node")
        except ValueError as e:
            raise e

    def start(self):
        pass


# node_4 = ImageSearchAndClickNode("fourth", True, "restart_steam.png", 0.7, 2)
# node_5 = ImageSearchNode("fifth", True, "advertising.png", 0.8, 0)
#
# advertising_correction = (0, 0)
# node_6 = ClickNode("sixth", True, node_5)
#
# node_7 = ImageSearchNode("seventh", True, "power_button.png", 0.7, 0)
# node_8 = ImageSearchAndClickNode("eighth", True, "was_in_lobby.png", 0.7, 2)
# node_9 = ImageSearchAndClickNode("ninth", True, "accept_invite.png", 0.7, 2)
# node_10 = FunctionNode("tenth", True, 0, lambda x: "To be implemented")
# node_11 = ClickNode("eleventh", True, node_10)
# node_12 = FunctionNode("twelfth", True, 0, lambda x: "To be implemented")
#
#
# DOTA2_AUTOMATION_NODES = [
#     node_1, node_2, node_3, node_4, node_5, node_6, node_7, node_8,
#     node_9, node_10, node_11, node_12
# ]


if __name__ == '__main__':
    node_1 = StartNode("first", True, 0, lambda x: "To be implemented")
    node_2 = ImageSearchAndClickNode("second", True, "checkbox.png", 0.8, 2)
    node_3 = ImageSearchNode("third", True, "logotype.png", 0.6, 0)
    AUTOMATION_NODES = [node_1, node_2, node_3]

    G = PicsaInitGraph(AUTOMATION_NODES)

    G.set_dependant(node_1, node_2)
    G.set_dependant(node_2, node_2)

#
# G.set_dependant(node_1, node_2)
# G.set_dependant(node_1, node_3)
# G.set_dependant(node_2, node_3)
# G.set_dependant(node_2, node_4)
# G.set_dependant(node_4, node_12)
# G.set_dependant(node_3, node_5)
# G.set_dependant(node_5, node_6)
# G.set_dependant(node_6, node_7)
# G.set_dependant(node_3, node_7)
# G.set_dependant(node_7, node_8)
# G.set_dependant(node_7, node_9)
# G.set_dependant(node_8, node_9)
# G.set_dependant(node_9, node_10)
# G.set_dependant(node_10, node_11)
# G.set_dependant(node_11, node_12)





