import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
import json
import string
from time import sleep

from pygame.display import toggle_fullscreen


def load_config():
    with open("config.json", 'r') as file:
        config = json.load(file)
    return config


config = load_config()

pygame.init()
pygame.mixer.init()

menu_started = True
winScreenActive = False


def changeWinScreenActive():
    global winScreenActive
    winScreenActive = not winScreenActive


pygame.display.set_caption("Mathformer")

BG_COLOR = config["BG_COLOR"]
WIDTH, HEIGHT = config["WIDTH"], config["HEIGHT"]
FPS = config["FPS"]
PLAYER_VEL = config["PLAYER_VEL"]

MAPS_PATH = config["MAPS_FOLDER_NAME"]

window = pygame.display.set_mode((WIDTH, HEIGHT))

global achievements_objects
achievements_objects = []


def get_stats():
    path = join("player.json")
    with open(path, 'r') as playerStats:
        stats = json.load(playerStats)
    return stats

lastMapName = " "

def LastMap(name=None):
    global lastMapName
    if name == None:
        return lastMapName
    else:
        lastMapName = name

def load_map():
    path = join("maps")
    map_files = [f for f in listdir(path) if isfile(join(path, f))]

    all_maps = []

    for _map in map_files:
        with open(join(path, _map), 'r') as _file:
            maps = json.load(_file)
            all_maps.append(maps)

    map = random.choice(all_maps)

    while map["map_name"] == LastMap():
        map = random.choice(all_maps)

    LastMap(map["map_name"])
    return map


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def respawn_player(player):
    player.rect.x = 100
    player.rect.y = 100
    return


def get_block(width, height, left, top):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    rect = pygame.Rect(left, top, width, height)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, name="player"):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.health = 100
        self.name = name

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        if not self.hit:
            self.health -= 20
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, width, height, left, top):
        super().__init__(x, y, width, height)
        block = get_block(width, height, left, top)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "enemy")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = self.animation_count // self.ANIMATION_DELAY % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class EndCheckpoint(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "meta")
        self.ecp = load_sprite_sheets("Items", "Checkpoints/End", width, height)
        self.image = self.ecp["End (Idle)"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "End (Idle)"

    def on(self):
        self.animation_name = "End (Pressed)"

    def off(self):
        self.animation_name = "End (Idle)"

    def loop(self):
        sprites = self.ecp[self.animation_name]
        sprite_index = self.animation_count // self.ANIMATION_DELAY % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)
    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    pygame.draw.rect(window, (255, 0, 0), (10, 10, 200, 20))
    pygame.draw.rect(window, (0, 255, 0), (10, 10, player.health * 2, 20))

    player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if hasattr(obj, 'name') and obj.name != "meta" and pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if hasattr(obj, 'name') and obj.name != "meta" and pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, [obj for obj in objects if obj.name != "text"], -PLAYER_VEL)
    collide_right = collide(player, [obj for obj in objects if obj.name != "text"], PLAYER_VEL)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, [obj for obj in objects if obj.name != "text"], player.y_vel)

    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "enemy":
            player.make_hit()


class Text(pygame.sprite.Sprite):
    def __init__(self, x, y, font_size, text, letter_sprites, scale_factor=1):
        super().__init__()
        self.x = x
        self.y = y
        self.font_size = font_size
        self.text = text.upper()
        self.letter_sprites = letter_sprites
        self.scale_factor = scale_factor
        self.generate_text_sprites()
        self.name = "text"

    def generate_text_sprites(self):
        self.sprites = []
        for char in self.text:
            if char == ' ':
                # Add an empty space for a space character
                self.sprites.append(pygame.Surface((self.font_size, self.font_size), pygame.SRCALPHA))
            elif char in self.letter_sprites:
                # Add the letter sprite to the list
                scaled_sprite = pygame.transform.scale(self.letter_sprites[char],
                                                       (int(self.font_size * self.scale_factor),
                                                        int(self.font_size * self.scale_factor)))
                self.sprites.append(scaled_sprite)
            else:
                # Add an empty space for unknown characters
                self.sprites.append(pygame.Surface((self.font_size, self.font_size), pygame.SRCALPHA))

    def draw(self, win, offset_x):
        current_x = self.x
        for sprite in self.sprites:
            win.blit(sprite, (current_x - offset_x, self.y))
            current_x += self.font_size  # Add letter width to the current X position


