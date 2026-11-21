"""Règles du jeu et intelligence artificielle (minimax / alpha-bêta).

Le voleur part de N1, doit quitter cette case puis y revenir pour gagner.
Les trois policiers partent de N2, N7 et N9 : un policier est déjà voisin
de N1 et peut en bloquer l'accès dès que le voleur en sort. Un seul policier
joue par tour, après le voleur.
Les policiers gagnent en coinçant le voleur : toutes ses cases voisines
doivent être occupées par la police (ils ne peuvent pas entrer sur sa case).
Si la police occupe N1 pendant BLOCK_LIMIT tours consécutifs, le voleur
gagne par évasion forcée.
"""

import time
from collections import deque
from dataclasses import dataclass, replace

from graph import START_NODE, get_neighbors, shortest_distance

WIN_SCORE = 10_000
MAX_TURNS = 50

# Poids de l'évaluation (du point de vue du voleur).
GOAL_WEIGHT = 4       # proximité de N1
MOBILITY_WEIGHT = 4   # nombre de cases de fuite
PRESSURE_WEIGHT = 8   # policiers directement adjacents
NEAR_WEIGHT = 1       # policiers proches
NEAR_RANGE = 4
BLOCKED_BONUS = 6          # un policier immobilisé sur N1
BLOCK_PROGRESS_WEIGHT = 20  # chaque tour où N1 reste bloqué
BLOCK_LIMIT = 3            # 3 tours de blocage => victoire du voleur
UNREACHABLE = MAX_TURNS

# Budget de recherche.
THIEF_MAX_DEPTH = 10
THIEF_TIME_LIMIT = 0.35
POLICE_MAX_DEPTH = 8
POLICE_TIME_LIMIT = 0.25

POLICE_START = ("N2", "N7", "N9")
THIEF_TURN = "voleur"
POLICE_TURN = "police"


@dataclass(frozen=True)
class GameState:
    thief: str = START_NODE
    police: tuple[str, ...] = POLICE_START
    left_start: bool = False
    turn: int = 0
    to_move: str = THIEF_TURN
    winner: str | None = None
    blocked_start_turns: int = 0

    def is_terminal(self):
        return self.winner is not None or self.turn >= MAX_TURNS


def initial_state():
    return GameState()


def legal_thief_moves(state):
    """Le voleur avance d'une arête, sans pouvoir traverser un policier."""
    if state.is_terminal() or state.to_move != THIEF_TURN:
        return ()
    return tuple(move for move in get_neighbors(state.thief)
                 if move not in state.police)


def legal_police_moves(state):
    """Un seul policier joue : (index du policier, nouvelle case)."""
    if state.is_terminal() or state.to_move != POLICE_TURN:
        return ()

    moves = []
    for index, position in enumerate(state.police):
        other_police = state.police[:index] + state.police[index + 1:]
        for neighbor in get_neighbors(position):
            # Un policier ne peut ni entrer sur le voleur, ni se superposer.
            if neighbor != state.thief and neighbor not in other_police:
                moves.append((index, neighbor))
    return tuple(moves)


def _thief_blocked(state):
    """Vrai si toutes les sorties du voleur sont occupées par la police."""
    return all(neighbor in state.police for neighbor in get_neighbors(state.thief))


def apply_thief_move(state, new_position):
    """Joue le coup du voleur puis passe la main à la police."""
    if new_position not in legal_thief_moves(state):
        raise ValueError(f"Déplacement du voleur invalide : {state.thief} -> {new_position}")

    left_start = state.left_start or new_position != START_NODE
    winner = "voleur" if left_start and new_position == START_NODE else None

    return replace(
        state,
        thief=new_position,
        left_start=left_start,
        to_move=POLICE_TURN if winner is None else state.to_move,
        winner=winner,
    )


