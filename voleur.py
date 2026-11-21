"""Pion et parcours du voleur."""

THIEF_POSITION = "N1"


def draw_thief(screen, pygame, nodes, to_screen, red, white, font,
               position=THIEF_POSITION):
    """Dessine le voleur sur sa case actuelle."""
    black = (20, 20, 20)
    x, y = to_screen(nodes[position])

    pygame.draw.circle(screen, black, (x, y), 19)
    pygame.draw.circle(screen, red, (x, y), 16)

    label = font.render("V", True, white)
    screen.blit(
        label,
        (x - label.get_width() // 2, y - label.get_height() // 2)
    )


def draw_thief_path(screen, pygame, nodes, to_screen, red, history):
    """Trace le chemin déjà parcouru par le voleur."""
    if len(history) < 2:
        return

    points = [to_screen(nodes[node_id]) for node_id in history]
    pygame.draw.lines(screen, red, False, points, 3)
