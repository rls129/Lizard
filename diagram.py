import sys
import networkx as nx
from copy import deepcopy
from lark import *
from base import *
import matplotlib.pyplot as plt

gate_count = 0

from PySide6.QtCore import QPointF, Qt, QLine
from PySide6.QtGui import QBrush, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


WIDTH = 600
HEIGHT = 400
scale = HEIGHT/2


app = QApplication(sys.argv)
scene = QGraphicsScene(0, 0, WIDTH, HEIGHT)
scene.setBackgroundBrush(Qt.gray)

def draw(a):
    g = nx.DiGraph()

    def get_graph(node, level):
        global gate_count
        if isinstance(node, Token):
            assert(node.type == "IDENTIFIER")
            name = node.value
            if not g.has_node(name):       
                g.add_node(name, type = "signal", level=level)
            return name
        
        if isinstance(node, Tree):
            if node.data.value == "value":
                return get_graph(node.children[0], level-1)

            if node.data.value == "literal":
                literal = node.children[0]
                if not g.has_node(literal):       
                    g.add_node(literal, type = "bit", level=level)
                return literal.value

            if node.data.value == "binary_expression":
                left = get_graph(node.children[0], level-1)
                right = get_graph(node.children[2], level-1)
                
                gate_name = node.children[1].value
                gate_node = gate_name+str(gate_count)
                g.add_node(gate_node, type = "gate", image = "./res/images/"+gate_name+".svg", level=level)
                gate_count+=1
                g.add_edge(left, gate_node)
                g.add_edge(right, gate_node)
                return gate_node


    for process in a.processes:
        sts = process.statements
        if isinstance(sts, Statements):
            sts = sts.statements
        if len(sts) == 1 and sts[0].data.value == "shorthandprocess":
            shp = process.statements[0]
            rvalue = get_graph(shp.children[1], 0)
            lvalue = get_graph(shp.children[0], 1)
            g.add_edge(rvalue, lvalue)
    
    pos = nx.multipartite_layout(g, scale = scale, center = (WIDTH/2, HEIGHT/2), subset_key = "level")
    fixed_positions = {}
    edges = list(g.edges())
    added_nodes = []

    for n in g.nodes:
        node = g.nodes[n]
        x, y = pos[n][0], pos[n][1]
        if node["type"] == "gate":
            pixmap = QPixmap(node["image"])
            width = pixmap.width()
            height = pixmap.height()
            
            added_nodes.extend([n+str(i) for i in range(3)])

            fixed_positions[n+'0'] = (x+width/2 - 5, y)
            fixed_positions[n+'1'] = (x-width/2 + 5, y-height/4+2)
            fixed_positions[n+'2'] = (x-width/2 + 5, y+height/4-2)
            fixed_positions[n] = (x, y)
            pos.update(fixed_positions)

            predecessors = list(filter(lambda x: x[1] == n, edges))
            predecessors.sort(key=lambda x:pos[x[0]][1])
            successors = list(filter(lambda x: x[0] == n, edges))

            for i, x in enumerate(predecessors):
                edges.remove(x)
                edges.append((x[0], n+str(i+1)))
            
            for x in successors:
                edges.remove(x)
                edges.append((n+'0', x[1]))

    g.add_nodes_from(added_nodes, type = 'gate_pin')
    g.clear_edges()
    g.add_edges_from(edges)
    # print(edges)

    fixed_nodes = [n for n in fixed_positions]
    pos.update(fixed_positions)
    # pos = nx.spring_layout(g, pos = pos, fixed = fixed_nodes, k = 0.1)

    for n in g.nodes:
        node = g.nodes[n]
        x, y = pos[n][0], pos[n][1]
        if node["type"] == "signal" or node["type"] == "bit":
            circleitem = scene.addEllipse(x-2, y-2, 4, 4)
            textitem = scene.addText(n)
            x, y = x-15, y-10
            textitem.setPos(x, y)
        elif node["type"] == "gate":
            pixmap = QPixmap(node["image"])
            width = pixmap.width()
            height = pixmap.height()
            pixmapitem = scene.addPixmap(pixmap)
            pixmapitem.setPos(x-width/2, y-height/2)
    
    for a, b in g.edges:
        # print(a, b)
        lineitem = scene.addLine(*pos[a], *pos[b])

    
    view = QGraphicsView(scene)
    view.setRenderHint(QPainter.Antialiasing)
    view.show()

    app.exec_()
