# main.py

import math

import pygame

from game import BLOCK_LIMIT, Game
from graph import NODES, START_NODE
from police import draw_police
from voleur import draw_thief, draw_thief_path

pygame.init()

WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Plateau géométrique - Police-Voleur")

WHITE = (255, 255, 255)
GRID = (205, 205, 205)
GRID_MAJOR = (175, 175, 175)
BLACK = (20, 20, 20)
BLUE = (35, 130, 240)
ORANGE = (245, 145, 20)
RED = (235, 40, 40)

CENTER_X = 550
CENTER_Y = 350
SCALE_X = 155
SCALE_Y = 155

font = pygame.font.SysFont("Arial", 16)
node_font = pygame.font.SysFont("Arial", 14, bold=True)
pawn_font = pygame.font.SysFont("Arial", 16, bold=True)
title_font = pygame.font.SysFont("Arial", 22)
subtitle_font = pygame.font.SysFont("Arial", 17)

STEP_EVENT = pygame.USEREVENT + 1
STEP_DELAY_MS = 800

game = Game()
auto_play = True
pygame.time.set_timer(STEP_EVENT, STEP_DELAY_MS)
clock = pygame.time.Clock()


def to_screen(position):
    x, y = position
    return (int(CENTER_X + x * SCALE_X), int(CENTER_Y - y * SCALE_Y))


def draw_grid():
    for i in range(-3, 4):
        x = CENTER_X + i * SCALE_X
        pygame.draw.line(screen, GRID_MAJOR if i == 0 else GRID,
                         (x, 60), (x, 660), 1)

    for i in range(-4, 5):
        y_value = i / 2
        y = CENTER_Y - y_value * SCALE_Y
        pygame.draw.line(screen, GRID_MAJOR if i == 0 else GRID,
                         (55, y), (1045, y), 1)


def draw_arc_circle(center, rx, ry, start_angle, end_angle, color=BLACK, width=3, steps=100):
    cx, cy = center
    points = []
    for step in range(steps + 1):
        angle = start_angle + (end_angle - start_angle) * step / steps
        position = (cx + rx * math.cos(angle), cy + ry * math.sin(angle))
        points.append(to_screen(position))
    pygame.draw.lines(screen, color, False, points, width)


def draw_board():
    ellipse_rect = pygame.Rect(
        to_screen((-3.25, 1.95))[0],
        to_screen((-3.25, 1.95))[1],
        int(6.50 * SCALE_X),
        int(3.90 * SCALE_Y)
    )
    pygame.draw.ellipse(screen, BLACK, ellipse_rect, 3)

    pygame.draw.line(screen, BLACK, to_screen((-3.35, 0)), to_screen((3.35, 0)), 3)
    pygame.draw.line(screen, BLACK, to_screen((0, -2.25)), to_screen((0, 2.25)), 3)

    draw_arc_circle((0.0, 1.82), 0.55, 0.37, math.pi, 2 * math.pi)
    draw_arc_circle((0.0, -1.82), 0.55, 0.37, 0.0, math.pi)
    draw_arc_circle((3.0, 0.0), 0.65, 0.38, math.pi / 2, 3 * math.pi / 2)
    draw_arc_circle((-3., 0.0), 0.65, 0.38, -math.pi / 2, math.pi / 2)

    center = to_screen((0.0, 0.0))
    pygame.draw.circle(screen, BLACK, center, int(0.50 * SCALE_X), 3)


def draw_nodes():
    for node_id, position in NODES.items():
        number = int(node_id[1:])
        x, y = to_screen(position)

        if number == 1:
            color = RED
        elif 10 <= number <= 13:
            color = ORANGE
        else:
            color = BLUE

        pygame.draw.circle(screen, BLACK, (x, y), 8)
        pygame.draw.circle(screen, color, (x, y), 6)

        label = node_font.render(node_id, True, BLACK)
        screen.blit(label, (x + 10, y - 22))


def draw_hud(state):
    screen.blit(title_font.render("Police - Voleur : retour au depart", True, BLACK),
                (25, 12))

    ia = (f"IA voleur : minimax profondeur {game.thief_depth} "
          f"| evaluation {game.thief_score:+d}")
    screen.blit(font.render(ia, True, BLUE), (25, 40))

    forced_escape = state.winner == "voleur" and START_NODE in state.police

    if state.winner == "voleur":
        objective = ("Gagne ! N1 bloque trop longtemps : evasion forcee."
                     if forced_escape else "Gagne ! Le voleur est revenu sur N1.")
        banner_text = ("N1 bloque : le voleur s'echappe !" if forced_escape
                       else "Le voleur a regagne sa case depart !")
        banner_color = RED
    elif state.winner == "police":
        objective = "Perdu ! Les policiers ont coince le voleur."
        banner_text = "Les policiers ont coince le voleur !"
        banner_color = BLUE
    elif not state.left_start:
        objective = "Objectif : quitter N1 (case de depart)"
    else:
        objective = "Objectif : revenir sur N1 (case de depart)"

    police_text = ",".join(state.police)
    if START_NODE in state.police and not state.winner:
        police_text += f" (N1 bloque {state.blocked_start_turns}/{BLOCK_LIMIT})"
    status = (f"{objective}   |   Voleur : {state.thief}   |   "
              f"Police : {police_text}   |   Tour : {state.turn}")
    screen.blit(subtitle_font.render(status, True,
                                     banner_color if state.winner else BLACK),
                (25, 662))

    mode = "auto" if auto_play else "manuel"
    controls = f"ESPACE : jouer un coup   |   A : mode {mode}   |   R : recommencer"
    screen.blit(font.render(controls, True, BLACK), (25, 682))

    if state.winner:
        banner = pygame.Rect(300, 100, 500, 50)
        pygame.draw.rect(screen, WHITE, banner)
        pygame.draw.rect(screen, banner_color, banner, 3)
        text = title_font.render(banner_text, True, banner_color)
        screen.blit(text, (banner.centerx - text.get_width() // 2,
                           banner.centery - text.get_height() // 2))


def refresh_caption():
    mode = "auto" if auto_play else "manuel"
    pygame.display.set_caption(f"Police-Voleur - IA minimax ({mode})")


refresh_caption()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == STEP_EVENT and auto_play:
            game.step()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                game.step()
            elif event.key == pygame.K_a:
                auto_play = not auto_play
                refresh_caption()
            elif event.key == pygame.K_r:
                game.reset()

    screen.fill(WHITE)
    draw_grid()
    draw_board()
    draw_thief_path(screen, pygame, NODES, to_screen, RED, game.history)
    draw_nodes()
    draw_police(screen, pygame, NODES, to_screen,
                game.state.police, BLUE, WHITE, pawn_font)
    draw_thief(screen, pygame, NODES, to_screen, RED, WHITE, pawn_font,
               game.state.thief)
    draw_hud(game.state)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
