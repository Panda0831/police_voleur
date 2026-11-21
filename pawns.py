"""Représentation et affichage des pions du jeu Police-Voleur."""

POLICE_POSITIONS = ["N2", "N7", "N9"]
THIEF_POSITION = "N1"


def draw_pawns(screen, pygame, nodes, to_screen, blue, red, white, font):
    """Dessine les trois policiers et le voleur sur leurs nœuds."""
    black = (20, 20, 20)

    # Trois policiers
    for node_id in POLICE_POSITIONS:
        x, y = to_screen(nodes[node_id])
        pygame.draw.circle(screen, black, (x, y), 17)
        pygame.draw.circle(screen, blue, (x, y), 14)

        label = font.render("P", True, white)
        screen.blit(
            label,
            (x - label.get_width() // 2, y - label.get_height() // 2)
        )

    # Voleur au centre
    x, y = to_screen(nodes[THIEF_POSITION])
    pygame.draw.circle(screen, black, (x, y), 19)
    pygame.draw.circle(screen, red, (x, y), 16)

    label = font.render("V", True, white)
    screen.blit(
        label,
        (x - label.get_width() // 2, y - label.get_height() // 2)
    )
