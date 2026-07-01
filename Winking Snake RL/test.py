import ast
import sys
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from environment.snake_env import SimpleSnake, SimpleSnake2, WinkerSnake, WinkerSnake2, WinkNPoopSnake, WinkNPoopSnake2
from visualizer.pygame_visualizer import Visualizer, GRID_SIZE, GRID_LOC, WIN_WIDTH, WIN_HEIGHT
from agents.dqn_agent import DQNAgent

MODEL_PATH = ROOT_DIR / "models"
TRAINING_LOG_PATH = MODEL_PATH / "trained_model_log.csv"

ENVS = {
    "SimpleSnake": {"class": SimpleSnake, "states": 13, "actions": 3},
    "SimpleSnake2": {"class": SimpleSnake2, "states": 11, "actions": 3},
    "WinkerSnake": {"class": WinkerSnake, "states": 13, "actions": 4},
    "WinkerSnake2": {"class": WinkerSnake2, "states": 11, "actions": 4},
    "WinkNPoopSnake": {"class": WinkNPoopSnake, "states": 17, "actions": 4},
    "WinkNPoopSnake2": {"class": WinkNPoopSnake2, "states": 15, "actions": 4},
}

AGENTS = {
    "DQNAgent": {"class": DQNAgent},
}


GRID_LAYOUT = (5, 5)
APPLE_COUNT = 1
NUM_EPISODES = 5
FPS = 15


def parse_grid_layout(value):
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return (int(value[0]), int(value[1]))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("Grid size cannot be empty.")
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            parsed = None

        if isinstance(parsed, tuple):
            return tuple(int(x) for x in parsed)
        if isinstance(parsed, list):
            return (int(parsed[0]), int(parsed[1]))

        parts = text.replace(",", " ").split()
        if len(parts) == 2:
            return (int(parts[0]), int(parts[1]))

    raise ValueError(f"Could not parse grid size from: {value}")


def ask_for_grid_layout(default_grid):
    choice = input(f"Do you want to change the grid size? (y/n, default: {default_grid}): ").strip().lower()
    if choice in {"", "n", "no"}:
        return default_grid
    if choice in {"y", "yes"}:
        new_value = input("Enter new grid size (e.g. 5 5 or (5, 5)): ").strip()
        return parse_grid_layout(new_value)
    print("Invalid choice. Using the trained grid size.")
    return default_grid


def ask_for_apple_count(default_count):
    choice = input(f"Do you want to change the apple count? (y/n, default: {default_count}): ").strip().lower()
    if choice in {"", "n", "no"}:
        return default_count
    if choice in {"y", "yes"}:
        new_value = input("Enter new apple count: ").strip()
        return int(new_value)
    print("Invalid choice. Using the trained apple count.")
    return default_count


def main():
    model_name = input("Enter model name to test: ").strip()
    if not model_name.endswith(".pt"):
        model_name = f"{model_name}.pt"

    log_df = pd.read_csv(TRAINING_LOG_PATH)
    matching_row = log_df.loc[log_df["model_name"] == model_name]

    if matching_row.empty:
        raise ValueError(f"Model '{model_name}' was not found in {TRAINING_LOG_PATH}")

    row = matching_row.iloc[0]
    selected_env = str(row.get("environment_name", ""))
    selected_agent = str(row.get("agent_name", ""))
    trained_grid = parse_grid_layout(row.get("grid_layout", GRID_LAYOUT))
    trained_apple_count = int(row.get("apple_count", APPLE_COUNT))

    if selected_env not in ENVS:
        raise ValueError(f"Unsupported environment from training log: {selected_env}")
    if selected_agent not in AGENTS:
        raise ValueError(f"Unsupported agent from training log: {selected_agent}")

    grid_layout = ask_for_grid_layout(trained_grid)
    apple_count = ask_for_apple_count(trained_apple_count)

    env_info = {
        "grid_layout": grid_layout,
        "grid_size": GRID_SIZE,
        "grid_location": GRID_LOC,
        "apple_count": apple_count,
    }

    print(f"Using environment: {selected_env}")
    print(f"Using agent: {selected_agent}")
    print(f"Using grid layout: {grid_layout}")
    print(f"Using apple count: {apple_count}")

    env = ENVS[selected_env]["class"]()
    env.env_init(env_info=env_info)

    model_path = MODEL_PATH / model_name
    agent = AGENTS[selected_agent]["class"].load_for_inference(model_path)

    visualizer = Visualizer(
        grid_layout=grid_layout,
        fps=FPS,
        win_width=WIN_WIDTH,
        win_height=WIN_HEIGHT,
    )
    visualizer.init()

    for episode in range(1, NUM_EPISODES + 1):
        state = env.env_start()
        cumulative_reward = 0.0
        step_count = 0
        terminal = False
        running = True
        label = f"Testing model with {model_name}"

        poops = getattr(env, "poops", [])

        visualizer.render(env.grid, env.apples, env.snake, env.nodes_added, cumulative_reward, label, terminal, poops)

        while running and not terminal:
            visualizer.tick()
            running = visualizer.handle_events()
            if not running:
                break

            action = agent.select_greedy_action(state)
            reward, state, terminal = env.env_step(action)
            cumulative_reward += reward
            step_count += 1

            poops = getattr(env, "poops", [])

            visualizer.render(env.grid, env.apples, env.snake, env.nodes_added, cumulative_reward, label, terminal, action, poops)

        print(
            f"Episode {episode}: steps={step_count}  "
            f"apples_eaten={env.nodes_added}  cumulative_reward={cumulative_reward:.2f}"
        )

        if not running:
            break

    visualizer.close()


if __name__ == "__main__":
    main()
