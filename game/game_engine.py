
import pygame
from .paddle import Paddle
from .ball import Ball
from .brick import Brick

# Game Engine

WHITE = (255, 255, 255)
BG = (15, 15, 25)

BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.paddle = Paddle(
            width // 2 - 50, height - 30, 100, 14
        )

        self.ball = Ball(width // 2, height - 50, radius=8)
        self.ball.vx, self.ball.vy = 4, -4

        self.rows, self.cols = 5, 8
        self.bricks = self._build_bricks(self.rows, self.cols)

        self.lives = 3
        self.score = 0
        self.font = pygame.font.SysFont("Arial", 28)
        self.game_over = False
        self.result = None

    def _build_bricks(self, rows, cols):
        bricks = []
        margin, gap, top = 30, 6, 60
        brick_w = (
            self.width - margin * 2 - gap * (cols - 1)
        ) // cols
        brick_h = 22

        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)
                bricks.append(Brick(x, y, brick_w, brick_h))

        return bricks

    def handle_event(self, event):
        # Paddle movement is handled in handle_input().
        pass

    def handle_input(self):
        if self.game_over:
            return

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    def _resolve_collision(self, target_rect, previous_x, previous_y):
        """Resolve a collision based on the ball's approach direction."""
        radius = self.ball.radius

        previous_rect = pygame.Rect(
            round(previous_x - radius),
            round(previous_y - radius),
            radius * 2,
            radius * 2,
        )

        current_rect = self.ball.rect()

        # The ball approached from above.
        if previous_rect.bottom <= target_rect.top:
            self.ball.vy = -abs(self.ball.vy)

        # The ball approached from below.
        elif previous_rect.top >= target_rect.bottom:
            self.ball.vy = abs(self.ball.vy)

        # The ball approached from the left.
        elif previous_rect.right <= target_rect.left:
            self.ball.vx = -abs(self.ball.vx)

        # The ball approached from the right.
        elif previous_rect.left >= target_rect.right:
            self.ball.vx = abs(self.ball.vx)

        else:
            # Corner or overlapping collision: use the smaller overlap.
            overlap_x = (
                min(current_rect.right, target_rect.right)
                - max(current_rect.left, target_rect.left)
            )

            overlap_y = (
                min(current_rect.bottom, target_rect.bottom)
                - max(current_rect.top, target_rect.top)
            )

            if overlap_x < overlap_y:
                if self.ball.x < target_rect.centerx:
                    self.ball.vx = -abs(self.ball.vx)
                else:
                    self.ball.vx = abs(self.ball.vx)
            else:
                if self.ball.y < target_rect.centery:
                    self.ball.vy = -abs(self.ball.vy)
                else:
                    self.ball.vy = abs(self.ball.vy)

    def update(self):
        if self.game_over:
            return

        # Remember the position before moving.
        previous_x = self.ball.x
        previous_y = self.ball.y

        self.ball.move()

        # Left and right walls.
        if (
            self.ball.x - self.ball.radius <= 0
            and self.ball.vx < 0
        ):
            self.ball.vx = abs(self.ball.vx)

        elif (
            self.ball.x + self.ball.radius >= self.width
            and self.ball.vx > 0
        ):
            self.ball.vx = -abs(self.ball.vx)

        # Top wall.
        if (
            self.ball.y - self.ball.radius <= 0
            and self.ball.vy < 0
        ):
            self.ball.vy = abs(self.ball.vy)

        # Paddle collision.
        paddle_rect = self.paddle.rect()

        if self.ball.rect().colliderect(paddle_rect):
            self._resolve_collision(
                paddle_rect, previous_x, previous_y
            )

        # Brick collision.
        for brick in self.bricks:
            if (
                brick.alive
                and self.ball.rect().colliderect(brick.rect())
            ):
                self._resolve_collision(
                    brick.rect(), previous_x, previous_y
                )

                brick.alive = False
                self.score += 1
                break

        # Ball fell below the screen.
        if self.ball.y - self.ball.radius > self.height:
            self.lives -= 1

            if self.lives <= 0:
                self.game_over = True
                self.result = "lose"
            else:
                self._reset_ball()

        # All bricks destroyed.
        if all(not brick.alive for brick in self.bricks):
            self.game_over = True
            self.result = "win"

    def _reset_ball(self):
        self.ball.x = self.width // 2
        self.ball.y = self.height - 50
        self.ball.vx, self.ball.vy = 4, -4

    def render(self, screen):
        screen.fill(BG)

        pygame.draw.rect(screen, WHITE, self.paddle.rect())

        pygame.draw.circle(
            screen,
            WHITE,
            (int(self.ball.x), int(self.ball.y)),
            self.ball.radius,
        )

        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        score_text = self.font.render(
            f"Score: {self.score}", True, WHITE
        )
        screen.blit(score_text, (10, 10))

        lives_text = self.font.render(
            f"Lives: {self.lives}", True, WHITE
        )
        screen.blit(
            lives_text, (self.width - 130, 10)
        )

        # Task 2 will replace this console message with an end screen.
        if self.game_over and not getattr(
            self, "_game_over_logged", False
        ):
            if self.result == "win":
                print("You win! Final score:", self.score)
            else:
                print("Game over! Final score:", self.score)

            self._game_over_logged = True