class TimedText(Text):
    def __init__(self, x, y, font_size, text, letter_sprites, scale_factor=1, duration_seconds=3, loopNow=True):
        super().__init__(x, y, font_size, text, letter_sprites, scale_factor)
        self.duration_seconds = duration_seconds
        self.visible = True
        self.start_time = pygame.time.get_ticks()
        self.loopNow = loopNow

    def loop(self):
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - self.start_time) / 1000  # Convert milliseconds to seconds

        if elapsed_time >= self.duration_seconds:
            self.visible = False

    def draw(self, win, offset_x):
        if self.visible:
            if self.loopNow:
                self.loop()
            super().draw(win, offset_x)


def load_letter_sprites(font_path, width, height):
    letter_sprites = {}
    font_sheet = pygame.image.load(font_path).convert_alpha()

    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ    0123456789.,:?!()+- "
    index = 0

    for row in range(height):
        for col in range(width):
            char = letters[index]
            letter_rect = pygame.Rect(col * 8, row * 10, 8, 10)
            letter_surface = pygame.Surface((8, 10), pygame.SRCALPHA, 32)
            letter_surface.blit(font_sheet, (0, 0), letter_rect)
            letter_sprites[char] = pygame.transform.scale(letter_surface, (8, 10))
            index += 1
    return letter_sprites


