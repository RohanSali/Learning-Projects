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

GRAPH_PANEL_WIDTH  = 600
TRAINING_WIN_WIDTH = WIN_WIDTH + GRAPH_PANEL_WIDTH

class TrainingGraphPanel:
    """
    Draws a live reward-graph + training stats on the right portion of the
    training window.  Consumed by Visualizer.render_training().
    """

    # Colour palette (dark-blue theme)
    C_BG        = (18,  22,  32)
    C_BORDER    = (45,  55,  80)
    C_GRID      = (32,  42,  62)
    C_TITLE     = (190, 210, 255)
    C_STAT_LBL  = (130, 155, 200)
    C_STAT_VAL  = (215, 230, 255)
    C_RAW       = (55,  95,  160) 
    C_AVG       = (70,  210, 130) 
    C_AXIS      = (100, 120, 160)
    C_ZERO      = (80,  100, 140) 

    # Panel layout margins (inside the panel rect)
    MG_LEFT   = 40
    MG_RIGHT  = 20
    MG_TOP    = 140   # room for title + 5 stat rows
    MG_BOTTOM = 80

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Graph drawing area inside the panel
        self.gx = x + self.MG_LEFT
        self.gy = y + self.MG_TOP
        self.gw = width  - self.MG_LEFT - self.MG_RIGHT
        self.gh = height - self.MG_TOP  - self.MG_BOTTOM

        self._fonts_ok = False

    def _ensure_fonts(self):
        if self._fonts_ok:
            return
        self.f_title = pygame.font.SysFont("comicsans", 17)
        self.f_stat  = pygame.font.SysFont("comicsans", 13)
        self.f_small = pygame.font.SysFont("comicsans", 11)
        self._fonts_ok = True

    def draw(self, surface: pygame.Surface, episode_returns: list,
             epsilon: float, episode: int, num_episodes: int,
             print_every: int):
        """Render the full panel onto *surface*."""
        self._ensure_fonts()

        # Panel background
        pygame.draw.rect(surface, self.C_BG,
                         (self.x, self.y, self.width, self.height))
        # Left separator line
        pygame.draw.line(surface, self.C_BORDER,
                         (self.x, self.y), (self.x, self.y + self.height), 2)

        # Title
        title = self.f_title.render("Training Progress", True, self.C_TITLE)
        surface.blit(title,
                     (self.x + (self.width - title.get_width()) // 2,
                      self.y + 10))

        # Thin divider under title
        pygame.draw.line(surface, self.C_BORDER,
                         (self.x, self.y + 36),
                         (self.x + self.width, self.y + 36), 1)

        # Stats block
        n = len(episode_returns)
        recent_n   = min(print_every, n) if n else 1
        recent_avg = sum(episode_returns[-recent_n:]) / recent_n if n else 0.0
        best_r     = max(episode_returns) if n else 0.0
        last_r     = episode_returns[-1]  if n else 0.0

        stats = [
            ("Episode",            f"{episode} / {num_episodes}"),
            ("Epsilon  (ε)",       f"{epsilon:.4f}"),
            (f"Last Return",       f"{last_r:+.2f}"),
            (f"Avg ({print_every})",  f"{recent_avg:+.2f}"),
            ("Best Return",        f"{best_r:+.2f}"),
        ]
        for i, (lbl, val) in enumerate(stats):
            row_y = self.y + 40 + i * 17
            ls = self.f_stat.render(lbl + ":", True, self.C_STAT_LBL)
            vs = self.f_stat.render(val, True, self.C_STAT_VAL)
            surface.blit(ls, (self.x + 10, row_y))
            surface.blit(vs, (self.x + self.width - vs.get_width() - 10, row_y))

        # Graph border 
        pygame.draw.rect(surface, self.C_BORDER,
                         (self.gx, self.gy, self.gw, self.gh), 1)

        if n < 2:
            hint = self.f_small.render("Waiting for episode data …", True,
                                       self.C_STAT_LBL)
            surface.blit(hint,
                         (self.gx + (self.gw - hint.get_width()) // 2,
                          self.gy + self.gh // 2 - 6))
            return

        # Scale
        min_r = min(episode_returns)
        max_r = max(episode_returns)
        padding = max(abs(max_r - min_r) * 0.05, 1.0)
        min_r -= padding
        max_r += padding
        r_span  = max_r - min_r

        def to_px(ep_idx: int, reward: float):
            px = self.gx + int(ep_idx / max(num_episodes - 1, 1) * self.gw)
            py = self.gy + self.gh - int((reward - min_r) / r_span * self.gh)
            px = max(self.gx, min(self.gx + self.gw, px))
            py = max(self.gy, min(self.gy + self.gh, py))
            return px, py

        # Y-axis grid lines + labels
        N_YTICKS = 6
        for i in range(N_YTICKS):
            frac  = i / (N_YTICKS - 1)
            gy_px = self.gy + int(frac * self.gh)
            r_val = max_r - frac * r_span

            # Zero line stands out
            line_color = self.C_ZERO if abs(r_val) < r_span * 0.04 else self.C_GRID
            pygame.draw.line(surface, line_color,
                             (self.gx, gy_px), (self.gx + self.gw, gy_px), 1)

            lbl = self.f_small.render(f"{r_val:.0f}", True, self.C_AXIS)
            surface.blit(lbl, (self.gx - lbl.get_width() - 4, gy_px - 6))

        # X-axis label
        xl = self.f_small.render("Episode", True, self.C_AXIS)
        surface.blit(xl, (self.gx + self.gw - xl.get_width(),
                          self.gy + self.gh + 6))

        # Raw episode rewards (thin, faint)
        raw_pts = [to_px(i, r) for i, r in enumerate(episode_returns)]
        if len(raw_pts) >= 2:
            pygame.draw.lines(surface, self.C_RAW, False, raw_pts, 1)

        # Rolling average (bold green)
        roll = []
        for i in range(n):
            s = max(0, i - print_every + 1)
            roll.append(sum(episode_returns[s:i + 1]) / (i - s + 1))
        avg_pts = [to_px(i, r) for i, r in enumerate(roll)]
        if len(avg_pts) >= 2:
            pygame.draw.lines(surface, self.C_AVG, False, avg_pts, 2)

        # Legend
        leg_x = self.gx
        leg_y = self.gy + self.gh + 22
        # Raw
        pygame.draw.line(surface, self.C_RAW,
                         (leg_x, leg_y + 5), (leg_x + 22, leg_y + 5), 1)
        surface.blit(self.f_small.render("Episode Reward", True, self.C_AXIS),
                     (leg_x + 26, leg_y - 1))
        # Avg
        leg_y2 = leg_y + 17
        pygame.draw.line(surface, self.C_AVG,
                         (leg_x, leg_y2 + 5), (leg_x + 22, leg_y2 + 5), 2)
        surface.blit(self.f_small.render(f"Rolling Avg ({print_every})",
                                         True, self.C_AXIS),
                     (leg_x + 26, leg_y2 - 1))


class Visualizer:
    """
    Pygame-based renderer for the Winking Snake environment.

    Supports three render modes:
      • render()           original mode (debug.py / runner.py)
      • render_training()  game view (left) + live reward graph (right)
      • render_demo()      game view with an episode label banner
    """

    def __init__(self, grid_name: str = "Grid.png",
                 grid_layout: tuple = (10, 10),
                 fps: int = 5,
                 win_width: int = WIN_WIDTH,
                 win_height: int = WIN_HEIGHT):
        self.grid_name   = grid_name
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
        self._graph_panel: TrainingGraphPanel | None = None

    def init(self):
        if self._initialized:
            return

        pygame.font.init()
        self.win = pygame.display.set_mode((self.win_width, self.win_height))
        pygame.display.set_caption("Winking Snake RL")
        self.clock = pygame.time.Clock()
        self.stat_font = pygame.font.SysFont("comicsans", 18)
        self.phase_font = pygame.font.SysFont("comicsans", 20)
        self.title_font = pygame.font.SysFont("timesnewroman", 30, True)

        cs = self.cell_size
        self.bg_img = pygame.image.load(os.path.join(IMG_DIR, "BgIMG2.png"))
        self.grid_img = pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, self.grid_name)), GRID_SIZE)
        self.snake_imgs = [
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Head.png")), cs),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Tail.png")), cs),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Body.png")), cs),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "RightTurn.png")), cs),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "LeftTurn.png")), cs),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Wink.png")), cs),
            pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Collide.png")), cs),
        ]
        self.apple_img = pygame.transform.scale(pygame.image.load(os.path.join(IMG_DIR, "Apple.png")), cs)

        # Create graph panel only when the window is wide enough
        if self.win_width > WIN_WIDTH:
            self._graph_panel = TrainingGraphPanel(
                x=WIN_WIDTH, 
                y=0,
                width=self.win_width - WIN_WIDTH,
                height=self.win_height,
            )

        self._initialized = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def tick(self):
        if self.clock is not None:
            self.clock.tick(self.fps)

    def tick_at(self, fps: int):
        if self.clock is not None:
            self.clock.tick(fps)

    def _draw_game_view(self, grid, apples, snake, score,
                        cumulative_reward, label, terminal, action_taken):
        """
        Blit the game background, grid, apples and snake onto self.win.
        Scores are positioned inside the left WIN_WIDTH-px column.
        Call display.update() separately.
        """
        self.win.blit(self.bg_img, (0, 0))

        # Title
        title_text = self.title_font.render(f"Winker Snake RL Game", True, (0,0,0))
        self.win.blit(title_text, ((WIN_WIDTH - title_text.get_width()) // 2, 40))

        # Score 
        score_text = self.stat_font.render(f"Score: {score}", True, (0, 0, 0))
        self.win.blit(score_text, (WIN_WIDTH - 30 - score_text.get_width(), 115))

        # Cumulitive Reward
        cum_text = self.stat_font.render(f"Cumu. Reward: {round(cumulative_reward, 2)}", True, (0, 0, 0))
        self.win.blit(cum_text, (WIN_WIDTH - 30 - cum_text.get_width(), 140))

        # Current Phase
        if label:
            lbl_surf = self.phase_font.render(label, True, (0, 0, 0))
            self.win.blit(lbl_surf, ((WIN_WIDTH - lbl_surf.get_width()) // 2, 90))

        # Grid
        self.win.blit(self.grid_img, (grid.x, grid.y))

        # Apples
        for apple in apples:
            x, y = grid.get_location(apple.position[0], apple.position[1])
            self.win.blit(self.apple_img, (x, y))

        # Snake
        for i in range(snake.length):
            if terminal:
                if snake.length>2 and i == 1:
                    continue

            node_type = snake.nodes[i].nodeType
            position = snake.nodes[i].position
            face = snake.nodes[i].facing

            idx = node_type
            if node_type == 0:
                if action_taken == 3:
                    idx = 5
                if terminal:
                    idx = 6
                    position = snake.nodes[i].last_pos
                    face = snake.nodes[i].last_facing
            elif node_type == 2:
                turn = snake.nodes[i - 1].whichTurn
                if turn == 1:
                    idx = 3
                elif turn == 2:
                    idx = 4
            elif node_type == 1:
                if terminal and snake.length==2:
                    position = snake.nodes[i].last_pos
                else:
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

            x, y = grid.get_location(position[0], position[1])

            new_rect = rotated_image.get_rect(
                center=image.get_rect(topleft=(x, y)).center
            )  # keep centered correctly after rotation

            self.win.blit(rotated_image, new_rect.topleft)


    def render(self, grid, apples, snake, score, cumulative_reward, label = "", terminal: bool = False, action_taken: int = 0):
        """
        Original game-only render (debug.py / test.py compatible).
        Window size should be WIN_WIDTH x WIN_HEIGHT.
        """
        if not self._initialized:
            self.init()
        self._draw_game_view(grid, apples, snake, score, cumulative_reward, label, action_taken, terminal)
        pygame.display.update()

    def render_training(self, grid, apples, snake, score, cumulative_reward,
                        episode_returns: list, epsilon: float,
                        episode: int, num_episodes: int, print_every: int,
                        terminal: bool = False, action_taken: int = 0):
        """
        Training render: game on the left, live reward graph on the right.
        Requires win_width >= TRAINING_WIN_WIDTH.
        """
        if not self._initialized:
            self.init()
        self._draw_game_view(grid, apples, snake, score, cumulative_reward,
                              label="Training Phase", action_taken=action_taken, terminal=terminal)
        if self._graph_panel is not None:
            self._graph_panel.draw(
                self.win, episode_returns, epsilon,
                episode, num_episodes, print_every)
        pygame.display.update()

    def render_demo(self, grid, apples, snake, score, cumulative_reward,
                    episode_label: str = "", terminal: bool = False, action_taken: int = 0):
        """
        Demo render: game view with an optional banner label at the top.
        Used for post-checkpoint greedy playthroughs.
        """
        if not self._initialized:
            self.init()
        self._draw_game_view(grid, apples, snake, score, cumulative_reward,
                             episode_label, action_taken, terminal)
        pygame.display.update()

    def save_frame(self, filepath: str):
        """Save the current window surface to an image file."""
        if self._initialized and self.win is not None:
            pygame.image.save(self.win, filepath)

    def close(self):
        if self._initialized:
            pygame.quit()
            self._initialized = False