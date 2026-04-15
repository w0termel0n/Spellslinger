import pygame
import random
from spells import Spell
from spell_list import SPELL_LIST
import sys

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
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# Define constants for canvas width, height, and placement
CANVAS_LENGTH = 230
CANVAS_X = (CENTER_X) - 282
CANVAS_Y = (SCREEN_HEIGHT-CANVAS_LENGTH) - 30

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
class Entity(pygame.sprite.Sprite):
    def __init__(self, icon, position, max_health=100, max_mana=100):
        super().__init__()
        self.image = pygame.image.load(icon).convert()
        self.image = pygame.transform.scale(self.image, (200, 250))

        self.rect = self.image.get_rect(topleft=position)

        # Core stats
        self.max_health = max_health
        self.health = max_health

        self.max_mana = max_mana
        self.mana = max_mana

        self.last_mana_regen = pygame.time.get_ticks()

        self.effects = {}

    def take_damage(self, amount):
        self.health = clamp(self.health - amount, 0, self.max_health)

    def spend_mana(self, amount):
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False
    
    def __str__(self):
        return "Entity"
    
class Player(Entity):
    def __init__(self, icon, position):
        super().__init__(icon, position)


class Enemy(Entity):
    def __init__(self, icon, position):
        super().__init__(icon, position)

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

def start_menu():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spellslinger")

    pygame.font.init()
    font = pygame.font.SysFont("caveatregular", 30)
    title_font = pygame.font.SysFont("caveatregular", 80)

    running = True
    while running:

        screen.fill((60,25,60))
        mouse = pygame.mouse.get_pos()

        play_button = pygame.Rect(CENTER_X - 90, CENTER_Y - 50 // 2 - 20, 140, 50)
        quit_button = pygame.Rect(CENTER_X - 90, CENTER_Y - 50 // 2 + 60, 140, 50)

        pygame.draw.rect(screen, (170,170,170) if play_button.collidepoint(mouse) else (100,100,100), play_button)
        pygame.draw.rect(screen, (170,170,170) if quit_button.collidepoint(mouse) else (100,100,100), quit_button)

        title_text = title_font.render("Spellslinger", True, WHITE)
        play_text = font.render("Play", True, WHITE)
        quit_text = font.render("Quit", True, WHITE)

        screen.blit(title_text, (CENTER_X - 185, 100))
        screen.blit(play_text, (CENTER_X - 45, CENTER_Y - 50 // 2 - 15))
        screen.blit(quit_text, (CENTER_X - 45, CENTER_Y - 50 // 2 + 65))

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(mouse):
                    run()
                    return
                if quit_button.collidepoint(mouse):
                    running = False

        pygame.display.update()
    
    pygame.quit()
    sys.exit()

# ---------------
# GAME FUNCTIONS
# ---------------
def init():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spellslinger")

    spellbook = pygame.image.load("assets/Spellbook.png")
    spellbook = pygame.transform.scale(spellbook, (1250, 750))

    canvas = pygame.Surface((CANVAS_LENGTH, CANVAS_LENGTH))
    canvas.fill(WHITE)

    player = Player(
        "assets/Wizard-Left.png",
        ((SCREEN_WIDTH // 4) - 100, (SCREEN_HEIGHT - CANVAS_LENGTH) // 2 - 100),
    )

    enemy = Enemy(
        "assets/Wizard-Right.png",
        ((3 * SCREEN_WIDTH // 4) - 100, (SCREEN_HEIGHT - CANVAS_LENGTH) // 2 - 100),
    )

    sprites = pygame.sprite.Group(player, enemy)

    state = {
        "spell_count": 0,
        "last_pos": None,
    }

    return screen, canvas, player, sprites, state, enemy, spellbook


def handle_events(state, canvas, player, enemy):
    for event in pygame.event.get():
        if event.type == QUIT:
            return False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return False
            elif event.key == K_c:
                canvas.fill(WHITE)
            elif event.key == K_EQUALS:
                player.mana = clamp(player.mana + 10, 0, player.max_mana)
            elif event.key == K_MINUS:
                player.mana = clamp(player.mana - 10, 0, player.max_mana)

        elif event.type == MOUSEBUTTONUP and event.button == 1:
            mx, my = event.pos  # mouse position at release
            # Check if inside canvas bounds
            if (CANVAS_X <= mx < CANVAS_X + CANVAS_LENGTH and
                CANVAS_Y <= my < CANVAS_Y + CANVAS_LENGTH):
                
                save_canvas(canvas, state, player, enemy)

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


def save_canvas(canvas, state, player, enemy):
    scaled = pygame.transform.scale(canvas, (280, 280))
    pygame.image.save(scaled, f"drawings/spell_{state['spell_count']}.png")
    state["spell_count"] += 1

    spell_name = recognize_spell()
    cast_spell(spell_name, player, enemy)

    canvas.fill(WHITE)


def draw(screen, canvas, player, sprites, enemy, spellbook):
    # Draw Background
    screen.fill(BLACK)

     # Draw Spellbook
    screen.blit(spellbook, (CENTER_X - 590, SCREEN_HEIGHT - 525))

    # Draw Canvas
    screen.blit(canvas, (CANVAS_X, CANVAS_Y))

    # Draw Player
    for entity in sprites:
        screen.blit(entity.image, entity.rect)

    # Draw Player Mana
    draw_value_bar(
        screen,
        "mana",
        player.mana,
        MAX_MANA,
        CENTER_X + 57,
        SCREEN_HEIGHT - 130,
        250,
        20,
    )

    # Draw Player Health
    draw_value_bar(
        screen,
        "health",
        player.health,
        MAX_HEALTH,
        CENTER_X + 57,
        SCREEN_HEIGHT - 110,
        250,
        20
    )

    # Draw Enemy Mana
    draw_value_bar(
        screen,
        "mana",
        enemy.mana,
        MAX_MANA,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 22,
        200,
        20
    )

    # Draw Enemy Health
    draw_value_bar(
        screen,
        "health",
        enemy.health,
        MAX_HEALTH,
        SCREEN_WIDTH - 400,
        enemy.rect.y,
        200,
        20
    )

    pygame.display.flip()

def cast_spell(spell_name, caster, target):
    spell_name = "fireball"
    spell = Spell.from_name(spell_name, SPELL_LIST)

    # Check mana (also spends it)
    if not caster.spend_mana(spell.mana_cost):
        print("Not enough mana!")
        return

    # Deal damage
    target.take_damage(spell.dmg)

    # Apply effects
    for effect, value in spell.effects.items():
        target.effects[effect] = target.effects.get(effect, 0) + value

    print(f"{caster} cast {spell_name}!")
    print(f"{spell_name} damage:", spell.dmg)

def recognize_spell():
    # TEMP: replace later with drawing recognition
    return random.choice(list(SPELL_LIST.keys()))

def regen_mana(player):
    current_time = pygame.time.get_ticks()

    # 2000 ms = 2 seconds
    if current_time - player.last_mana_regen >= 2000:
        player.mana = clamp(player.mana + 5, 0, player.max_mana)
        player.last_mana_regen = current_time


# ---------------
# MAIN GAME LOOP
# ---------------
def run():
    screen, canvas, player, sprites, state, enemy, spellbook = init()
    clock = pygame.time.Clock()

    running = True
    while running:
        running = handle_events(state, canvas, player, enemy)
        
        handle_drawing(canvas, state)

        regen_mana(player)

        draw(screen, canvas, player, sprites, enemy, spellbook)

        clock.tick(FPS)

    pygame.quit()

# ---------------
# ENTRY POINT
# ---------------
if __name__ == "__main__":
    run()
    #start_menu()