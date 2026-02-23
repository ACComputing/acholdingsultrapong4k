import pygame
import sys
import math
import random

# ------------------------------------------------------------
# Dynamic Sound Engine (procedural, no external files)
# ------------------------------------------------------------
class SoundEngine:
    def __init__(self):
        # Force re‑initialisation to mono (1 channel)
        pygame.mixer.quit()
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self.sample_rate = 22050

    def _generate_tone(self, frequency, duration, volume=0.3):
        """Generate a sine wave as a pygame Sound object."""
        n_samples = int(self.sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = float(i) / self.sample_rate
            value = math.sin(2 * math.pi * frequency * t)
            int_val = int(volume * 32767 * value)
            samples.append(int_val)

        import array
        sample_array = array.array('h', samples)          # signed 16‑bit
        # Use Sound(buffer=...) – works with 1‑channel raw data
        sound = pygame.mixer.Sound(buffer=bytes(sample_array))
        return sound

    def hit_paddle(self):
        sound = self._generate_tone(frequency=440, duration=0.1, volume=0.2)
        sound.play()

    def score(self):
        sound = self._generate_tone(frequency=220, duration=0.2, volume=0.3)
        sound.play()

# ------------------------------------------------------------
# Game constants
# ------------------------------------------------------------
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 15, 100
BALL_SIZE = 15
FPS = 60
BALL_SPEED = 7                     # constant speed (Atari‑like)
MAX_ANGLE = math.pi / 3            # 60 degrees max deflection

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

# ------------------------------------------------------------
# Paddle class
# ------------------------------------------------------------
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 7

    def move_ai(self, ball_y):
        if self.rect.centery < ball_y - 10:
            self.rect.y += self.speed
        elif self.rect.centery > ball_y + 10:
            self.rect.y -= self.speed
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def move_mouse(self, mouse_y):
        self.rect.y = mouse_y - PADDLE_HEIGHT // 2
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)

# ------------------------------------------------------------
# Ball class
# ------------------------------------------------------------
class Ball:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BALL_SIZE, BALL_SIZE)
        self.reset()

    def reset(self):
        """Center ball and give it a random direction."""
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        angle = random.uniform(-MAX_ANGLE, MAX_ANGLE)  # radians
        direction = random.choice([-1, 1])
        self.vx = direction * BALL_SPEED * math.cos(angle)
        self.vy = BALL_SPEED * math.sin(angle)

    def move(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

    def bounce_y(self):
        self.vy = -self.vy

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)

# ------------------------------------------------------------
# Main menu
# ------------------------------------------------------------
def main_menu(screen, clock):
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 36)

    title_text = font.render("PONG", True, WHITE)
    start_text = small_font.render("START", True, WHITE)
    quit_text = small_font.render("QUIT", True, WHITE)

    start_rect = start_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
    quit_rect = quit_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    return "game"
                if quit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        screen.fill(BLACK)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 150))
        screen.blit(start_text, start_rect)
        screen.blit(quit_text, quit_rect)

        mouse_pos = pygame.mouse.get_pos()
        if start_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, GRAY, start_rect.inflate(20, 10), 2)
        if quit_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, GRAY, quit_rect.inflate(20, 10), 2)

        pygame.display.flip()
        clock.tick(FPS)

# ------------------------------------------------------------
# Game over prompt
# ------------------------------------------------------------
def game_over_prompt(screen, clock):
    font = pygame.font.Font(None, 48)
    prompt_text = font.render("Game over? (y/n)", True, WHITE)
    text_rect = prompt_text.get_rect(center=(WIDTH//2, HEIGHT//2))

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    return True
                if event.key == pygame.K_n:
                    return False

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        screen.blit(prompt_text, text_rect)
        pygame.display.flip()
        clock.tick(FPS)

# ------------------------------------------------------------
# Main game
# ------------------------------------------------------------
def game(screen, clock, sound_engine):
    left_paddle = Paddle(30, HEIGHT//2 - PADDLE_HEIGHT//2)
    right_paddle = Paddle(WIDTH - 30 - PADDLE_WIDTH, HEIGHT//2 - PADDLE_HEIGHT//2)
    ball = Ball(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2)

    left_score = 0
    right_score = 0
    font = pygame.font.Font(None, 36)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        # Mouse control for right paddle
        mouse_y = pygame.mouse.get_pos()[1]
        right_paddle.move_mouse(mouse_y)

        # AI for left paddle
        left_paddle.move_ai(ball.rect.centery)

        # Ball movement
        ball.move()

        # Wall collisions (top/bottom)
        if ball.rect.top <= 0 or ball.rect.bottom >= HEIGHT:
            ball.bounce_y()

        # --- Paddle collisions (classic Atari physics) ---
        # Left paddle (ball moving left to right)
        if ball.rect.colliderect(left_paddle.rect) and ball.vx < 0:
            # Offset from paddle center, normalized to [-1, 1]
            offset = (ball.rect.centery - left_paddle.rect.centery) / (PADDLE_HEIGHT / 2)
            offset = max(-1, min(1, offset))          # clamp
            # New angle: offset * MAX_ANGLE
            angle = offset * MAX_ANGLE
            # New velocity (constant speed, now moving right)
            ball.vx = BALL_SPEED * math.cos(angle)
            ball.vy = BALL_SPEED * math.sin(angle)
            # Shift ball outside paddle to avoid sticking
            ball.rect.left = left_paddle.rect.right + 1
            sound_engine.hit_paddle()

        # Right paddle (ball moving right to left)
        if ball.rect.colliderect(right_paddle.rect) and ball.vx > 0:
            offset = (ball.rect.centery - right_paddle.rect.centery) / (PADDLE_HEIGHT / 2)
            offset = max(-1, min(1, offset))
            angle = offset * MAX_ANGLE
            ball.vx = -BALL_SPEED * math.cos(angle)   # negative = left
            ball.vy = BALL_SPEED * math.sin(angle)
            ball.rect.right = right_paddle.rect.left - 1
            sound_engine.hit_paddle()

        # Scoring
        if ball.rect.left <= 0:
            right_score += 1
            sound_engine.score()
            ball.reset()
        if ball.rect.right >= WIDTH:
            left_score += 1
            sound_engine.score()
            ball.reset()

        # Game over check
        if left_score >= 5 or right_score >= 5:
            restart = game_over_prompt(screen, clock)
            return restart

        # Drawing
        screen.fill(BLACK)
        pygame.draw.aaline(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT))

        left_paddle.draw(screen)
        right_paddle.draw(screen)
        ball.draw(screen)

        left_text = font.render(str(left_score), True, WHITE)
        right_text = font.render(str(right_score), True, WHITE)
        screen.blit(left_text, (WIDTH//4, 30))
        screen.blit(right_text, (3*WIDTH//4 - right_text.get_width(), 30))

        pygame.display.flip()
        clock.tick(FPS)

# ------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pong")
    clock = pygame.time.Clock()
    sound_engine = SoundEngine()

    while True:
        action = main_menu(screen, clock)
        if action == "game":
            restart = game(screen, clock, sound_engine)
            if not restart:
                break

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
