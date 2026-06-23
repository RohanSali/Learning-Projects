import os
from pathlib import Path
import pygame

pygame.font.init()

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
IMG_DIR = os.path.join(ROOT_DIR, "imgs")

GRID_SIZE = (500, 500)
GRID_LOC = (40, 200)

WIN_WIDTH = 580
WIN_HEIGHT = 740


class Visualizer:
    def __init__(self,grid_name="Grid_10.png", grid_layout=(10,10), fps=5, win_width=WIN_WIDTH, win_height=WIN_HEIGHT):
        self.grid_name = grid_name
        self.grid_layout = grid_layout
        self.cell_size = (
            int(GRID_SIZE[0] / grid_layout[0]),
            int(GRID_SIZE[1] / grid_layout[1]),
        )
        self.fps = fps
        self.win_width = win_width
        self.win_height = win_height
        self.win = None
        self.clock = None
        self.stat_font = None
        self._initialized = False

    def init(self):
        if self._initialized:
            return

        pygame.font.init()
        self.win = pygame.display.set_mode((self.win_width, self.win_height))
        self.clock = pygame.time.Clock()
        self.stat_font = pygame.font.SysFont("comicsans", 15)

        cell_size = self.cell_size
        self.bg_img = pygame.image.load(os.path.join(IMG_DIR, "BgIMG2.png"))
        self.grid_img = pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, self.grid_name)), GRID_SIZE)
        self.snake_imgs = [
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Head.png")), cell_size),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Tail.png")), cell_size),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Body.png")), cell_size),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "RightTurn.png")), cell_size),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "LeftTurn.png")), cell_size),
        ]
        self.apple_img = pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Apple.png")), cell_size)

        self._initialized = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def tick(self):
        if self.clock is not None:
            self.clock.tick(self.fps)

    def render(self, grid, apples, snake, score, cumulative_reward):
        if not self._initialized:
            self.init()

        self.win.blit(self.bg_img, (0, 0))

        score_text = self.stat_font.render("Score: " + str(score), 1, (0, 0, 0))
        self.win.blit(score_text, (self.win_width - 20 - score_text.get_width(), 30))

        cum_re_text = self.stat_font.render("Cumu. Reward: " + str(cumulative_reward), 1, (0, 0, 0))
        self.win.blit(cum_re_text, (self.win_width - 20 - cum_re_text.get_width(), 50))

        # Grid
        self.win.blit(self.grid_img, (grid.x, grid.y))

        # Apples
        for apple in apples:
            x, y = grid.get_location(apple.position[0], apple.position[1])
            self.win.blit(self.apple_img, (x, y))

        # Snake
        for i in range(snake.length):
            node_type = snake.nodes[i].nodeType
            position = snake.nodes[i].position
            x, y = grid.get_location(position[0], position[1])
            face = snake.nodes[i].facing

            idx = node_type

            if node_type == 2:
                turn = snake.nodes[i - 1].whichTurn
                if turn == 1:
                    idx = 3
                elif turn == 2:
                    idx = 4
            elif node_type == 1:
                face = snake.nodes[i - 1].facing

            image = self.snake_imgs[idx]

            rotation = 0  # No rotation
            if face == 1:
                rotation = 270  # 90 deg anti-clockwise
            elif face == 2:
                rotation = 180  # 180 deg anti-clockwise
            elif face == 3:
                rotation = 90  # 270 deg anti-clockwise
            rotated_image = pygame.transform.rotate(image, rotation)
            new_rect = rotated_image.get_rect(
                center=image.get_rect(topleft=(x, y)).center
            )  # keep centered correctly after rotation

            self.win.blit(rotated_image, new_rect.topleft)

        pygame.display.update()

    def close(self):
        """Shut pygame down cleanly."""
        if self._initialized:
            pygame.quit()
            self._initialized = False