class Button(Object):
    def __init__(self, x, y, width, height, image):
        super().__init__(x, y, width, height, "button")
        self.image = pygame.image.load(join("assets", "Menu", "Buttons", image + ".png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


def fade_out(window, clock, duration):
    start_time = pygame.time.get_ticks()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA | pygame.HWSURFACE)
    alpha = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_time

        if elapsed_time >= duration:
            return

        alpha = elapsed_time / duration
        overlay.fill((0, 0, 0, alpha * 255))  # Use black color for fading out
        window.blit(overlay, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)


class StartMenu():
    def __init__(self, window, background, bg_image, offset_x, block_size, letter_sprites, objects, setobjects, clock):
        self.achievements_shown = False
        self.background = background
        self.bg_image = bg_image
        self.offset_x = offset_x
        self.block_size = block_size
        self.letter_sprites = letter_sprites

        self.objects = objects

        self.settings_shown = False

        self.text_objects = [Text(85, 100, 64, "MATHFORMER", self.letter_sprites)]

        self.settings_objects = setobjects

        self.clock = clock

        self.settings_objects.append(Text(85, 100, 64, "USTAWIENIA", self.letter_sprites))
        self.settings_objects.append(Text(200, 365, 32, "COFNIJ", self.letter_sprites))

        self._text = "POZIOM {}".format(get_stats()["map_level"])
        achievements_objects.append(
            Text(WIDTH / 2 - (len(self._text) * 46 / 2), HEIGHT / 2 - 46, 46, self._text, self.letter_sprites))
        achievements_objects.append(Button(25, HEIGHT - 90, 60, 60, "Back"))
        achievements_objects.append(Text(90, HEIGHT - 75, 32, "COFNIJ", self.letter_sprites))
        for i in range(len(self.text_objects)):
            self.objects.append(self.text_objects[i])

    def switch_settings(self):
        self.settings_shown = not self.settings_shown

    def switch_achievements(self):
        self.achievements_shown = not self.achievements_shown

    def loop(self):
        for tile in self.background:
            window.blit(self.bg_image, tile)

        if not self.settings_shown and not self.achievements_shown:
            for obj in self.objects:
                obj.draw(window, self.offset_x)

        if self.achievements_shown:
            for obj in achievements_objects:
                obj.draw(window, self.offset_x)

        if self.settings_shown:
            for setting_object in self.settings_objects:
                setting_object.draw(window, self.offset_x)

        pygame.display.update()


class RandomMathTask():
    def __init__(self):
        self.numbers = []
        self.numbers.append(random.randint(-10, 10))
        self.numbers.append(random.choice(["+", "-", ":", "x"]))
        self.numbers.append(random.randint(-10, 10))

        if self.numbers[1] == ":":
            while self.numbers[2] == 0 or (
                    self.numbers[0] / self.numbers[2] != math.floor(self.numbers[0] / self.numbers[2])):
                self.numbers[2] = random.randint(-10, 10)

    def get(self):
        return self.numbers

    def calculate_result(self):
        if self.numbers[1] == "+":
            return self.numbers[0] + self.numbers[2]
        elif self.numbers[1] == "-":
            return self.numbers[0] - self.numbers[2]
        elif self.numbers[1] == ":":
            # Check if the denominator is not zero
            return self.numbers[0] / self.numbers[2] if self.numbers[2] != 0 else "-"
        elif self.numbers[1] == "x":
            return self.numbers[0] * self.numbers[2]
        else:
            return "-"


class PlayerWinScreen():
    def __init__(self, window, background, bg_image, offset_x, letter_sprites, clock):
        self.resultNumbers = None
        self.background = background
        self.bg_image = bg_image
        self.letter_sprites = letter_sprites
        self.offset_x = offset_x
        self.window = window

        self.objects = []

        self.clock = clock

        self.numbersObjects = []

        self.objects.append(Text(110, 150, 36, "Oblicz:", self.letter_sprites))

        self.task = RandomMathTask()
        self.numbers = self.task.get()

        self.current_num_pos = 110

        if(str(self.numbers[2]).startswith("-")):
            self.equation_text = Text(110, 200, 36,
                                      (str(self.numbers[0]) + " " + str(self.numbers[1]) + " (" + str(self.numbers[2])) + ")",
                                      self.letter_sprites)
        else:
            self.equation_text = Text(110, 200, 36,
                                      (str(self.numbers[0]) + " " + str(self.numbers[1]) + " " + str(
                                          self.numbers[2])),
                                      self.letter_sprites)


        self.objects.append(self.equation_text)

        self.result_texts = []
        for i in range(len(self.numbers) + 4):
            result_text = Text(110 + (i * 36), 350, 36, "-", self.letter_sprites)
            self.result_texts.append(result_text)
            self.objects.append(result_text)

        self.result = math.floor(self.task.calculate_result())
        self.CheckResultButton = Button(110 + (len(self.numbers) + 7) * 36, 310, 60, 60, "Next")
        self.RemoveNumberFromTaskButton = Button(110 + (len(self.numbers) + 5) * 36, 310, 60, 60, "Back")

        self.objects.append(self.CheckResultButton)
        self.objects.append(self.RemoveNumberFromTaskButton)

    def loop(self):
        for tile in self.background:
            self.window.blit(self.bg_image, tile)

        for obj in self.objects:
            obj.draw(self.window, self.offset_x)

        for obj in self.numbersObjects:
            obj.draw(self.window, self.offset_x)

        pygame.display.update()

    def handle(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.TEXTINPUT:
                key = event.text
                if key.isdigit():
                    # If the key is a digit, add it to the equation text
                    self.numbersObjects.append(Text(self.current_num_pos, 326, 36, key, self.letter_sprites))
                    self.current_num_pos += 36
                elif key in ['+', '-']:
                    # If the key is '+' or '-', add it to the equation text
                    self.numbersObjects.append(Text(self.current_num_pos, 326, 36, key, self.letter_sprites))
                    self.current_num_pos += 36
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0] or (event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE):
                mouse_pos = pygame.mouse.get_pos()
                if (self.RemoveNumberFromTaskButton.is_clicked(mouse_pos)) or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE):
                    if len(self.numbersObjects) > 0:
                        self.numbersObjects.pop()
                        self.current_num_pos -= 36
                if self.CheckResultButton.is_clicked(mouse_pos) and not event.type == pygame.KEYDOWN:
                    self.resultNumbers = []
                    for obj in self.numbersObjects:
                        self.resultNumbers.append(str(obj.text))
                    self.resultNumbers = ''.join(self.resultNumbers)
                    if not self.resultNumbers == "":
                        if not self.resultNumbers.endswith("-"):
                            if not self.resultNumbers.endswith("+"):
                                if int(self.resultNumbers) == int(self.result):
                                    changeWinScreenActive()
                                    fade_out(self.window, self.clock, 1250)
                                else:
                                    self.objects.append(
                                        TimedText(75, 450, 36, "zly wynik!", self.letter_sprites, 1, 2, True))
                            else:
                                self.objects.append(
                                    TimedText(75, 450, 36, "czy minus?", self.letter_sprites, 1, 2, True))
                        else:
                            self.objects.append(TimedText(75, 450, 36, "czy plus?", self.letter_sprites, 1, 2, True))
                    else:
                        self.objects.append(TimedText(75, 450, 36, "gdzie liczby?", self.letter_sprites, 1, 2, True))