def apply_police_move(state, move):
    """Joue le coup d'un policier, puis vérifie capture / blocage."""
    if move not in legal_police_moves(state):
        raise ValueError(f"Déplacement de la police invalide : {move}")

    index, new_position = move
    police = list(state.police)
    police[index] = new_position
    police = tuple(police)

    blocked_turns = (state.blocked_start_turns + 1
                     if START_NODE in police else 0)

    winner = None
    if blocked_turns >= BLOCK_LIMIT:
        winner = "voleur"  # N1 bloqué trop longtemps : évasion forcée
    elif state.turn + 1 >= MAX_TURNS:
        winner = "police"  # le voleur n'a pas eu le temps de rentrer

    next_state = replace(
        state,
        police=police,
        turn=state.turn + 1,
        to_move=THIEF_TURN,
        winner=winner,
        blocked_start_turns=blocked_turns,
    )

    if winner is None and _thief_blocked(next_state):
        next_state = replace(next_state, winner="police")  # blocage

    return next_state


def _free_exits(state, position):
    """Cases voisines d'une position encore libres pour le voleur."""
    return sum(neighbor not in state.police for neighbor in get_neighbors(position))


def distance_to_start(state, position=None):
    """Distance réelle jusqu'à N1 en contournant les cases occupées.

    Renvoie UNREACHABLE si N1 est occupé ou si aucun chemin n'existe.
    """
    if position is None:
        position = state.thief
    if position == START_NODE:
        return 0
    if START_NODE in state.police:
        return UNREACHABLE

    visited = {position}
    queue = deque([(position, 0)])

    while queue:
        current, distance = queue.popleft()
        for neighbor in get_neighbors(current):
            if neighbor == START_NODE:
                return distance + 1
            if neighbor not in state.police and neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))

    return UNREACHABLE


def evaluate(state):
    """Estime la position du point de vue du voleur (le plus grand est le mieux)."""
    if state.winner == "voleur":
        return WIN_SCORE - state.turn  # gagner vite est préférable
    if state.winner == "police":
        return -WIN_SCORE + state.turn

    exits = _free_exits(state, state.thief)
    if exits == 0:
        return -WIN_SCORE + state.turn  # le voleur est coincé

    score = MOBILITY_WEIGHT * exits

    if state.left_start:
        score -= GOAL_WEIGHT * min(distance_to_start(state), UNREACHABLE)

    adjacent = sum(shortest_distance(cop, state.thief) == 1 for cop in state.police)
    score -= PRESSURE_WEIGHT * adjacent

    near = sum(
        max(0, NEAR_RANGE - shortest_distance(cop, state.thief))
        for cop in state.police
    )
    score -= NEAR_WEIGHT * near

    # Un policier sur N1 bloque l'arrivée, mais il est immobilisé : les autres
    # policiers sont trop peu nombreux pour former un piège.
    if START_NODE in state.police:
        score += BLOCKED_BONUS + BLOCK_PROGRESS_WEIGHT * state.blocked_start_turns

    return score


def ordered_thief_moves(state):
    """Les coups qui rapprochent de N1 (ou dégagent le plus de sorties) d'abord."""
    moves = legal_thief_moves(state)
    if START_NODE in state.police:
        return tuple(sorted(moves, key=lambda m: (-_free_exits(state, m),
                                                  distance_to_start(state, m))))
    return tuple(sorted(moves, key=lambda m: (distance_to_start(state, m),
                                              -len(get_neighbors(m)))))


def ordered_police_moves(state):
    """Les coups les plus dangereux pour le voleur d'abord."""
    return tuple(sorted(legal_police_moves(state),
                        key=lambda m: evaluate(apply_police_move(state, m))))


def minimax(state, depth, alpha, beta, table=None):
    """Minimax alpha-bêta avec table de transposition.

    Le voleur maximise, la police minimise. La table stocke des bornes
    (EXACT / LOWER / UPPER) pour éviter de recalculer les mêmes positions.
    """
    if depth <= 0 or state.is_terminal():
        return evaluate(state)

    if state.to_move == THIEF_TURN and not legal_thief_moves(state):
        return -WIN_SCORE + state.turn
    if state.to_move == POLICE_TURN and not legal_police_moves(state):
        return evaluate(state)

    if table is not None:
        entry = table.get(state)
        if entry is not None and entry[0] >= depth:
            stored_depth, value, flag = entry
            if flag == "EXACT":
                return value
            if flag == "LOWER":
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

    alpha_origin, beta_origin = alpha, beta
    maximizing = state.to_move == THIEF_TURN
    moves = ordered_thief_moves(state) if maximizing else ordered_police_moves(state)

    if maximizing:
        best = float("-inf")
        for move in moves:
            score = minimax(apply_thief_move(state, move), depth - 1,
                            alpha, beta, table)
            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
    else:
        best = float("inf")
        for move in moves:
            score = minimax(apply_police_move(state, move), depth - 1,
                            alpha, beta, table)
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break

    if table is not None:
        flag = ("EXACT" if alpha_origin < best < beta_origin else
                "LOWER" if best >= beta_origin else "UPPER")
        table[state] = (depth, best, flag)

    return best


