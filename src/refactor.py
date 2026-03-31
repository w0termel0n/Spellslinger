import pygame
import random

# Import pygame.locals for easier access to key coordinates
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

# ---------------
# CONSTANTS
# ---------------
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

# Define constant for drawing
BRUSH_SIZE = 10

# Define constant for framerate
FPS = 165

# ---------------
# CLASSES
# ---------------
# Define a Player object by extending pygame.sprite.Sprite
# The surface drawn on the screen is now an attribute of 'player'
class Player(pygame.sprite.Sprite):
    def __init__(self, icon, position):
        super(Player, self).__init__()
        self.image = pygame.image.load(icon).convert()
        self.image = pygame.transform.scale(self.image, (200, 250))
        self.image.set_colorkey(WHITE, RLEACCEL)
        
        self.rect = self.image.get_rect(topleft=position) 

# ---------------
# UI FUNCTIONS
# ---------------
def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def draw_value_bar(screen, color, current, max_value, x, y, length, height):
    current = clamp(current, 0, max_value)
    percentage = current / max_value

    pygame.draw.rect(screen, GRAY, (x, y, length, height))
    # Foreground, scaled by ratio
    if color == "mana":
        pygame.draw.rect(screen, BLUE, (x, y, int(length * percentage), height))
    elif color == "health":
        pygame.draw.rect(screen, RED, (x, y, int(length * percentage), height))
    # Border for clarity
    pygame.draw.rect(screen, BLACK, (x, y, length, height), 2)

# ---------------
# GAME FUNCTIONS
# ---------------
def init():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spellslinger")

    canvas = pygame.Surface((CANVAS_LENGTH, CANVAS_LENGTH))
    canvas.fill(WHITE)

    player = Player(
        "assets/Wizard-Left.png",
        ((SCREEN_WIDTH // 4) - 100, (SCREEN_HEIGHT - CANVAS_LENGTH) // 2 - 100),
    )

    sprites = pygame.sprite.Group(player)

    state = {
        "mana": 100,
        "health": 100,
        "spell_count": 0,
        "last_pos": None,
    }

    return screen, canvas, player, sprites, state


def handle_events(state, canvas):
    for event in pygame.event.get():
        if event.type == QUIT:
            return False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return False
            elif event.key == K_c:
                canvas.fill(WHITE)
            elif event.key == K_EQUALS:
                state["mana"] = clamp(state["mana"] + 10, 0, MAX_MANA)
            elif event.key == K_MINUS:
                state["mana"] = clamp(state["mana"] - 10, 0, MAX_MANA)

        elif event.type == MOUSEBUTTONUP and event.button == 1:
            save_canvas(canvas, state)

    return True


def handle_drawing(canvas, state):
    mx, my = pygame.mouse.get_pos()
    cx = mx - CANVAS_X
    cy = my - CANVAS_Y

    mouse_pressed = pygame.mouse.get_pressed()[0]

    if 0 <= cx < CANVAS_LENGTH and 0 <= cy < CANVAS_LENGTH:
        if mouse_pressed:
            if state["last_pos"]:
                pygame.draw.line(canvas, BLACK, state["last_pos"], (cx, cy), BRUSH_SIZE)

            pygame.draw.circle(canvas, BLACK, (cx, cy), BRUSH_SIZE // 2)
            state["last_pos"] = (cx, cy)
        else:
            state["last_pos"] = None
    else:
        state["last_pos"] = None


def save_canvas(canvas, state):
    scaled = pygame.transform.scale(canvas, (280, 280))
    pygame.image.save(scaled, f"drawings/spell_{state['spell_count']}.png")
    state["spell_count"] += 1
    canvas.fill(WHITE)


def draw(screen, canvas, player, sprites, state):
    screen.fill(BLACK)

    # Canvas
    screen.blit(canvas, (CANVAS_X, CANVAS_Y))

    # Player
    for entity in sprites:
        screen.blit(entity.image, entity.rect)

    # UI Bars
    draw_value_bar(
        screen,
        "mana",
        state["mana"],
        MAX_MANA,
        player.rect.x,
        player.rect.y + 250,
        200,
        20,
    )

    draw_value_bar(
        screen,
        "health",
        state["health"],
        MAX_HEALTH,
        player.rect.x,
        player.rect.y + 270,
        200,
        20
    )

    pygame.display.flip()

# ---------------
# MAIN GAME LOOP
# ---------------
def run():
    screen, canvas, player, sprites, state = init()
    clock = pygame.time.Clock()

    running = True
    while running:
        running = handle_events(state, canvas)
        handle_drawing(canvas, state)
        draw(screen, canvas, player, sprites, state)

        clock.tick(FPS)

    pygame.quit()

# ---------------
# ENTRY POINT
# ---------------
if __name__ == "__main__":
    run()