class MusicButton(Button):
    def __init__(self, x, y, width, height, image, music_on=True):
        super().__init__(x, y, width, height, image)
        self.music_on = music_on

    def toggle_music(self):
        self.music_on = not self.music_on
        path = join("config.json")
        with open(path, 'r') as _config:
            _con = json.load(_config)
            _con["MUSIC"] = self.music_on

        with open(path, 'w') as _config:
            json.dump(_con, _config)

        if self.music_on:
            pygame.mixer.music.play(-1) or pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()


def updatePlayerLevel():
    path = join("player.json")
    with open(path, 'r') as playerStats:
        stats = json.load(playerStats)
        stats["map_level"] = stats["map_level"] + 1

    with open(path, 'w') as playerStats:
        json.dump(stats, playerStats)


class RoundedRectangle():
    def __init__(self, surface, rect, color, corner_radius):
        self.surface = surface
        self.rect = pygame.Rect(rect)
        self.color = color
        self.corner_radius = corner_radius

    def draw(self, window, offset_x):
        pygame.draw.rect(window, self.color, self.rect, border_radius=self.corner_radius)

    def update_rect(self, rect):
        self.rect = pygame.Rect(rect)


def main(window, menu_started):
    global timed_text
    current_level = get_stats()["map_level"]
    if menu_started:
        run = False
    else:
        run = True
    clock = pygame.time.Clock()

    pygame.mixer.init()
    pygame.mixer.music.load("assets/Music/background.mp3")
    pygame.mixer.music.set_volume(0.1)

    if config["MUSIC"]:
        pygame.mixer.music.play(-1)

    block_size = 96

    offset_x = 0
    scroll_area_width = 200

    font_path = join("assets", "Menu", "Text", "Text (Black) (8x10).png")
    letter_sprites = load_letter_sprites(font_path, 10, 5)

    music_button = MusicButton(110, 200, 60, 60, "Volume", music_on=True)
    back_sett_btn = Button(110, 350, 60, 60, "Back")

    settings_objects = [music_button, back_sett_btn, Text(200, 215, 32, "MUZYKA", letter_sprites)]
    fullscreen_btn = Button(110, 275, 60, 60, "Fullscreen")
    settings_objects.append(fullscreen_btn)
    settings_objects.append(Text(200, 290, 32, "Pelny ekran", letter_sprites))
    menu_objects = []
    playBtn = Button((WIDTH - 85) / 2, (HEIGHT - 85) / 2, 85, 85, "Play")
    menu_objects.append(playBtn)
    settingsBtn = Button((WIDTH / 2) - 75 * 2, (HEIGHT - 75) / 2, 75, 75, "Settings")
    menu_objects.append(settingsBtn)
    achievementsBtn = Button((WIDTH + 75 * 2) / 2, (HEIGHT - 75) / 2, 75, 75, "Achievements")
    menu_objects.append(achievementsBtn)

    player = Player(100, 100, 50, 50)

    map_data = load_map()

    background, bg_image = get_background(map_data.get("background") + ".png")

    blocks = map_data.get("blocks", [])
    fire_objects = map_data.get("fires", [])

    floor = [Block(i * 96, HEIGHT - (0 * 96) - 96, 96, 96, map_data.get("floorX"), map_data.get("floorY")) for i in
             range(-WIDTH // block_size, (WIDTH * 2) // block_size)]

    menu_objects.extend(floor)
    objects = [*floor]

    for block_info in blocks:
        x = block_info["x"]
        y = block_info["y"]
        width = block_info["width"]
        height = block_info["height"]
        left = block_info["left"]
        top = block_info["top"]
        objects.append(Block(x * width, HEIGHT - (y * height) - height, width, height, left, top))

    fires = [
        Fire(fire_info["x"] * 96 + 32, HEIGHT - (fire_info["y"] * 96) - 80 * 2, fire_info["width"], fire_info["height"])
        for fire_info in
        fire_objects]
    objects.extend(fires)

    ecp = [
        EndCheckpoint(ecp_info["x"] * 96 + 32, HEIGHT - (ecp_info["y"] * 96) - 80 * 2, ecp_info["width"],
                      ecp_info["height"])
        for ecp_info in map_data.get("ecp", [])
    ]
    objects.extend(ecp)

    # Dodaj text_object do listy objects

    menu = StartMenu(window, background, bg_image, offset_x, block_size, letter_sprites, menu_objects, settings_objects,
                     clock)
    while menu_started:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    menu_started = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    # Check if the mouse click is on the button
                    if playBtn.is_clicked(mouse_pos):
                        menu_started = False
                    if settingsBtn.is_clicked(mouse_pos):
                        fade_out(window, clock, 1000 / 3)
                        menu.switch_settings()
                    if back_sett_btn.is_clicked(mouse_pos):
                        fade_out(window, clock, 1000 / 3)
                        menu.switch_settings()
                    if achievementsBtn.is_clicked(mouse_pos):
                        fade_out(window, clock, 1000 / 3)
                        menu.switch_achievements()
                    if music_button.is_clicked(mouse_pos):
                        music_button.toggle_music()
                    if fullscreen_btn.is_clicked(mouse_pos):
                        fade_out(window, clock, 1000 / 2)
                        toggle_fullscreen()
                    if achievements_objects[1].is_clicked(mouse_pos):
                        fade_out(window, clock, 1000 / 3)
                        menu.switch_achievements()

        menu.loop()

        if not menu_started:
            fade_out(window, clock, 1500)
            run = True

    timed_text = TimedText(135, 150, 64, "Poziom {}".format(current_level),
                           letter_sprites, 1, 3, False)

    text_objects = [timed_text]

    for i in range(len(text_objects)):
        objects.append(text_objects[i])

    is_win = False

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
                if event.key == pygame.K_ESCAPE:
                    run = False

        player.loop(FPS)
        timed_text.loop()
        timed_text.draw(window, 0)
        for fire in fires:
            fire.loop()
            fire.on()

        handle_move(player, objects)

        for _ecp in ecp:
            _ecp.loop()

            # Check for collision with EndCheckpoint
            if pygame.sprite.collide_mask(player, _ecp) and not is_win:
                is_win = True
                fade_out(window, clock, 1000)
                changeWinScreenActive()
                winScreen = PlayerWinScreen(window, background, bg_image, 0, letter_sprites, clock)
                while winScreenActive:
                    winScreen.handle()
                    clock.tick(FPS)
                    winScreen.loop()

                updatePlayerLevel()
                main(window, menu_started=False)

        if player.rect.y >=550:
            player.health = 0

        if player.health <= 0:
            player.health = 100
            offset_x = 0
            respawn_player(player)


        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    main(window, menu_started=True)


if __name__ == "__main__":
    main(window, menu_started)