def _search_root(state, depth, maximizing, table):
    """Renvoie (meilleur coup, meilleur score) à une profondeur donnée."""
    moves = ordered_thief_moves(state) if maximizing else ordered_police_moves(state)
    best_move = moves[0] if moves else None
    best_score = float("-inf") if maximizing else float("inf")
    alpha, beta = float("-inf"), float("inf")

    for move in moves:
        if maximizing:
            score = minimax(apply_thief_move(state, move), depth - 1,
                            alpha, beta, table)
            if score > best_score:
                best_score, best_move = score, move
            alpha = max(alpha, best_score)
        else:
            score = minimax(apply_police_move(state, move), depth - 1,
                            alpha, beta, table)
            if score < best_score:
                best_score, best_move = score, move
            beta = min(beta, best_score)

    return best_move, best_score


def iterative_search(state, maximizing, max_depth, time_limit):
    """Approfondissement itératif : on garde le meilleur coup entièrement calculé."""
    moves = (legal_thief_moves(state) if maximizing else legal_police_moves(state))
    if not moves:
        return None, 0, 0

    best_move = moves[0]
    best_score = 0
    reached_depth = 0
    table = {}
    start = time.perf_counter()

    for depth in range(2, max_depth + 1, 2):
        elapsed = time.perf_counter() - start
        if elapsed >= time_limit:
            break

        move, score = _search_root(state, depth, maximizing, table)
        if move is not None:
            best_move, best_score, reached_depth = move, score, depth
        if abs(score) >= WIN_SCORE - MAX_TURNS:  # victoire ou défaite certaine
            break

    return best_move, best_score, reached_depth


def choose_thief_move(state, max_depth=THIEF_MAX_DEPTH, time_limit=THIEF_TIME_LIMIT):
    """Choisit le meilleur coup pour le voleur (minimax approfondi)."""
    move, score, depth = iterative_search(state, True, max_depth, time_limit)
    return move, score, depth


def choose_police_move(state, max_depth=POLICE_MAX_DEPTH,
                       time_limit=POLICE_TIME_LIMIT):
    """Choisit le meilleur coup pour la police."""
    move, score, depth = iterative_search(state, False, max_depth, time_limit)
    return move


class Game:
    """Une partie : IA de chaque camp, un coup chacun par tour."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = initial_state()
        self.thief_score = 0
        self.thief_depth = 0
        self.history = [self.state.thief]
        self.police_history = [self.state.police]
        return self.state

    def step(self):
        """Joue un tour complet : le voleur, puis un policier."""
        if self.state.is_terminal():
            return self.state

        if self.state.to_move == THIEF_TURN:
            if not legal_thief_moves(self.state):
                self.state = replace(self.state, winner="police")
                return self.state

            move, score, depth = choose_thief_move(self.state)
            self.thief_score = score
            self.thief_depth = depth
            if move is not None:
                self.state = apply_thief_move(self.state, move)
                self.history.append(self.state.thief)

        if not self.state.is_terminal() and self.state.to_move == POLICE_TURN:
            move = choose_police_move(self.state)
            if move is not None:
                self.state = apply_police_move(self.state, move)
                self.police_history.append(self.state.police)
            else:
                # Aucun coup disponible : la police passe son tour.
                waited = self.state.turn + 1
                winner = "police" if waited >= MAX_TURNS else None
                self.state = replace(self.state, to_move=THIEF_TURN,
                                     turn=waited, winner=winner)

        return self.state

    def play_until_end(self):
        while not self.state.is_terminal():
            self.step()
        return self.state


if __name__ == "__main__":
    game = Game()
    while not game.state.is_terminal():
        game.step()
        print(f"Tour {game.state.turn:2d} | voleur {game.state.thief:3s} "
              f"| police {', '.join(game.state.police)} | gagnant {game.state.winner}")
    print("Vainqueur final :", game.state.winner)
