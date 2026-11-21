"""Pions policiers du jeu Police-Voleur.

La liste des positions vient de l'état de la partie : elle est vide tant que
les policiers ne sont pas introduits dans le jeu.
"""


def draw_police(screen, pygame, nodes, to_screen, positions, blue, white, font):
    """Dessine les policiers présents sur le plateau."""
    black = (20, 20, 20)

    for node_id in positions:
        x, y = to_screen(nodes[node_id])
        pygame.draw.circle(screen, black, (x, y), 17)
        pygame.draw.circle(screen, blue, (x, y), 14)

        label = font.render("P", True, white)
        screen.blit(
            label,
            (x - label.get_width() // 2, y - label.get_height() // 2)
        )
