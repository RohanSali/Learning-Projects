import sys
from pathlib import Path
import pygame

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from environment.snake_env import SimpleSnake, SimpleSnake2, WinkerSnake, WinkerSnake2, WinkNPoopSnake, WinkNPoopSnake2
from visualizer.pygame_visualizer import Visualizer, GRID_SIZE, GRID_LOC, WIN_HEIGHT, WIN_WIDTH

GRID_LAYOUT = (5, 5)

# Keyboard -> action mapping. Actions are relative to current facing
# (ahead/right/left), not absolute grid directions, so Up always means
# "keep going the way you're facing" rather than "move toward the top
# of the grid".
ACTION_NAMES = {0: "ahead", 1: "right", 2: "left", 3: "wink"}
ARROW_KEY_ACTIONS = {
    pygame.K_UP: 0,     # ahead
    pygame.K_RIGHT: 1,  # right
    pygame.K_LEFT: 2,   # left
}
WINK_KEY = pygame.K_w


def debug_env_start():
    env = WinkNPoopSnake2()
    env_info = {
        'grid_layout': GRID_LAYOUT,
        'grid_size': GRID_SIZE,
        'grid_location': GRID_LOC,
        'apple_count': 1,
    }

    env.env_init(env_info=env_info)
    observation = env.env_start()

    print("=== env_start() ===")
    print("observation:", observation)
    print("snake head:", env.snake.head.position)
    print("snake facing:", env.snake.head.facing)
    print("snake length:", env.snake.length)
    print("apples:", [apple.position for apple in env.apples])
    print()
    print("Controls: Up=ahead  Right=turn right  Left=turn left  W=wink  Esc/close window=quit")
    print()

    visualizer = Visualizer(
        grid_layout=env.grid.layout,
        fps=2,
        win_width=WIN_WIDTH,
        win_height=WIN_HEIGHT
    )
    visualizer.init()

    poops = getattr(env, "poops", [])
    visualizer.render(env.grid, env.apples, env.snake, score=0, cumulative_reward=0, label="Controller Environment", poops=poops)

    cumulative_reward = 0.0
    step_count = 0
    running = True
    terminal = False

    while running and not terminal:
        visualizer.tick()

        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in ARROW_KEY_ACTIONS:
                    action = ARROW_KEY_ACTIONS[event.key]
                elif event.key == WINK_KEY:
                    action = 3

        if not running:
            break

        if action is None:
            continue  # no key pressed this frame, wait for the next one

        step_count += 1
        reward, observation, terminal = env.env_step(action)
        cumulative_reward += reward

        print(f"--- step {step_count} ---")
        print("action:", action, f"({ACTION_NAMES[action]})")
        print("reward:", reward)
        print("observation:", observation)
        print("terminal:", terminal)
        print("cumulative reward:", cumulative_reward)
        print()

        score = env.env_message("score")

        poops = getattr(env, "poops", [])
        visualizer.render(env.grid, env.apples, env.snake, score=score, cumulative_reward=cumulative_reward, label="Controller Environment", terminal=terminal, action_taken=action, poops=poops)

    if terminal:
        print("=== Episode ended ===")
        print("total steps:", step_count)
        print("final cumulative reward:", cumulative_reward)

    visualizer.close()


if __name__ == "__main__":
    debug_env_start()