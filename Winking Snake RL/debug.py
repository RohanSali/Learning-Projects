import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from environment.snake_env import WinkerSnake
from visualizer.pygame_visualizer import Visualizer, GRID_SIZE, GRID_LOC

GRID_NAME = "Grid_5.png"
GRID_LAYOUT = (5, 5)

WIN_WIDTH = 440
WIN_HEIGHT = 500

def debug_env_start():
    env = WinkerSnake()
    env_info = {
        'grid_layout' : GRID_LAYOUT,
        'grid_size' : GRID_SIZE,
        'grid_location' : GRID_LOC,
        'apple_count' : 1,
    }

    env.env_init(env_info=env_info)
    observation = env.env_start()

    print("=== env_start() ===")
    print("observation:", observation)
    print("snake head:", env.snake.head.position)
    print("snake facing:", env.snake.head.facing)
    print("snake length:", env.snake.length)
    print("apples:", [apple.position for apple in env.apples])

    visualizer = Visualizer(
        grid_name=GRID_NAME,
        grid_layout=env.grid_layout,
        fps=5,
        win_width=WIN_WIDTH,
        win_height=WIN_HEIGHT
    )
    visualizer.init()

    running = True
    while running:
        visualizer.tick()
        running = visualizer.handle_events()
        visualizer.render(env.grid, env.apples, env.snake, score=0)

    visualizer.close()


if __name__ == "__main__":
    debug_env_start()