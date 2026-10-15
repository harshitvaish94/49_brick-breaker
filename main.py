
import pygame
from game.game_engine import GameEngine

pygame.init()

WIDTH, HEIGHT = 640, 560
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brick Breaker - Pygame Version")

clock = pygame.time.Clock()
FPS = 60

engine = GameEngine(WIDTH, HEIGHT)


def main():
    global engine

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                engine.handle_event(event)

        if engine.quit_requested:
            running = False

        # Start a fresh game when a difficulty is selected.
        if engine.restart_requested:
            chosen_difficulty = engine.selected_difficulty
            engine = GameEngine(
                WIDTH,
                HEIGHT,
                difficulty=chosen_difficulty,
            )

        if running:
            engine.handle_input()
            engine.update()
            engine.render(SCREEN)

            pygame.display.flip()
            clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()

