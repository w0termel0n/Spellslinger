import pygame
import random
from spells import Spell
from spell_list import SPELL_LIST
import sys
from effects import EFFECTS

# Import pygame.locals for easier access to key coordinates
from pygame.locals import (
    K_EQUALS,
    K_MINUS,
    K_ESCAPE,
    K_c,
    KEYDOWN,
    MOUSEBUTTONUP,
    QUIT,
    K_BACKQUOTE,
    K_1,
    K_2,
    K_3,
    K_4,
    K_5,
    K_6,
    K_7,
    K_8,
    K_9,
    K_0,
    K_BACKSPACE,
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
MAX_HEALTH = 200

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

# Create dictionary for image cache
IMAGE_CACHE = {}

def get_image(path, size=(88, 66)):
    """
    Retrieves the image of a spell projectile

    Args:
        path (string) - path of image location
        size (tuple[int, int]) - width and height of image

    Returns:
        IMAGE_CACHE[key] (pygame.Surface) - cache and scaled image
    """
    # Set key for the dictionary
    key = (path, size)

    # Check if image is already in cache
    if key not in IMAGE_CACHE:
        # Load the image as a pygame image
        img = pygame.image.load(path).convert_alpha()
        # Scale the image to the correct size
        img = pygame.transform.scale(img, size)
        # Store the image in the cache
        IMAGE_CACHE[key] = img

    # Return the image
    return IMAGE_CACHE[key]

# Define list of effect icons
EFFECT_ICONS = {
    "blitz": "assets/effects/blitz.png",
    "burning": "assets/effects/burning.png",
    "curse": "assets/effects/curse_pixel.png",
    "freezing": "assets/effects/freezing.png",
    "glaciate": "assets/effects/glaciate.png",
    "kindling": "assets/effects/kindling.png",
    "shield": "assets/effects/shield.png",
    "blind": "assets/effects/blind.png",
    "leech": "assets/effects/leech.png",
}

# Define buffs & debuffs for effect icons
BUFFS = {"blitz", "glaciate", "kindling", "shield"}
DEBUFFS = {"blind", "burning", "freezing", "curse"}

# Create dictionary for icon cache
ICON_CACHE = {}

def get_icon(path, size=(40, 40)):
    """
    Retrieves the path of an effect icon

    Args:
        path (string) - path of icon location
        size (tuple[int, int])- width and height of icon    
    
    Returns:
        ICON_CACHE[key] (pygame.Surface) - cache and scaled image of effect icon
    """
    # Check if icon is already in cache 
    if path not in ICON_CACHE:
        # Load the icon as pygame image
        img = pygame.image.load(path).convert_alpha()
        # Resize the icon
        img = pygame.transform.scale(img, size)
        # Store the icon into cahce
        ICON_CACHE[path] = img

    # Return the icon
    return ICON_CACHE[path]

# Define spell abbreviations for effects
SPELL_ABBREVIATIONS = {
    "blindness": "BL",
    "blitz": "BZ",
    "counterspell": "CS",
    "curse": "CR",
    "fireball": "FB",
    "frostbite": "FR",
    "glaciate": "GL",
    "kindling": "KD",
    "leech": "LE",
    "roulette": "RL",
    "shield": "SH",
    "spike": "SP",
}


# ---------------
# CLASSES
# ---------------
class Entity(pygame.sprite.Sprite):
    """
    Base class for game entities (players, enemies)

    Provides tracking for sprite, health, mana, and active effects

    Attributes:
        image (pygame.Surface) - sprite image
        rect (pygame.Rect) - surface containing sprite
        max_health (int) - maximum possible health
        health (int) - current health
        max_mana (int) - maximum possible mana
        mana (int) - current mana
        last_mana_regen (int) - timestamp of most recent mana value
        effects (dictionary) - active effects

    Methods:
        __init__() - initiales an Entity
        spend_mana() - determine if Entity has enough mana for a spell
        __str__() - return type of Class
    """
    def __init__(self, icon, position, max_health=MAX_HEALTH, max_mana=MAX_MANA):
        """
        Initializes an Entity

        Args:
            icon (str) - path to sprite image 
            position (tuple[int, int]) - x, y position of sprite 
            max_health (int) - maximum possible health
            max_mana (int) - maximum possible mana
        """
        super().__init__()
        # Entity icon
        self.image = pygame.image.load(icon).convert()
        self.image = pygame.transform.scale(self.image, (200, 250))

        # Surface to display icon
        self.rect = self.image.get_rect(topleft=position)

        # Entity health
        self.max_health = max_health
        self.health = max_health

        # Entity mana
        self.max_mana = max_mana
        self.mana = max_mana

        # Entity mana regen
        self.last_mana_regen = pygame.time.get_ticks()

        # Entity effects
        self.effects = {}

    def spend_mana(self, amount):
        """
        Determines if mana can be spent on spell

        Args:
            amount (int) - mana cost of spell

        Returns:
            bool - True if enough mana to cast, else False
        """
        # Check if current mana exceeds cost of spell
        if self.mana >= amount:
            # If greater, decrease mana by cost
            self.mana -= amount
            return True
        # If less, return False
        return False
    
    def __str__(self):
        return "Entity"
    
class Player(Entity):
    """
    Subclass of Entity

    Methods:
        __init__() - initializes a Player
    """
    def __init__(self, icon, position):
        """
        Initializes a Player

        Args:
            icon (str) - path to sprite image 
            position (tuple[int, int]) - x, y position of sprite 
        """
        super().__init__(icon, position)


class Enemy(Entity):
    """
    Subclass of Entity

    Methods:
        __init__() - initializes an Enemy
    """

    def __init__(self, icon, position):
        """
        Initializes an Enemy

        Args:
            icon (str) - path to sprite image 
            position (tuple[int, int]) - x, y position of sprite 
        """
        super().__init__(icon, position)


class Projectile:
    """
    Class for spell projectiles

    Provides ability to track and draw projectiles of spells

    Attributes:
        caster (Entity) - entity who cast the spell
        target (Entity) - entity who will have spell applied to
        spell (Spell) - spell being cast
        duration (int) - flight time of spell

    Methods:
        __init__() - initiales a Projectile
        update() - tracks the position of the projectile
        projectile_draw() - draw the projectile in flight
    """
    def __init__(self, caster, target, spell, duration=2.0):
        """
        Initializes a Projectile

        Args:
            caster (Entity) - entity who cast the spell
            target (Entity) - entity who will have spell applied to
            spell (Spell) - spell being cast
            duration (int) - flight time of spell
        """
        # Properties of spell casted
        self.caster = caster
        self.target = target
        self.spell = spell

        # Image of projectile
        if spell.projectile_img:
            img = get_image(spell.projectile_img)

            # Flip if enemy is casting
            if isinstance(caster, Enemy):
                img = pygame.transform.flip(img, True, False)

            self.image = img
        else:
            self.image = None

        # Start and end of projectile travel
        if isinstance(caster, Enemy):
            # Enemy shoots right to left
            self.start_pos = caster.rect.midleft
            self.end_pos = target.rect.midright
        else:
            # Player shoots left to right
            self.start_pos = caster.rect.midright
            self.end_pos = target.rect.midleft

        # Maximum time in air
        self.duration = duration
        # Time spent in air
        self.elapsed = 0

        # Positions of the projectile
        self.position = list(self.start_pos)

    def update(self, dt):
        """
        Tracks the position of a Projectile

        Args:
            dt (int) - time spent in flight

        Returns:
            bool - True if it's reached target, else False
        """
        # Increment time in flight
        self.elapsed += dt

        # Determing progress of flight
        t = min(self.elapsed / self.duration, 1)

        # Determine position in air from progress of flight
        self.position[0] = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        self.position[1] = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t

        return t >= 1  # True when it reaches target

    def projectile_draw(self, screen):
        """
        Draws a Projectile in flight

        Args:
            screen (pygame.display) - screen to be drawn on
        """
        # Check if projectile has an image
        if self.image:
            # Draw the image on rect
            rect = self.image.get_rect(center=(int(self.position[0]), int(self.position[1])))
            #Display the image
            screen.blit(self.image, rect)

# ---------------
# UI FUNCTIONS
# ---------------
def clamp(value, min_val, max_val):
    """
    Set boundaries for a value

    Helper function for draw_value_bar

    Args:
        value (int) - value to be clamped
        min_val (int) - minimum possible value
        max_val (int) - maximum possible value

    Returns:
        If the value is less than the minimum, return the minimum
        If the value is greater than the maximum, return the maximum
        Else, return the value
    """
    return max(min_val, min(value, max_val))

def draw_value_bar(screen, color, current, max_value, x, y, length, height):
    """
    Draws a visible bar to track health and mana

    Args:
        screen (pygame.display) - screen to be drawn on
        color (string) - "mana" for BLUE or "health" for RED
        current (int) - current value of health or mana
        max_value (int) - maximum possible health or mana
        x (int) - x position of bar
        y (int) - y position of bar
        length (int) - length of bar
        height (int) - height of bar
    """
    # Ensure current value does not exceed max
    current = clamp(current, 0, max_value)
    # Calculate the percentage of value
    percentage = current / max_value

    # Draw background of bar
    pygame.draw.rect(screen, GRAY, (x, y, length, height))
    # Draw the value bar
    # Make value var red
    if color == "mana":
        pygame.draw.rect(screen, BLUE, (x, y, int(length * percentage), height))
    # Make value bar blue
    elif color == "health":
        pygame.draw.rect(screen, RED, (x, y, int(length * percentage), height))
    # Outline value bar
    pygame.draw.rect(screen, BLACK, (x, y, length, height), 2)

def start_menu():
    """
    Draws the starting screen of the game
    """
    # Initialize pygame
    pygame.init()
    # Create window for game
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Title the window
    pygame.display.set_caption("Spellslinger")

    # Initialize fonts
    pygame.font.init()
    # Store font for regular buttons
    font = pygame.font.SysFont("caveatregular", 30)
    # Store font for title
    title_font = pygame.font.SysFont("caveatregular", 80)

    # Run until interrupted
    running = True
    while running:
        # Make background purple
        screen.fill((60,25,60))
        # Determine position of mouse cursor
        mouse = pygame.mouse.get_pos()

        # Create menu buttons
        play_button = pygame.Rect(CENTER_X - 90, CENTER_Y - 50 // 2 - 20, 140, 50)
        quit_button = pygame.Rect(CENTER_X - 90, CENTER_Y - 50 // 2 + 60, 140, 50)

        # Change menu button color on click
        pygame.draw.rect(screen, (170,170,170) if play_button.collidepoint(mouse) else (100,100,100), play_button)
        pygame.draw.rect(screen, (170,170,170) if quit_button.collidepoint(mouse) else (100,100,100), quit_button)

        # Instantiate text
        title_text = title_font.render("Spellslinger", True, WHITE)
        play_text = font.render("Play", True, WHITE)
        quit_text = font.render("Quit", True, WHITE)

        # Display Text
        screen.blit(title_text, (CENTER_X - 185, 100))
        screen.blit(play_text, (CENTER_X - 45, CENTER_Y - 50 // 2 - 15))
        screen.blit(quit_text, (CENTER_X - 45, CENTER_Y - 50 // 2 + 65))

        # Watch for menu click
        for event in pygame.event.get():
            # Check for X button
            if event.type == pygame.QUIT:
                # Interupt the loop
                running = False
            # Check for menu button press
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check for play button
                if play_button.collidepoint(mouse):
                    # Play the game
                    run()
                    return
                # Check for quit button
                if quit_button.collidepoint(mouse):
                    # Interupt the loop
                    running = False

        # Update display on action
        pygame.display.update()
    
    # Quit the game
    pygame.quit()
    # Close the program
    sys.exit()

def game_over_screen(screen, winner, state):
    pygame.font.init()
    title_font = pygame.font.SysFont("caveatregular", 80)
    button_font = pygame.font.SysFont("caveatregular", 40)

    running = True
    while running:
        screen.fill((30, 0, 0))

        mouse = pygame.mouse.get_pos()

        # Buttons
        retry_button = pygame.Rect(CENTER_X - 100, CENTER_Y + 40, 200, 60)
        quit_button = pygame.Rect(CENTER_X - 100, CENTER_Y + 120, 200, 60)

        # Hover effect
        pygame.draw.rect(screen, (170,170,170) if retry_button.collidepoint(mouse) else (100,100,100), retry_button)
        pygame.draw.rect(screen, (170,170,170) if quit_button.collidepoint(mouse) else (100,100,100), quit_button)

        # Text
        result_text = title_font.render(f"{winner} Wins!", True, WHITE)
        retry_text = button_font.render("Retry", True, WHITE)
        quit_text = button_font.render("Quit", True, WHITE)

        score_font = pygame.font.SysFont("caveatregular", 40)
        score_text = score_font.render(f"Final Score: {int(state['score'])}", True, WHITE)
        screen.blit(score_text, (CENTER_X - 110, CENTER_Y - 10))

        # Draw text
        screen.blit(result_text, (CENTER_X - 180, CENTER_Y - 100))
        screen.blit(retry_text, (CENTER_X - 45, CENTER_Y + 40))
        screen.blit(quit_text, (CENTER_X - 35, CENTER_Y + 120))

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_button.collidepoint(mouse):
                    run()   # restart game
                    return
                if quit_button.collidepoint(mouse):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

def abbreviate_spell(name):
    """
    Abbreviates the name of a spell

    Helper function to draw_effect_row

    Args:
        name (string) - name of spell to be abbreviated
    
    Returns:
        First 3 letters of the spell, all capitalized
    """
    return SPELL_ABBREVIATIONS.get(name, name[:3].upper())

def draw_effect_row(screen, entity, effects, x, y, direction="up"):
    """
    Draws icons for spell effects in a row

    Args:
        screen (pygame.display) - screen to be drawn on
        entity (Entity) - entity affected by spell
        effects (dictionary) - list of effect name and properties
        x (int) - x position of effect icon
        y (int) - y position of effect icon
        direction (str) - determines above or below value bars
    """
    # Spacing between icons
    spacing = 36
    # Run for every possible effect
    for i, effect in enumerate(effects):
        # Check for effect
        if effect not in EFFECT_ICONS:
            continue

        # Retrieve effect icon
        icon = get_icon(EFFECT_ICONS[effect])

        # Check if icon drawn above or below bars
        if direction == "up":
            # Draw above the bars
            pos_y = y - spacing
        else:
            # Draw below the bars
            pos_y = y + spacing

         # Check if curse is active
        if effect == "curse":
            # Store blocked spell
            blocked = entity.effects["curse"].get("blocked_spell", "")
            # Store name of blocked spell
            label_text = abbreviate_spell(blocked)

            # Store font for text
            font = pygame.font.SysFont("caveatregular", 30)
            # Store text of blocked spell
            label = font.render(label_text, True, GRAY)

            # Initialize text
            icon_x = x + i * spacing

            text_rect = label.get_rect(center=(icon_x + 20, y + 55))
            screen.blit(label, text_rect)

        # Draw effect icon
        screen.blit(icon, (x + i * spacing, pos_y))


# ---------------
# GAME FUNCTIONS
# ---------------
def init():
    """
    Initialzes the window for the game

    Returns:
        screen (pygame.display) - window the game will play in
        canvas (pygame.Surface) - drawable surface for spell runes
        player (Entity) - instance of the player
        sprites (pygame.sprite) - icons of player and enemy
        state (dictionary) - tracks # of spells and mouse position for canvas
        enemy (Entity) - instance of the enemy
        spellbook (pygame.image) - image of spellbook for UI
        projectiles (array) - array of active Projectiles
    """
    # Initialize pygame
    pygame.init()
    # Create window for game
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Title game window
    pygame.display.set_caption("Spellslinger")

    # Load image of spellbook for UI
    spellbook = pygame.image.load("assets/Spellbook.png")
    # Create image of spellbook
    spellbook = pygame.transform.scale(spellbook, (1250, 750))

    # Initialize canvas for drawing
    canvas = pygame.Surface((CANVAS_LENGTH, CANVAS_LENGTH))
    # Make canvas white
    canvas.fill(WHITE)

    # Initialize player sprite
    player = Player(
        "assets/Wizard-Left.png",
        ((SCREEN_WIDTH // 4) - 100, (SCREEN_HEIGHT - CANVAS_LENGTH) // 2 - 100),
    )

    # Initialize enemy sprite
    enemy = Enemy(
        "assets/Wizard-Right.png",
        ((3 * SCREEN_WIDTH // 4) - 100, (SCREEN_HEIGHT - CANVAS_LENGTH) // 2 - 100),
    )

    # Store sprites as pygame sprite group
    sprites = pygame.sprite.Group(player, enemy)

    # Store # of spells casted and position of mouse cursor
    state = {
        "spell_count": 0,
        "last_pos": None,
        "score": 0
    }

    # Initialize array of Projectiles
    projectiles = []

    # Return all needed variables
    return screen, canvas, player, sprites, state, enemy, spellbook, projectiles


def handle_events(state, canvas, player, enemy, projectiles):
    """
    Handles action events for the program

    Args:
        state (dictionary) - tracks # of spells and mouse position for canvas
        canvas (pygame.Surface) - drawable surface for spell runes
        player (Entity) - instance of the player
        enemy (Entity) - instance of the enemy
        projectiles (array) - array of active Projectiles

    Returns:
        bool - True until interuppted
    """
    for event in pygame.event.get():
        if event.type == QUIT:
            return False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return False
            elif event.key == K_c:
                canvas.fill(WHITE)
            # Check for number keys (1-9) to cast corresponding spells
            elif event.key == K_BACKQUOTE:
                cast_spell("blindness", player, enemy, projectiles, state)
            elif event.key == K_1:
                cast_spell("blitz", player, enemy, projectiles, state)
            elif event.key == K_2:
                cast_spell("counterspell", player, enemy, projectiles, state)
            elif event.key == K_3:
                cast_spell("curse", player, enemy, projectiles)
            elif event.key == K_4:
                cast_spell("fireball", player, enemy, projectiles, state)
            elif event.key == K_5:
                cast_spell("frostbite", player, enemy, projectiles, state)
            elif event.key == K_6:
                cast_spell("glaciate", player, enemy, projectiles, state)
            elif event.key == K_7:
                cast_spell("kindling", player, enemy, projectiles, state)
            elif event.key == K_8:
                cast_spell("leech", player, enemy, projectiles, state)
            elif event.key == K_9:
                cast_spell("roulette", player, enemy, projectiles, state)
            elif event.key == K_0:
                cast_spell("shield", player, enemy, projectiles, state)
            elif event.key == K_MINUS:
                cast_spell("spike", player, enemy, projectiles, state)
            elif event.key == K_EQUALS:
                cast_spell("shield", player, enemy, projectiles, state)
            elif event.key == K_BACKSPACE:
                player.health = clamp(player.health / 2, 0, player.max_health)

        elif event.type == MOUSEBUTTONUP and event.button == 1:
            mx, my = event.pos  # mouse position at release
            # Check if inside canvas bounds
            if (CANVAS_X <= mx < CANVAS_X + CANVAS_LENGTH and
                CANVAS_Y <= my < CANVAS_Y + CANVAS_LENGTH):
                
                save_canvas(canvas, state, player, enemy, projectiles)

    return True


def handle_drawing(canvas, state):
    """
    Handles drawing on the canvas

    Args:
        canvas (pygame.Surface) - drawable surface for spell runes
        state (dictionary) - tracks # of spells and mouse position for canvas
    """
    # Store position of mouse cursor
    mx, my = pygame.mouse.get_pos()
    # Store x and y of canvas
    cx = mx - CANVAS_X
    cy = my - CANVAS_Y

    # Detect when mouse is pressed down
    mouse_pressed = pygame.mouse.get_pressed()[0]

    # Only draw within bounds of canvas
    if 0 <= cx < CANVAS_LENGTH and 0 <= cy < CANVAS_LENGTH:
        if mouse_pressed:
            if state["last_pos"]:
                # Draw a line between previous and current mouse position
                pygame.draw.line(canvas, BLACK, state["last_pos"], (cx, cy), BRUSH_SIZE)

            # Draw a dot on current mouse position
            pygame.draw.circle(canvas, BLACK, (cx, cy), BRUSH_SIZE // 2)
            state["last_pos"] = (cx, cy)
        else:
            state["last_pos"] = None
    else:
        state["last_pos"] = None


def save_canvas(canvas, state, player, enemy, projectiles):
    """
    Saves drawing on the canvas before reseting the canvas to blank

    Args:
        canvas (pygame.Surface) - drawable surface for spell runes
        state (dictionary) - tracks # of spells and mouse position for canvas
        player (Entity) - instance of the player
        enemy (Entity) - instance of the enemy
        projectiles (array) - array of active Projectiles
    """
    # Set image size
    scaled = pygame.transform.scale(canvas, (280, 280))
    # Store canvas as image
    pygame.image.save(scaled, f"drawings/spell_{state['spell_count']}.png")
    state["spell_count"] += 1

    # Store name of spell cast
    spell_name = recognize_spell()
    # Cast the given spell
    cast_spell(spell_name, player, enemy, projectiles, state)

    # Reset canvas to white
    canvas.fill(WHITE)

def draw_player_canvas(screen, canvas, entity):
    """
    Draws the player's canvas on the screen

    Args:
        screen (pygame.display) - window the game will play in
        canvas (pygame.Surface) - drawable surface for spell runes
        entity (Entity) - entity who will see the canvas
    """
    # Check for blind effect
    if "blind" in entity.effects:
        # Store canvas
        black = pygame.Surface((CANVAS_LENGTH, CANVAS_LENGTH))
        # Make canvas black
        black.fill(BLACK)
        # Draw black canvas
        screen.blit(black, (CANVAS_X, CANVAS_Y))
    else:
        # Draw canvas as normal
        screen.blit(canvas, (CANVAS_X, CANVAS_Y))

def draw(screen, canvas, player, sprites, enemy, spellbook, projectiles, state):
    """
    Draws the entire UI for the game

    Args:
        screen (pygame.display) - window the game will play in
        canvas (pygame.Surface) - drawable surface for spell runes
        player (Entity) - instance of the player
        sprites (pygame.sprite) - icons of player and enemy
        enemy (Entity) - instance of the enemy
        spellbook (pygame.image) - image of spellbook for UI
        projectiles (array) - array of active Projectiles
    """
    # Draw background
    screen.fill(BLACK)

    # Draw spellbook
    screen.blit(spellbook, (CENTER_X - 590, SCREEN_HEIGHT - 525))

    # Draw canvas
    draw_player_canvas(screen, canvas, player)

    # Draw entity sprites
    for entity in sprites:
        screen.blit(entity.image, entity.rect)

    # Draw Player mana bar
    draw_value_bar(
        screen,
        "mana",
        player.mana,
        MAX_MANA,
        CENTER_X + 57,
        SCREEN_HEIGHT - 160,
        250,
        20,
    )

    # Draw Player health bar
    draw_value_bar(
        screen,
        "health",
        player.health,
        MAX_HEALTH,
        CENTER_X + 57,
        SCREEN_HEIGHT - 140,
        250,
        20
    )

    # Store Player effects as buffs and debuffs
    player_buffs = [e for e in player.effects if e in BUFFS]
    player_debuffs = [e for e in player.effects if e in DEBUFFS]

    # Draw buffs ABOVE mana bar
    draw_effect_row(
        screen,
        player,
        player_buffs,
        CENTER_X + 57,
        SCREEN_HEIGHT - 160,
        direction="up"
    )

    # Draw debuffs BELOW health bar
    draw_effect_row(
        screen,
        player,
        player_debuffs,
        CENTER_X + 57,
        SCREEN_HEIGHT - 160,
        direction="down"
    )

    # Draw Enemy mana bar
    draw_value_bar(
        screen,
        "mana",
        enemy.mana,
        MAX_MANA,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 44,
        200,
        20
    )

    # Draw Enemy health bar
    draw_value_bar(
        screen,
        "health",
        enemy.health,
        MAX_HEALTH,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 22,
        200,
        20
    )

    # Store Enemy effects as buffs and debuffs
    enemy_buffs = [e for e in enemy.effects if e in BUFFS]
    enemy_debuffs = [e for e in enemy.effects if e in DEBUFFS]

    # Draw buffs ABOVE mana bar
    draw_effect_row(
        screen,
        enemy,
        enemy_buffs,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 44,
        direction="up"
    )

    # Draw debuffs BELOW health bar
    draw_effect_row(
        screen,
        enemy,
        enemy_debuffs,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 44,
        direction="down"
    )
    
    # Draw projectiles
    for projectile in projectiles:
        projectile.projectile_draw(screen)

    # Draw score
    font = pygame.font.SysFont("caveatregular", 30)
    score_text = font.render(f"Score: {int(state['score'])}", True, WHITE)
    screen.blit(score_text, (20, 20))

    # Check for game over
    if player.health <= 0 or enemy.health <= 0:
        winner = "Enemy" if player.health <= 0 else "Player"
        game_over_screen(screen, winner, state)
        return

    # Update display
    pygame.display.flip()

def recognize_spell():
    """
    Takes the rune drawn on canvas an inputs it into the CNN to be identified

    Args:
        canvas (pygame.Surface) - surface containing the rune to be identified

    Returns:
        spell_name (string) - name of the spell identified from rune
    """
    # TEMP: replace later with drawing recognition
    return random.choice(list(SPELL_LIST.keys()))

def deal_damage(caster, target, base_damage, state):
    """
    Calculates the damage of the spell and applies it to the target

    Args:
        caster (Entity) - entity who cast the spell
        target (Entity) - entity affected by the spell
        base_damage (int) - unmodified damage value of the spell cast

    Returns:
        damage (int) - modified damage value of the spell
    """
    # Store damage of spell
    damage = base_damage

    # Check for defensive effects
    if "shield" in target.effects:
        shield = target.effects["shield"]

        # Check for instance shield
        if shield.get("uses", 0) > 0:
            # Half damage of spell
            damage *= 0.5
            # Remove instance of shield
            shield["uses"] -= 1

            # Remove shield from effects
            if shield["uses"] <= 0:
                del target.effects["shield"]

    # Apply damage to target
    target.health = clamp(target.health - damage, 0, target.max_health)

    # Update score
    if caster != target:
        if isinstance(caster, Player):
            state["score"] += damage   # damage dealt
        if isinstance(target, Player):
            state["score"] -= damage   # damage taken

    # Return modified damage value
    return damage

def cast_spell(spell_name, caster, target, projectiles, state):
    """
    Determines if a spell can be cast before casting it if able

    Args:
        spell_name (string) - name of spell to be cast
        caster (Entity) - entity who cast the spell
        target (Entity) - entity to be affected by the spell
        projectiles (array) - array of active Projectiles
    """
    # Store spell cast
    spell = Spell.from_name(spell_name, SPELL_LIST)

    # Check for curse effect
    if "curse" in caster.effects:
        # Store name of blocked spell
        blocked = caster.effects["curse"].get("blocked_spell")

        # Check if spell is blocked
        if blocked == spell_name:
        # Prevent casting of blocked spell
            print(f"{spell_name} is blocked by curse!")
            return
    
    # Check for enough mana
    if not caster.spend_mana(spell.mana_cost):
        # Prevent casting of spell
        print("Not enough mana!")
        return
    
    # Check for counterspell
    if spell_name == "counterspell":
        # Find projectile targeting caster
        for proj in projectiles:
            # Check for target
            if proj.target == caster:
                # Remove the spell in the air
                projectiles.remove(proj)
                print("Projectile countered!")
                return

        print("No projectile to counter!")
        return

    # Check for type of spell
    if spell.delivery == "projectile":
        # Add spell to projectiles
        projectiles.append(Projectile(caster, target, spell))
        print(f"{caster} cast {spell_name}! (projectile launched)")
    else:
        # Resolve spell as Instant
        resolve_spell_direct(spell, caster, target, state)
        print(f"{caster} cast {spell_name}! (instant)")
        

def resolve_spell_direct(spell, caster, target, state):
    """
    Applies the effects of an Instant spell

    Args:
        spell (Spell) - spell that was cast
        caster (Entity) - entity who cast the spell
        target (Entity) - entity to be affected by the spell
    """
    # Deal damage of spell
    deal_damage(caster, target, spell.dmg, state)

    # Search for spell effect
    for effect, chance in spell.effects.items():
        # Store chance of application
        total_chance = min(chance, 1.0)

        # Determine if effect gets applied
        if random.random() < total_chance:
            if effect in EFFECTS:
                # Apply effect to target
                EFFECTS[effect](caster, target)
    
    print(f"{caster} casts {spell}!")
    print(f"{spell} damage:", spell.dmg)
    print(f"Player effects: ", caster.effects)
    print(f"Target effects: ", target.effects)
    

def resolve_spell(projectile, state):
    """
    Resolves the effects of a spell after its projectile collides with its target

    Args:
        projectile (array) - array of active Projectiles
    """
    # Store properties of Projectile
    caster = projectile.caster
    target = projectile.target
    spell = projectile.spell

    # Store damage of spell
    damage_dealt = deal_damage(caster, target, spell.dmg, state)

    # Check if cast spell was Leech
    if spell.leech:
        # Add damage dealt to caster health
        caster.health = clamp(
            caster.health + damage_dealt,
            0,
            caster.max_health
    )

    # Search for spell effect
    for effect, chance in spell.effects.items():
        # Store chance for application
        total_chance = chance

        # Apply caster buffs to modify chance
        if effect == "burning" and "kindling" in caster.effects:
            total_chance += caster.effects["kindling"]["bonus_chance"]
        if effect == "freezing" and "glaciate" in caster.effects:
            total_chance += caster.effects["glaciate"]["bonus_chance"]

        # Ensure chance does not exceed 1.0
        total_chance = min(total_chance, 1.0)

        # Log effect with calculated chance
        print(f"{effect} base chance: {chance} → modified chance: {total_chance}")

        # Determine if spell effect is applied
        if random.random() < total_chance:
            if effect in EFFECTS:
                # Apply spell effect
                EFFECTS[effect](caster, target)

    # Log spell damage and effects
    print(f"Spell damage:", spell.dmg)
    print(f"Player effects: ", caster.effects)
    print(f"Target effects: ", target.effects)

def process_effects(entity, dt, state):
    """
    Applies the effects of a spell

    Args:
        entity (Entity) - entity who is effected
    """
    to_remove = []

    # Check for effects
    for effect, data in entity.effects.items():
        data["duration"] -= dt

        # Check for burning effect
        if effect == "burning":
            # Deal damage over time
            source = data.get("source", entity)
            deal_damage(source, entity, data["tick_damage"] * dt, state)

        # Check for effect duration
        if data["duration"] <= 0:
            # Remove effect when time runs out
            to_remove.append(effect)

    for effect in to_remove:
        # Remove effect
        del entity.effects[effect]
    
    # Check for blind effect
    if "blind" in entity.effects:
        entity.effects["blind"]["duration"] -= dt

        if entity.effects["blind"]["duration"] <= 0:
            del entity.effects["blind"]

def regen_mana(entity):
    """
    Determines then applies the mana regeneration rate of a player

    Args:
        player (Entity) - entity to have mana restored
    """
    # Store timestamp
    current_time = pygame.time.get_ticks()

    # Check if 2 second has passed
    if current_time - entity.last_mana_regen >= 2000:
        # Regen 5 mana
        regen_amount = 5

        #Check for freezing effect
        if "freezing" in entity.effects:
            # Store slow amount
            slow = entity.effects["freezing"]["slow"]
            # Reduce regen amount by slow amount
            regen_amount *= (1 - slow)

         # Check for Blitz effect
        if "blitz" in entity.effects:
            # Store bonus amount
            bonus_regen = entity.effects["blitz"]["bonus_regen"]
            # Increase regen by bonus amount
            regen_amount += bonus_regen 

        # Ensure mana does not exceed maximum
        entity.mana = clamp(entity.mana + regen_amount, 0, entity.max_mana)
        entity.last_mana_regen = current_time

def enemy_cast(enemy, player, projectiles, state):
    # Cooldown so enemy doesn't spam
    if not hasattr(enemy, "last_cast_time"):
        enemy.last_cast_time = 0

    current_time = pygame.time.get_ticks()

    if current_time - enemy.last_cast_time < 3000:
        return

    # Get affordable spells
    affordable_spells = [
        name for name, data in SPELL_LIST.items()
        if data["mana_cost"] <= enemy.mana
    ]

    if not affordable_spells:
        return

    # Build weights based on mana cost (and usefulness)
    weights = []
    for name in affordable_spells:
        data = SPELL_LIST[name]
        cost = data["mana_cost"]
        dmg = data.get("dmg", 0)

        weight = cost  # base: higher cost = more likely

        # Prefer damage when player is low
        if player.health < 60 and dmg > 0:
            weight += 30

        # Avoid wasting counterspell if nothing to counter
        if name == "counterspell" and not any(p.target == enemy for p in projectiles):
            weight = 0

        # Slightly reduce pure buff spam
        if dmg == 0 and not data["effects"]:
            weight *= 0.5

        weights.append(weight)

    # Pick a spell
    spell_choice = random.choices(affordable_spells, weights=weights, k=1)[0]

    # Cast it
    cast_spell(spell_choice, enemy, player, projectiles, state)

    enemy.last_cast_time = current_time


# ---------------
# MAIN GAME LOOP
# ---------------
def run():
    """
    Runs the game
    """
    # Initialize game
    screen, canvas, player, sprites, state, enemy, spellbook, projectiles = init()
    # Store clock
    clock = pygame.time.Clock()

    # Run till interuppted
    running = True
    while running:
        # Check for events
        running = handle_events(state, canvas, player, enemy, projectiles)
        
        # Check for drawing on canvas
        handle_drawing(canvas, state)

        # Store time for projectile flight
        dt = clock.tick(FPS) / 1000

        # Draw projectiles
        for projectile in projectiles[:]:
            # Store collision
            finished = projectile.update(dt)

            # Check for collision
            if finished:
                # Apply spell
                resolve_spell(projectile, state)
                # Remove from active projectiles
                projectiles.remove(projectile)

        # Process spell effects
        process_effects(player, dt, state)
        process_effects(enemy, dt, state)

        # Process mana regen
        regen_mana(player)
        regen_mana(enemy)

        enemy_cast(enemy, player, projectiles, state)

        # Update screen
        draw(screen, canvas, player, sprites, enemy, spellbook, projectiles, state)

    # Quit the game
    pygame.quit()

# ---------------
# ENTRY POINT
# ---------------
if __name__ == "__main__":
    start_menu()