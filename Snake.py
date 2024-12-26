import tkinter
import random
import logging
from enum import Enum
import platform

# Optional für Windows-Beep, nur als Beispiel:
# import winsound

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Konstanten für das Spielfeld
ROWS = 25
COLS = 25
TILE_SIZE = 25

WINDOW_WIDTH = TILE_SIZE * COLS
WINDOW_HEIGHT = TILE_SIZE * ROWS

class Direction(Enum):
    UP = "Up"
    DOWN = "Down"
    LEFT = "Left"
    RIGHT = "Right"

class Difficulty(Enum):
    EASY = 150
    MEDIUM = 100
    HARD = 50

class ItemType(Enum):
    RED_FOOD = 1       # Rotes Futter
    GOLD_FOOD = 2      # Goldenes Futter
    POISON = 3
    SPEED_BOOST = 4
    SLOWDOWN = 5

class Tile:
    """
    Repräsentiert ein einzelnes Spielfeld (Kachel).
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Item(Tile):
    """
    Erweiterung der Tile-Klasse um den Typ des Items.
    """
    def __init__(self, x, y, item_type=ItemType.RED_FOOD):
        super().__init__(x, y)
        self.item_type = item_type

class SnakeGame:
    """
    Hauptklasse für das Snake-Spiel.
    """
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title("Snake")
        self.window.resizable(False, False)

        # Zeichenfläche (Canvas)
        self.canvas = tkinter.Canvas(
            self.window,
            bg="black",
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT
        )
        self.canvas.pack()
        self.window.update()

        # Fenster zentrieren
        self.center_window()

        # Spielvariablen initialisieren
        self.snake1 = Tile(TILE_SIZE * 5, TILE_SIZE * 5)
        self.snake2 = Tile(TILE_SIZE * 15, TILE_SIZE * 15)

        # Startbewegungen (0 = kein Move)
        self.velocity_x1, self.velocity_y1 = 0, 0
        self.velocity_x2, self.velocity_y2 = 0, 0

        # Schlange(n)
        self.snake_body1 = [Tile(self.snake1.x, self.snake1.y)]
        self.snake_body2 = [Tile(self.snake2.x, self.snake2.y)]

        # Hindernisse
        self.obstacles = []

        # Items: Hier legen wir ALLE Items (Futter, Gift etc.) ab
        self.items = []

        # Standard-Flags
        self.game_over = False
        self.is_paused = False

        self.score1 = 0
        self.score2 = 0
        self.highscore = self.load_highscore()

        # Gameplay-Variablen
        self.difficulty = None
        self.mode = None

        # Zusätzliche Einstellungen
        self.grid_enabled = False  # Gitternetz an/aus
        self.speed_boost_active = False
        self.slowdown_active = False
        self.speed_boost_timer = 0
        self.slowdown_timer = 0

        # Spezielle Gold-Glow-Funktion
        self.gold_glow_timer1 = 0  # Wie lange die Schlange 1 golden leuchtet
        self.gold_glow_timer2 = 0  # Wie lange die Schlange 2 golden leuchtet

        # Key-Bindings
        self.window.bind("<KeyPress>", self.on_key_press)

    def center_window(self):
        """Zentriert das Fenster auf dem Bildschirm."""
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        window_x = int((screen_width / 2) - (window_width / 2))
        window_y = int((screen_height / 2) - (window_height / 2))

        self.window.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")

    def load_highscore(self):
        """Lädt den Highscore aus einer Datei."""
        try:
            with open("highscore.txt", "r") as file:
                return int(file.read())
        except FileNotFoundError:
            return 0

    def save_highscore(self):
        """Speichert den Highscore in einer Datei."""
        if max(self.score1, self.score2) > self.highscore:
            with open("highscore.txt", "w") as file:
                file.write(str(max(self.score1, self.score2)))

    def on_key_press(self, event):
        """Verarbeitet alle Tasten."""
        key = event.keysym.lower()

        if key == "r":  # Neustart
            self.restart_game(None)
            return
        if key == "p":  # Pause
            self.toggle_pause()
            return
        if key == "g":  # Gitternetz an/aus
            self.grid_enabled = not self.grid_enabled
            logging.info(f"Grid enabled: {self.grid_enabled}")
            return

        # Keine Bewegung, wenn Game Over oder pausiert
        if self.game_over or self.is_paused:
            return

        # Player 1 (Pfeiltasten)
        if event.keysym == Direction.UP.value and self.velocity_y1 != 1:
            self.velocity_x1 = 0
            self.velocity_y1 = -1
        elif event.keysym == Direction.DOWN.value and self.velocity_y1 != -1:
            self.velocity_x1 = 0
            self.velocity_y1 = 1
        elif event.keysym == Direction.LEFT.value and self.velocity_x1 != 1:
            self.velocity_x1 = -1
            self.velocity_y1 = 0
        elif event.keysym == Direction.RIGHT.value and self.velocity_x1 != -1:
            self.velocity_x1 = 1
            self.velocity_y1 = 0

        # Player 2 (WASD)
        if key == "w" and self.velocity_y2 != 1:
            self.velocity_x2 = 0
            self.velocity_y2 = -1
        elif key == "s" and self.velocity_y2 != -1:
            self.velocity_x2 = 0
            self.velocity_y2 = 1
        elif key == "a" and self.velocity_x2 != 1:
            self.velocity_x2 = -1
            self.velocity_y2 = 0
        elif key == "d" and self.velocity_x2 != -1:
            self.velocity_x2 = 1
            self.velocity_y2 = 0

    def toggle_pause(self):
        """Schaltet den Pausen-Zustand um."""
        self.is_paused = not self.is_paused
        logging.info(f"Pause: {self.is_paused}")

    # -------------------------------------------------------------------------
    # Sound-Funktion:
    # -------------------------------------------------------------------------
    def play_sound(self, event_name):
        """
        Diese Methode ruft du auf, um einen Sound-Effekt abzufeuern.
        Mögliche event_names: "item_eaten", "obstacle_collision", "wall_collision", "game_over"
        """
        logging.info(f"Sound-Event: {event_name}")
        # Beispiel für Windows-Beep 
        # if platform.system() == "Windows":
        #     if event_name == "item_eaten":
        #         winsound.Beep(1000, 100)
        #     elif event_name == "game_over":
        #         winsound.Beep(300, 300)

    # -------------------------------------------------------------------------
    # SPIEL-LOGIK
    # -------------------------------------------------------------------------
    def move(self):
        """Bewegt die Schlangen und prüft auf Kollisionen."""
        if self.game_over or self.is_paused:
            return

        # Timer-Updates für Boosts etc.
        if self.speed_boost_active:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boost_active = False
        if self.slowdown_active:
            self.slowdown_timer -= 1
            if self.slowdown_timer <= 0:
                self.slowdown_active = False

        # Timer-Updates für Gold Glow
        if self.gold_glow_timer1 > 0:
            self.gold_glow_timer1 -= 1
        if self.gold_glow_timer2 > 0:
            self.gold_glow_timer2 -= 1

        # Player 1
        self.snake1.x += self.velocity_x1 * TILE_SIZE
        self.snake1.y += self.velocity_y1 * TILE_SIZE
        self.handle_snake_logic(self.snake1, self.snake_body1, 1)

        # Player 2 (nur Multiplayer)
        if self.mode == "Multiplayer":
            self.snake2.x += self.velocity_x2 * TILE_SIZE
            self.snake2.y += self.velocity_y2 * TILE_SIZE
            self.handle_snake_logic(self.snake2, self.snake_body2, 2)

    def handle_snake_logic(self, snake, snake_body, player):
        """Kollisionsabfragen: Wände, eigener Körper, Items, Hindernisse."""
        # Körper-Ende rückt nach vorn
        for i in range(len(snake_body) - 1, 0, -1):
            snake_body[i].x = snake_body[i - 1].x
            snake_body[i].y = snake_body[i - 1].y

        # Kopf
        snake_body[0].x = snake.x
        snake_body[0].y = snake.y

        # Wand-Kollision
        if snake.x < 0 or snake.x >= WINDOW_WIDTH or snake.y < 0 or snake.y >= WINDOW_HEIGHT:
            self.game_over = True
            self.save_highscore()
            self.play_sound("wall_collision")
            return

        # Kollision mit eigenem Körper
        for tile in snake_body[1:]:
            if snake.x == tile.x and snake.y == tile.y:
                self.game_over = True
                self.save_highscore()
                self.play_sound("game_over")
                return

        # Hindernisse
        for obs in self.obstacles:
            if snake.x == obs.x and snake.y == obs.y:
                self.game_over = True
                self.save_highscore()
                self.play_sound("obstacle_collision")
                return

        # Items
        # Kopie der Liste (wir könnten sie während des Loops verändern)
        for item in self.items[:]:
            if snake.x == item.x and snake.y == item.y:
                self.handle_item_collision(item, snake_body, player)

    def handle_item_collision(self, item, snake_body, player):
        """Reagiert auf Kollision mit einem Item."""
        if item.item_type == ItemType.RED_FOOD or item.item_type == ItemType.GOLD_FOOD:
            # Schlange verlängern
            snake_body.append(Tile(snake_body[-1].x, snake_body[-1].y))
            # Score
            points = 1 if item.item_type == ItemType.RED_FOOD else 3

            # Falls goldenes Futter: Farbglow an
            if item.item_type == ItemType.GOLD_FOOD:
                if player == 1:
                    self.gold_glow_timer1 = 30
                else:
                    self.gold_glow_timer2 = 30

            if player == 1:
                self.score1 += points
            else:
                self.score2 += points

            self.play_sound("item_eaten")

            # Beide Food-Items entfernen (rotes + goldenes)
            self.remove_both_food_items()

            # Danach erneut zwei Futteritems spawnen
            self.spawn_food_pair()

        elif item.item_type == ItemType.POISON:
            # Gift = Game Over (oder man könnte Punkte abziehen)
            self.game_over = True
            self.save_highscore()
            self.play_sound("game_over")
            return

        elif item.item_type == ItemType.SPEED_BOOST:
            # Speed-Boost
            self.speed_boost_active = True
            self.speed_boost_timer = 100
            self.play_sound("item_eaten")
            self.items.remove(item)

        elif item.item_type == ItemType.SLOWDOWN:
            # Slowdown
            self.slowdown_active = True
            self.slowdown_timer = 100
            self.play_sound("item_eaten")
            self.items.remove(item)

    def remove_both_food_items(self):
        """
        Sucht in self.items nach RED_FOOD und GOLD_FOOD und entfernt beide.
        """
        red_foods = [i for i in self.items if i.item_type == ItemType.RED_FOOD]
        gold_foods = [i for i in self.items if i.item_type == ItemType.GOLD_FOOD]
        
        # Entferne alle roten und goldenen Items
        for f in red_foods + gold_foods:
            if f in self.items:
                self.items.remove(f)

    # -------------------------------------------------------------------------
    # SPAWN-FUNKTIONEN
    # -------------------------------------------------------------------------
    def spawn_food_pair(self):
        """
        Erzeugt gleichzeitig 1 rotes und 1 goldenes Futter.
        Sobald eines gefressen wird, verschwindet auch das andere.
        """
        # Rotes Futter
        red_x = random.randint(0, COLS - 1) * TILE_SIZE
        red_y = random.randint(0, ROWS - 1) * TILE_SIZE
        red_item = Item(red_x, red_y, ItemType.RED_FOOD)

        # Goldenes Futter
        gold_x = random.randint(0, COLS - 1) * TILE_SIZE
        gold_y = random.randint(0, ROWS - 1) * TILE_SIZE
        gold_item = Item(gold_x, gold_y, ItemType.GOLD_FOOD)

        self.items.append(red_item)
        self.items.append(gold_item)

    def spawn_obstacle(self):
        """Erzeugt ein Hindernis an zufälliger Position."""
        ox = random.randint(0, COLS - 1) * TILE_SIZE
        oy = random.randint(0, ROWS - 1) * TILE_SIZE
        self.obstacles.append(Tile(ox, oy))

    # -------------------------------------------------------------------------
    # ZEICHNEN
    # -------------------------------------------------------------------------
    def draw(self):
        """Zeichnet das Spielfeld und aktualisiert das Spiel."""
        self.move()
        self.canvas.delete("all")

        # Gitternetz
        if self.grid_enabled:
            self.draw_grid()

        # Hindernisse
        for obs in self.obstacles:
            self.canvas.create_rectangle(
                obs.x, obs.y,
                obs.x + TILE_SIZE, obs.y + TILE_SIZE,
                fill="gray"
            )

        # Items
        for item in self.items:
            self.draw_item(item)

        # Schlangen
        self.draw_snake(self.snake_body1, 1)
        if self.mode == "Multiplayer":
            self.draw_snake(self.snake_body2, 2)

        # Scoreboard
        self.draw_scoreboard()

        # Game Over?
        if self.game_over:
            self.draw_game_over_text()
        else:
            # Nächstes Frame
            if self.difficulty:
                base_speed = self.difficulty.value
                # Speed-Boost => 40% schneller
                if self.speed_boost_active:
                    base_speed = int(base_speed * 0.6)
                # Slowdown => 40% langsamer
                if self.slowdown_active:
                    base_speed = int(base_speed * 1.4)

                # Dynamisch verkürzen, min. 50 ms
                speed = max(base_speed - (max(self.score1, self.score2) * 2), 50)
                self.window.after(speed, self.draw)

    def draw_grid(self):
        """Einfaches Gitternetz."""
        for i in range(ROWS):
            self.canvas.create_line(0, i * TILE_SIZE, WINDOW_WIDTH, i * TILE_SIZE, fill="dimgray")
        for j in range(COLS):
            self.canvas.create_line(j * TILE_SIZE, 0, j * TILE_SIZE, WINDOW_HEIGHT, fill="dimgray")

    def draw_item(self, item):
        """Zeichnet ein Item je nach Typ unterschiedlich."""
        color_map = {
            ItemType.RED_FOOD: "red",
            ItemType.GOLD_FOOD: "gold",
            ItemType.POISON: "purple",
            ItemType.SPEED_BOOST: "blue",
            ItemType.SLOWDOWN: "orange",
        }
        c = color_map[item.item_type]
        self.canvas.create_rectangle(
            item.x, item.y,
            item.x + TILE_SIZE, item.y + TILE_SIZE,
            fill=c
        )

    def draw_snake(self, snake_body, player_number):
        """
        Zeichnet die Schlange. Leuchtet gold, wenn gold_glow_timer aktiv ist.
        Unterscheidet Player 1 von Player 2.
        """
        # Standardfarbe
        color = "lime green" if player_number == 1 else "yellow"

        # Wenn gold_glow_timer > 0 => goldener Glow
        if player_number == 1 and self.gold_glow_timer1 > 0:
            color = "orange"
        if player_number == 2 and self.gold_glow_timer2 > 0:
            color = "orange"

        for tile in snake_body:
            self.canvas.create_rectangle(
                tile.x, tile.y,
                tile.x + TILE_SIZE, tile.y + TILE_SIZE,
                fill=color
            )

    def draw_scoreboard(self):
        """Zeigt Score und Highscore an."""
        self.canvas.create_text(
            100, 20,
            font="Arial 10",
            text=f"Highscore: {self.highscore}",
            fill="white"
        )
        # Player 1
        self.canvas.create_text(
            30, 40,
            font="Arial 10",
            text=f"P1: {self.score1}",
            fill="lime green"
        )
        # Player 2 (falls Multiplayer)
        if self.mode == "Multiplayer":
            self.canvas.create_text(
                100, 40,
                font="Arial 10",
                text=f"P2: {self.score2}",
                fill="yellow"
            )
        # PAUSE
        if self.is_paused:
            self.canvas.create_text(
                WINDOW_WIDTH / 2, 20,
                font="Arial 15 bold",
                text="PAUSED",
                fill="white"
            )

    def draw_game_over_text(self):
        """Game-Over-Anzeige."""
        self.canvas.create_text(
            WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 40,
            font="Arial 20",
            text="Game Over!",
            fill="white"
        )
        self.canvas.create_text(
            WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2,
            font="Arial 15",
            text=f"Player 1 Score: {self.score1}",
            fill="lime green"
        )
        if self.mode == "Multiplayer":
            self.canvas.create_text(
                WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 20,
                font="Arial 15",
                text=f"Player 2 Score: {self.score2}",
                fill="yellow"
            )
        self.canvas.create_text(
            WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 60,
            font="Arial 15",
            text="Press R to Restart",
            fill="white"
        )

    def restart_game(self, _event):
        """Setzt das Spiel zurück und zeigt den Modusbildschirm erneut."""
        logging.info("Spiel wird neu gestartet.")
        self.game_over = False
        self.is_paused = False

        self.snake1 = Tile(TILE_SIZE * 5, TILE_SIZE * 5)
        self.snake2 = Tile(TILE_SIZE * 15, TILE_SIZE * 15)
        self.velocity_x1, self.velocity_y1 = 0, 0
        self.velocity_x2, self.velocity_y2 = 0, 0

        self.snake_body1 = [Tile(self.snake1.x, self.snake1.y)]
        self.snake_body2 = [Tile(self.snake2.x, self.snake2.y)]

        self.obstacles = []
        self.items = []

        self.score1 = 0
        self.score2 = 0
        self.speed_boost_active = False
        self.slowdown_active = False
        self.speed_boost_timer = 0
        self.slowdown_timer = 0
        self.gold_glow_timer1 = 0
        self.gold_glow_timer2 = 0

        self.save_highscore()
        self.choose_mode()

    # -------------------------------------------------------------------------
    # MENÜ-FUNKTIONEN
    # -------------------------------------------------------------------------
    def choose_mode(self):
        """Zeigt Optionen zur Auswahl des Spielmodus."""
        self.canvas.delete("all")
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 4,
            font="Arial 20",
            text="Choose Mode",
            fill="white"
        )
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2 - 30,
            font="Arial 15",
            text="1: Singleplayer",
            fill="white"
        )
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2,
            font="Arial 15",
            text="2: Multiplayer",
            fill="white"
        )
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2 + 50,
            font="Arial 15",
            text="S: Settings",
            fill="white"
        )

        self.window.unbind("1")
        self.window.unbind("2")
        self.window.unbind("s")

        def set_mode(mode):
            self.mode = mode
            self.choose_difficulty()

        self.window.bind("1", lambda e: set_mode("Singleplayer"))
        self.window.bind("2", lambda e: set_mode("Multiplayer"))
        self.window.bind("s", lambda e: self.show_settings())

    def show_settings(self):
        """Beispielhaftes Einstellungsmenü."""
        self.canvas.delete("all")
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 3,
            font="Arial 20",
            text="Settings",
            fill="white"
        )
        # Gitternetz
        grid_text = "Grid: ON (press G in-game)" if self.grid_enabled else "Grid: OFF (press G in-game)"
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2 - 30,
            font="Arial 15",
            text=grid_text,
            fill="white"
        )
        # Zurück
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2 + 30,
            font="Arial 15",
            text="M: Return to Main Menu",
            fill="white"
        )

        self.window.unbind("m")
        self.window.bind("m", lambda e: self.choose_mode())

    def choose_difficulty(self):
        """Zeigt Optionen zur Auswahl der Schwierigkeit."""
        self.canvas.delete("all")
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 3,
            font="Arial 20",
            text="Wähle eine Schwierigkeit",
            fill="white"
        )
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2 - 30,
            font="Arial 15",
            text="1: Einfach",
            fill="white"
        )
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2,
            font="Arial 15",
            text="2: Mittel",
            fill="white"
        )
        self.canvas.create_text(
            WINDOW_WIDTH / 2,
            WINDOW_HEIGHT / 2 + 30,
            font="Arial 15",
            text="3: Schwer",
            fill="white"
        )

        self.window.unbind("1")
        self.window.unbind("2")
        self.window.unbind("3")

        def set_difficulty(level):
            self.difficulty = level
            # Nachdem die Schwierigkeit gewählt wurde, spawnen wir erstmal 2 Futteritems
            self.spawn_food_pair()
            self.draw()

        self.window.bind("1", lambda e: set_difficulty(Difficulty.EASY))
        self.window.bind("2", lambda e: set_difficulty(Difficulty.MEDIUM))
        self.window.bind("3", lambda e: set_difficulty(Difficulty.HARD))

    def run(self):
        """Startet das Spiel."""
        self.choose_mode()
        self.window.mainloop()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
