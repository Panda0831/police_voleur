# game/graph.py

START_NODE = "N1"


NODES = {
    # N1 : centre
    "N1": (0.00, 0.00),

    # Cercle central : sens horaire
    "N2": (0.00, 0.50),
    "N3": (0.50, 0.00),
    "N4": (0.00,-0.50),
    "N5": (-0.50,0.00),

    # Intersections des demi-arcs : sens horaire
    "N6": (0.00, 1.45),
    "N7": (2.35, 0.00),
    "N8": (0.00,-1.45),
    "N9": (-2.35,0.00),

    # 4 extrémités oranges des axes : haut, droite, bas, gauche
    "N10": (0.00, 1.95),
    "N11": (3.25, 0.00),
    "N12": (0.00,-1.95),
    "N13": (-3.25,0.00),

    # 8 points bleus sur l'ovale extérieur : sens horaire
    "N14": (-0.55, 1.82),
    "N15": ( 0.55, 1.82),
    "N16": ( 3.00, 0.38),
    "N17": ( 3.00,-0.38),
    "N18": ( 0.55,-1.82),
    "N19": (-0.55,-1.82),
    "N20": (-3.00,-0.38),
    "N21": (-3.00, 0.38),
}


def get_node_position(node_id):
    return NODES.get(node_id)


def validate_nodes():
    assert len(NODES) == 21

    for node_id, coordinates in NODES.items():
        assert len(coordinates) == 2
        assert -3.35 <= coordinates[0] <= 3.35
        assert -2.25 <= coordinates[1] <= 2.25

    print("Représentation valide !")
    print(f"Nombre de sommets : {len(NODES)}")
EDGES = [
    # Cercle central : N2 -> N3 -> N4 -> N5 -> N2
    ("N2", "N3"),
    ("N3", "N4"),
    ("N4", "N5"),
    ("N5", "N2"),

    # Axe vertical : N10 - N6 - N2 - N1 - N4 - N8 - N12
    ("N10", "N6"),
    ("N6", "N2"),
    ("N2", "N1"),
    ("N1", "N4"),
    ("N4", "N8"),
    ("N8", "N12"),

    # Axe horizontal : N13 - N9 - N5 - N1 - N3 - N7 - N11
    ("N13", "N9"),
    ("N9", "N5"),
    ("N5", "N1"),
    ("N1", "N3"),
    ("N3", "N7"),
    ("N7", "N11"),

    # Ovale extérieur (passe par les 4 pointes oranges)
    ("N14", "N10"),
    ("N10", "N15"),
    ("N15", "N16"),
    ("N16", "N11"),
    ("N11", "N17"),
    ("N17", "N18"),
    ("N18", "N12"),
    ("N12", "N19"),
    ("N19", "N20"),
    ("N20", "N13"),
    ("N13", "N21"),
    ("N21", "N14"),

    # Arcs intérieurs (passent par N6, N7, N8 et N9)
    ("N14", "N6"),
    ("N6", "N15"),
    ("N16", "N7"),
    ("N7", "N17"),
    ("N18", "N8"),
    ("N8", "N19"),
    ("N20", "N9"),
    ("N9", "N21"),
]


def build_adjacency():
    """Construit le graphe non orienté à partir de la liste des arêtes."""
    adjacency = {node_id: set() for node_id in NODES}

    for first, second in EDGES:
        assert first in adjacency and second in adjacency
        adjacency[first].add(second)
        adjacency[second].add(first)

    return adjacency


ADJACENCY = build_adjacency()


def get_neighbors(node_id):
    """Renvoie les sommets accessibles en un coup depuis node_id."""
    return tuple(sorted(ADJACENCY[node_id]))


def shortest_distance(start, end):
    """Distance minimale (en nombre d'arêtes) entre deux sommets."""
    if start == end:
        return 0

    visited = {start}
    queue = [(start, 0)]

    while queue:
        current, distance = queue.pop(0)
        for neighbor in ADJACENCY[current]:
            if neighbor == end:
                return distance + 1
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))

    raise ValueError(f"Aucun chemin entre {start} et {end}")


if __name__ == "__main__":
    validate_nodes()
    for node_id, position in NODES.items():
        print(f"{node_id}: {position}")
