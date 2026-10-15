
import pygame
import math
from array import array

from .paddle import Paddle
from .ball import Ball
from .brick import Brick

WHITE = (255, 255, 255)
BG = (15, 15, 25)
GREEN = (80, 220, 120)
RED = (240, 80, 80)
GRAY = (190, 190, 200)

BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]

DIFFICULTIES = {
    "Easy": {"ball_speed": 3, "paddle_width": 125},
    "Medium": {"ball_speed": 4, "paddle_width": 100},
    "Hard": {"ball_speed": 6, "paddle_width": 75},
}


class GameEngine:
    @staticmethod
    def _make_tone(frequency, duration, volume=0.25):
        """Generate a short sound effect without external audio files."""
        sample_rate = 22050
        total_samples = int(sample_rate * duration)
        samples = array("h")

        for i in range(total_samples):
            envelope = 1.0 - (i / total_samples)
            value = int(
                32767
                * volume
                * envelope
                * math.sin(
                    2 * math.pi * frequency * i / sample_rate
                )
            )
            samples.append(value)

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def __init__(self, width, height, difficulty="Medium"):
        self.width = width
        self.height = height
        self.difficulty = difficulty

        settings = DIFFICULTIES[difficulty]
        self.ball_speed = settings["ball_speed"]
        paddle_width = settings["paddle_width"]

        self.paddle = Paddle(
            width // 2 - paddle_width // 2,
            height - 30,
            paddle_width,
            14,
        )

        self.ball = Ball(width // 2, height - 50, radius=8)
        self.ball.vx = self.ball_speed
        self.ball.vy = -self.ball_speed

        self.rows, self.cols = 5, 8
        self.bricks = self._build_bricks(self.rows, self.cols)

        self.lives = 3
        self.score = 0

        self.font = pygame.font.SysFont("Arial", 28)
        self.title_font = pygame.font.SysFont("Arial", 44, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 20)

        self.game_over = False
        self.result = None
        self.quit_requested = False
        self.restart_requested = False
        self.selected_difficulty = difficulty

        # Task 4: Sound effects.
        self.sounds = {
            "brick": None,
            "bounce": None,
            "win": None,
            "lose": None,
        }

        try:
            # The mixer might not be available on every system.
            if pygame.mixer.get_init():
                self.sounds["brick"] = self._make_tone(900, 0.08)
                self.sounds["bounce"] = self._make_tone(450, 0.05)
                self.sounds["win"] = self._make_tone(1000, 0.35)
                self.sounds["lose"] = self._make_tone(180, 0.45)
        except (pygame.error, ValueError, OverflowError):
            print("Audio unavailable; continuing without sound.")

        self._paddle_was_colliding = False

    def _play_sound(self, name):
        sound = self.sounds.get(name)

        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

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
        # Task 3: Replay with a selected difficulty.
        if self.game_over and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_KP1):
                self.selected_difficulty = "Easy"
                self.restart_requested = True

            elif event.key in (pygame.K_2, pygame.K_KP2):
                self.selected_difficulty = "Medium"
                self.restart_requested = True

            elif event.key in (pygame.K_3, pygame.K_KP3):
                self.selected_difficulty = "Hard"
                self.restart_requested = True

            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.quit_requested = True

    def handle_input(self):
        if self.game_over:
            return

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    def _resolve_collision(self, target_rect, previous_x, previous_y):
        """Bounce the ball according to the side it hit."""
        radius = self.ball.radius

        previous_rect = pygame.Rect(
            round(previous_x - radius),
            round(previous_y - radius),
            radius * 2,
            radius * 2,
        )
        current_rect = self.ball.rect()

        if previous_rect.bottom <= target_rect.top:
            self.ball.vy = -abs(self.ball.vy)

        elif previous_rect.top >= target_rect.bottom:
            self.ball.vy = abs(self.ball.vy)

        elif previous_rect.right <= target_rect.left:
            self.ball.vx = -abs(self.ball.vx)

        elif previous_rect.left >= target_rect.right:
            self.ball.vx = abs(self.ball.vx)

        else:
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

        previous_x = self.ball.x
        previous_y = self.ball.y

        self.ball.move()

        # Left and right wall collisions.
        if self.ball.x - self.ball.radius <= 0 and self.ball.vx < 0:
            self.ball.vx = abs(self.ball.vx)
            self._play_sound("bounce")

        elif (
            self.ball.x + self.ball.radius >= self.width
            and self.ball.vx > 0
        ):
            self.ball.vx = -abs(self.ball.vx)
            self._play_sound("bounce")

        # Top wall collision.
        if self.ball.y - self.ball.radius <= 0 and self.ball.vy < 0:
            self.ball.vy = abs(self.ball.vy)
            self._play_sound("bounce")

        # Paddle collision.
        paddle_rect = self.paddle.rect()
        paddle_colliding = self.ball.rect().colliderect(paddle_rect)

        if paddle_colliding:
            self._resolve_collision(
                paddle_rect, previous_x, previous_y
            )

            # Avoid playing the sound repeatedly during one contact.
            if not self._paddle_was_colliding:
                self._play_sound("bounce")

        self._paddle_was_colliding = paddle_colliding

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
                self._play_sound("brick")
                break

        # Ball falls below the screen.
        if self.ball.y - self.ball.radius > self.height:
            self.lives -= 1

            if self.lives <= 0:
                self.game_over = True
                self.result = "lose"
                self._play_sound("lose")
            else:
                self._reset_ball()

        # All bricks destroyed: player wins.
        if (
            not self.game_over
            and all(not brick.alive for brick in self.bricks)
        ):
            self.game_over = True
            self.result = "win"
            self._play_sound("win")

    def _reset_ball(self):
        self.ball.x = self.width // 2
        self.ball.y = self.height - 50
        self.ball.vx = self.ball_speed
        self.ball.vy = -self.ball_speed
        self._paddle_was_colliding = False

    def render(self, screen):
        screen.fill(BG)

        # Draw paddle and ball.
        pygame.draw.rect(screen, WHITE, self.paddle.rect())
        pygame.draw.circle(
            screen,
            WHITE,
            (int(self.ball.x), int(self.ball.y)),
            self.ball.radius,
        )

        # Draw remaining bricks.
        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        # Score and lives.
        score_text = self.font.render(
            f"Score: {self.score}", True, WHITE
        )
        screen.blit(score_text, (10, 10))

        lives_text = self.font.render(
            f"Lives: {self.lives}", True, WHITE
        )
        screen.blit(lives_text, (self.width - 130, 10))

        # End screen and replay options.
        if self.game_over:
            overlay = pygame.Surface(
                (self.width, self.height), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            if self.result == "win":
                title = "YOU WIN!"
                title_color = GREEN
            else:
                title = "GAME OVER"
                title_color = RED

            title_text = self.title_font.render(
                title, True, title_color
            )
            final_score = self.font.render(
                f"Final Score: {self.score}", True, WHITE
            )
            replay_text = self.small_font.render(
                "Play Again - Choose Difficulty", True, WHITE
            )
            easy_text = self.small_font.render(
                "1 - Easy: Slower Ball, Wider Paddle", True, GREEN
            )
            medium_text = self.small_font.render(
                "2 - Medium: Normal Difficulty", True, WHITE
            )
            hard_text = self.small_font.render(
                "3 - Hard: Faster Ball, Narrower Paddle", True, RED
            )
            exit_text = self.small_font.render(
                "Esc - Exit", True, GRAY
            )

            screen.blit(
                title_text,
                title_text.get_rect(
                    center=(self.width // 2, 125)
                ),
            )
            screen.blit(
                final_score,
                final_score.get_rect(
                    center=(self.width // 2, 190)
                ),
            )
            screen.blit(
                replay_text,
                replay_text.get_rect(
                    center=(self.width // 2, 260)
                ),
            )
            screen.blit(
                easy_text,
                easy_text.get_rect(
                    center=(self.width // 2, 305)
                ),
            )
            screen.blit(
                medium_text,
                medium_text.get_rect(
                    center=(self.width // 2, 345)
                ),
            )
            screen.blit(
                hard_text,
                hard_text.get_rect(
                    center=(self.width // 2, 385)
                ),
            )
            screen.blit(
                exit_text,
                exit_text.get_rect(
                    center=(self.width // 2, 435)
                ),
            )
