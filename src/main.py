import pygame
import random
import sys
import os

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Flying Adventure")

# Game constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 800
GRAVITY = 0.15
INITIAL_GAME_SPEED = 8
FLAP_STRENGTH = -2
MAX_FALL_SPEED = 9
OBSTACLE_GAP = 200
OBSTACLE_SPACING = 500

# Colors
SKY_BLUE = (135, 206, 235)
CLOUD_WHITE = (255, 255, 255)
GRASS_GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Font setup
SCORE_FONT = pygame.font.SysFont('arial', 50)
MENU_FONT = pygame.font.SysFont('arial', 32)
GAME_OVER_FONT = pygame.font.SysFont('arial', 70)


def calculate_speed(score):
    """Calculate game speed based on player's score"""
    return INITIAL_GAME_SPEED + (score // 3)


def darken_color(color, amount=20):
    """Safely darken a color by ensuring values stay in valid range"""
    return (
        max(0, color[0] - amount),
        max(0, color[1] - amount),
        max(0, color[2] - amount)
    )


class Player:
    """Player character class"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.velocity = 0
        self.height = self.y
        self.time = 0
        self.animation_count = 0
        self.animation_timer = 0
        # Create simple circle-based player sprite
        self.radius = 15
        self.color = (255, 165, 0)  # Orange
        self.wing_phase = 0
        self.wing_timer = 0

    def flap(self):
        """Make the player character flap its wings"""
        self.velocity = FLAP_STRENGTH
        self.time = 0
        self.wing_phase = 2  # Wings fully extended

    def move(self):
        """Update player position based on physics"""
        self.time += 1
        displacement = GRAVITY * (self.time ** 2) + self.velocity * self.time

        if displacement > MAX_FALL_SPEED:
            displacement = MAX_FALL_SPEED
        elif displacement < 0:
            displacement -= 2

        self.y += displacement

        # Handle rotation based on movement
        if displacement < 0 or self.y < (self.height + 50):
            self.angle = 25
        else:
            if self.angle > -90:
                self.angle -= 5

        # Wing animation
        self.wing_timer += 1
        if self.wing_timer >= 5:
            self.wing_timer = 0
            self.wing_phase = max(0, self.wing_phase - 1)

    def draw(self, screen):
        """Draw the player character"""
        # Draw body (circle)
        pygame.draw.circle(screen, self.color, (self.x, int(self.y)), self.radius)

        # Draw eye
        pygame.draw.circle(screen, BLACK, (self.x + 5, int(self.y) - 5), 4)
        pygame.draw.circle(screen, WHITE, (self.x + 6, int(self.y) - 6), 2)

        # Draw beak
        beak_points = [(self.x + 15, int(self.y)), (self.x + 25, int(self.y) - 5), (self.x + 25, int(self.y) + 5)]
        pygame.draw.polygon(screen, (255, 140, 0), beak_points)

        # Draw wings based on wing phase and angle
        wing_y_offset = 0
        if self.wing_phase == 2:  # Fully extended
            wing_y_offset = -10
        elif self.wing_phase == 1:  # Mid-flap
            wing_y_offset = -5

        # Adjust wing position based on angle
        angle_rad = self.angle * 3.14159 / 180
        wing_rotation = min(20, max(-20, int(self.angle)))

        # Draw the wing
        wing_points = [
            (self.x - 5, int(self.y)),
            (self.x - 15, int(self.y + wing_y_offset + wing_rotation)),
            (self.x - 5, int(self.y + 5))
        ]
        pygame.draw.polygon(screen, (220, 120, 0), wing_points)

    def get_mask(self):
        """Return a simple rectangular collision mask"""
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


class Obstacle:
    """Obstacle that the player must avoid"""

    def __init__(self, x):
        self.x = x
        self.gap_height = 0
        self.top_height = 0
        self.bottom_y = 0
        self.width = 80
        self.passed = False
        self.set_height()
        self.color = BROWN
        self.dark_color = darken_color(BROWN)

    def set_height(self):
        """Randomly set the height of the obstacle"""
        self.gap_height = random.randrange(100, 400)
        self.top_height = self.gap_height - OBSTACLE_GAP
        self.bottom_y = self.gap_height

    def move(self, speed):
        """Move the obstacle to the left"""
        self.x -= speed

    def draw(self, screen):
        """Draw the top and bottom parts of the obstacle"""
        # Draw top obstacle
        pygame.draw.rect(screen, self.color, (self.x, 0, self.width, self.top_height))
        # Add some detail
        pygame.draw.rect(screen, self.dark_color,
                         (self.x, self.top_height - 30, self.width, 30))

        # Draw bottom obstacle
        pygame.draw.rect(screen, self.color, (self.x, self.bottom_y, self.width, SCREEN_HEIGHT - self.bottom_y))
        # Add some detail
        pygame.draw.rect(screen, self.dark_color,
                         (self.x, self.bottom_y, self.width, 30))

    def collide(self, player):
        """Check if player collides with the obstacle"""
        player_rect = player.get_mask()

        # Create rects for top and bottom obstacles
        top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        bottom_rect = pygame.Rect(self.x, self.bottom_y, self.width, SCREEN_HEIGHT - self.bottom_y)

        # Check for collision
        if player_rect.colliderect(top_rect) or player_rect.colliderect(bottom_rect):
            return True
        return False


class Ground:
    """Moving ground at the bottom of the screen"""

    def __init__(self, y):
        self.y = y
        self.height = SCREEN_HEIGHT - y
        self.x1 = 0
        self.x2 = SCREEN_WIDTH
        self.color = GRASS_GREEN
        self.dark_color = darken_color(GRASS_GREEN)

    def move(self, speed):
        """Move the ground to create scrolling effect"""
        self.x1 -= speed
        self.x2 -= speed

        if self.x1 + SCREEN_WIDTH <= 0:
            self.x1 = self.x2 + SCREEN_WIDTH
        if self.x2 + SCREEN_WIDTH <= 0:
            self.x2 = self.x1 + SCREEN_WIDTH

    def draw(self, screen):
        """Draw the ground"""
        pygame.draw.rect(screen, self.color, (self.x1, self.y, SCREEN_WIDTH, self.height))
        pygame.draw.rect(screen, self.color, (self.x2, self.y, SCREEN_WIDTH, self.height))

        # Add some detail to the ground
        for x in range(int(self.x1), int(self.x1 + SCREEN_WIDTH), 30):
            pygame.draw.line(screen, self.dark_color,
                             (x, self.y), (x, self.y + 5), 2)
        for x in range(int(self.x2), int(self.x2 + SCREEN_WIDTH), 30):
            pygame.draw.line(screen, self.dark_color,
                             (x, self.y), (x, self.y + 5), 2)


class Cloud:
    """Background cloud decoration"""

    def __init__(self):
        self.x = SCREEN_WIDTH + random.randint(0, 300)
        self.y = random.randint(50, 200)
        self.size = random.randint(40, 80)
        self.speed = random.uniform(1, 3)

    def move(self):
        """Move the cloud across the screen"""
        self.x -= self.speed

    def draw(self, screen):
        """Draw the cloud"""
        pygame.draw.circle(screen, CLOUD_WHITE, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, CLOUD_WHITE, (int(self.x - self.size * 0.5), int(self.y)), self.size * 0.8)
        pygame.draw.circle(screen, CLOUD_WHITE, (int(self.x + self.size * 0.5), int(self.y)), self.size * 0.8)

    def is_offscreen(self):
        """Check if cloud has moved off the screen"""
        return self.x < -self.size * 2


def draw_game_screen(screen, player, obstacles, ground, score, clouds):
    """Draw the main game screen with all elements"""
    # Draw sky background
    screen.fill(SKY_BLUE)

    # Draw clouds
    for cloud in clouds:
        cloud.draw(screen)

    # Draw player
    player.draw(screen)

    # Draw obstacles
    for obstacle in obstacles:
        obstacle.draw(screen)

    # Draw ground
    ground.draw(screen)

    # Draw score
    score_text = SCORE_FONT.render(f"Score: {score}", 1, WHITE)
    score_outline = SCORE_FONT.render(f"Score: {score}", 1, BLACK)
    screen.blit(score_outline, (SCREEN_WIDTH - 10 - score_text.get_width() + 2, 12))
    screen.blit(score_text, (SCREEN_WIDTH - 10 - score_text.get_width(), 10))

    pygame.display.update()


def username_screen(screen):
    """Display the username input screen"""
    input_box = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, 200, 40)
    button_box = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 60, 120, 40)
    active_color = (52, 152, 219)  # Blue
    inactive_color = (41, 128, 185)  # Darker blue
    box_color = inactive_color
    active = False
    username = ''
    clock = pygame.time.Clock()

    # Create some clouds for the background
    clouds = [Cloud() for _ in range(5)]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                elif button_box.collidepoint(event.pos) and username.strip():
                    return username
                else:
                    active = False
                box_color = active_color if active else inactive_color
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN and username.strip():
                        return username
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        if len(username) < 15:
                            username += event.unicode

        # Draw background
        screen.fill(SKY_BLUE)

        # Update and draw clouds
        for cloud in clouds:
            cloud.move()
            cloud.draw(screen)
            if cloud.is_offscreen():
                clouds.remove(cloud)
                clouds.append(Cloud())

        # Draw title
        title_text = GAME_OVER_FONT.render("Flying Adventure", 1, WHITE)
        title_shadow = GAME_OVER_FONT.render("Flying Adventure", 1, BLACK)
        screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title_text.get_width() // 2 + 2, 152))
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))

        # Drawing player character as mascot
        player_demo = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
        player_demo.draw(screen)

        # Draw instruction
        label_text = "Enter your username:"
        label_shadow = MENU_FONT.render(label_text, True, BLACK)
        label_surface = MENU_FONT.render(label_text, True, WHITE)
        label_rect = label_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(label_shadow, (label_rect.x + 2, label_rect.y + 2))
        screen.blit(label_surface, label_rect)

        # Draw input box
        pygame.draw.rect(screen, box_color, input_box, 0, border_radius=5)
        pygame.draw.rect(screen, BLACK, input_box, 2, border_radius=5)

        # Draw input text
        txt_shadow = MENU_FONT.render(username, True, BLACK)
        txt_surface = MENU_FONT.render(username, True, WHITE)
        text_rect = txt_surface.get_rect(center=input_box.center)
        screen.blit(txt_shadow, (text_rect.x + 1, text_rect.y + 1))
        screen.blit(txt_surface, text_rect)

        # Draw button
        pygame.draw.rect(screen, box_color, button_box, 0, border_radius=5)
        pygame.draw.rect(screen, BLACK, button_box, 2, border_radius=5)

        # Draw button text
        button_text = MENU_FONT.render("Start", True, WHITE)
        button_shadow = MENU_FONT.render("Start", True, BLACK)
        button_rect = button_text.get_rect(center=button_box.center)
        screen.blit(button_shadow, (button_rect.x + 1, button_rect.y + 1))
        screen.blit(button_text, button_rect)

        # Draw game instructions
        instruction_text = "Press SPACE to flap wings and avoid obstacles!"
        instruction_shadow = pygame.font.SysFont('arial', 24).render(instruction_text, True, BLACK)
        instruction_surface = pygame.font.SysFont('arial', 24).render(instruction_text, True, WHITE)
        instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        screen.blit(instruction_shadow, (instruction_rect.x + 1, instruction_rect.y + 1))
        screen.blit(instruction_surface, instruction_rect)

        pygame.display.flip()
        clock.tick(30)


def main():
    """Main game function"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    username = username_screen(screen)

    while True:
        player = Player(230, 350)
        ground = Ground(730)
        obstacles = [Obstacle(SCREEN_WIDTH)]
        clouds = [Cloud() for _ in range(5)]
        score = 0
        clock = pygame.time.Clock()

        running = True
        game_over = False

        while running:
            clock.tick(60)  # 60 FPS for smoother gameplay

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not game_over:
                        player.flap()
                    if event.key == pygame.K_r and game_over:
                        game_over = False
                        player = Player(230, 350)
                        obstacles = [Obstacle(SCREEN_WIDTH)]
                        score = 0
                    if event.key == pygame.K_t and game_over:
                        return  # Return to username screen

            current_speed = calculate_speed(score)

            # Update game objects if game is not over
            if not game_over:
                player.move()
                ground.move(current_speed)

                # Update and manage clouds
                for cloud in clouds:
                    cloud.move()
                    if cloud.is_offscreen():
                        clouds.remove(cloud)
                        clouds.append(Cloud())

                # Manage obstacles
                add_obstacle = False
                obstacles_to_remove = []

                for obstacle in obstacles:
                    if obstacle.collide(player):
                        game_over = True

                    if not obstacle.passed and player.x > obstacle.x + obstacle.width:
                        obstacle.passed = True
                        add_obstacle = True

                    obstacle.move(current_speed)

                    if obstacle.x + obstacle.width < 0:
                        obstacles_to_remove.append(obstacle)

                # Add new obstacle if needed
                if add_obstacle:
                    score += 1
                    obstacles.append(Obstacle(SCREEN_WIDTH))

                # Remove offscreen obstacles
                for obstacle in obstacles_to_remove:
                    obstacles.remove(obstacle)

                # Check for ground collision
                if player.y + player.radius > ground.y or player.y - player.radius < 0:
                    game_over = True

            # Draw the game screen
            draw_game_screen(screen, player, obstacles, ground, score, clouds)

            # Show game over screen if game is over
            if game_over:
                # Semi-transparent overlay
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.fill(BLACK)
                overlay.set_alpha(128)
                screen.blit(overlay, (0, 0))

                # Game over text
                game_over_text = GAME_OVER_FONT.render("GAME OVER", 1, RED)
                screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                                             SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))

                # Restart instructions
                restart_text = MENU_FONT.render("Press R to restart", 1, WHITE)
                screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                                           SCREEN_HEIGHT // 2 + 50))

                # Switch player instructions
                switch_text = MENU_FONT.render("Press T to switch player", 1, WHITE)
                screen.blit(switch_text, (SCREEN_WIDTH // 2 - switch_text.get_width() // 2,
                                          SCREEN_HEIGHT // 2 + 100))

                # Show username and score
                final_score_text = MENU_FONT.render(f"Player: {username} - Score: {score}", 1, WHITE)
                screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2,
                                               SCREEN_HEIGHT // 2 + 150))

                pygame.display.update()


if __name__ == "__main__":
    # Create a data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Main game loop
    while True:
        main()