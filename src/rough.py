import pygame
import random

# Import pygame.locals for easier access to key coordinates
# Updated to conform to flake8 and black standards
from pygame.locals import (
    RLEACCEL,
    K_EQUALS,
    K_MINUS,
    K_c,
    K_ESCAPE,
    KEYDOWN,
    MOUSEBUTTONUP,
    QUIT,
)

# Initialize Pygame
pygame.init()

# Define constants for the screen width and height
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700

# Define constants for canvas width, height, and placement
CANVAS_LENGTH = 250
CANVAS_X = (SCREEN_WIDTH // 2) - (CANVAS_LENGTH // 2)
CANVAS_Y = (SCREEN_HEIGHT-CANVAS_LENGTH) - 10

# Define constants for player stats
MAX_MANA = 100
MAX_HEALTH = 100

# Define constants for colors
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (120,120,120)
BLUE = (0,0,255)
RED = (255,0,0)

# Define a Player object by extending pygame.sprite.Sprite
# The surface drawn on the screen is now an attribute of 'player'
class Player(pygame.sprite.Sprite):
    def __init__(self, icon):
        super(Player, self).__init__()
        self.image = pygame.image.load(icon).convert()
        self.image = pygame.transform.scale(self.image, (200, 250))
        self.image.set_colorkey(WHITE, RLEACCEL)
        self.rect = self.image.get_rect()

def draw_value_bar(color, current, max_value, x, y, length, height):
    if current > max_value:
        current = max_value
    elif current < 0:
        current = 0
    
    percentage = current / max_value

    pygame.draw.rect(screen, GRAY, (x, y, length, height))
    # Foreground, scaled by ratio
    if color == "mana":
        pygame.draw.rect(screen, BLUE, (x, y, length * percentage, height))
    elif color == "health":
        pygame.draw.rect(screen, RED, (x, y, length * percentage, height))
    # Border for clarity
    pygame.draw.rect(screen, BLACK, (x, y, length, height), 2)

# Set up game window
screen= pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spellslinger")

# Set up drawing canvas
canvas = pygame.Surface((CANVAS_LENGTH, CANVAS_LENGTH))
canvas.fill(WHITE)

# Setup the clock for a decent framerate
clock = pygame.time.Clock()

# Instantiate players
player1 = Player("assets/Wizard-Left.png")
player1.rect.x = (SCREEN_WIDTH // 4) - 100
player1.rect.y = ((SCREEN_HEIGHT - CANVAS_LENGTH) // 2 - 100)

# Create sprite group for rendering
all_sprites = pygame.sprite.Group()
all_sprites.add(player1)

current_mana = 100
current_health = 100

last_pos = None
drawing = False
brush_size = 10
spell_count = 0

# Main game loop
running = True
while running:

    # Fill the screen with black
    screen.fill(BLACK)
    
    # Add vanvas to screen
    screen.blit(canvas, (CANVAS_X, CANVAS_Y))

             # Look for every event in the queue
    for event in pygame.event.get():
        # Did the user hit a key?
        if event.type == KEYDOWN:
            # Was it the escape key? If so, stop the loop
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_c:
                canvas.fill(WHITE)
            elif event.key == K_EQUALS:
                if current_mana > MAX_MANA:
                    current_mana = 100
                else:
                    current_mana += 10
            elif event.key == K_MINUS:
                if current_mana < 0:
                    current_mana = 0
                else:
                    current_mana -= 10
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                scaled_img = pygame.transform.scale(canvas, (280, 280))
                pygame.image.save(scaled_img, f"drawings/spell_{spell_count}.png")
                spell_count += 1
                canvas.fill(WHITE)
        elif event.type == pygame.QUIT:
            running = False

        mx, my = pygame.mouse.get_pos()
        cx = mx - CANVAS_X
        cy = my - CANVAS_Y

        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Only draw inside canvas
        if 0 <= cx < CANVAS_LENGTH and 0 <= cy < CANVAS_LENGTH:

            if mouse_pressed:
                if last_pos is not None:
                    pygame.draw.line(canvas, BLACK, last_pos, (cx, cy), brush_size)

                pygame.draw.circle(canvas, BLACK, (cx, cy), brush_size // 2)

                last_pos = (cx, cy)
            else:
                last_pos = None
        else:
            last_pos = None

    # Draw all sprites
    for entity in all_sprites:
        screen.blit(entity.image, entity.rect)

    draw_value_bar("mana", current_mana, MAX_MANA, player1.rect.x, player1.rect.y + 250, 200, 20)
    draw_value_bar("health", current_health, MAX_HEALTH, player1.rect.x, player1.rect.y + 270, 200, 20)

    # Flip everything to the display
    pygame.display.flip()

    # Setup the clock for a decent framerate
    clock.tick(165)

# Close pygame
pygame.quit()