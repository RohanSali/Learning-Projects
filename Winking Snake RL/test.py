import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from environment.snake_env import WinkerSnake, WinkerSnake2, WinkNPoopSnake, WinkNPoopSnake2
from visualizer.pygame_visualizer import Visualizer, GRID_SIZE, GRID_LOC, WIN_WIDTH, WIN_HEIGHT
from agents.dqn_agent import DQNAgent

MODEL_PATH = ROOT_DIR / "models"

GRID_LAYOUT = (5, 5)

ENV_INFO = {
    "grid_layout": GRID_LAYOUT,
    "grid_size": GRID_SIZE,
    "grid_location": GRID_LOC,
    "apple_count": 1,
}

NUM_EPISODES = 5
FPS = 15


def main():
    env = WinkNPoopSnake2()
    env.env_init(env_info=ENV_INFO)

    model_name = input("Enter model name to test : ")
    model_path = Path.joinpath(MODEL_PATH , model_name+".pt")
    agent = DQNAgent.load_for_inference(model_path)

    visualizer = Visualizer(
        grid_layout=GRID_LAYOUT,
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
