import sys
import csv
from pathlib import Path
from datetime import datetime

import numpy as np

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rlglue.rl_glue import RLGlue
from environment.snake_env import SimpleSnake, SimpleSnake2, WinkerSnake, WinkerSnake2, WinkNPoopSnake, WinkNPoopSnake2
from agents.dqn_agent import DQNAgent
from visualizer.pygame_visualizer import (
    Visualizer,
    GRID_LOC, GRID_SIZE,
    WIN_HEIGHT, TRAINING_WIN_WIDTH,
)

SELECTED_ENV = SimpleSnake2
SELECTED_AGENT = DQNAgent

MODELS_DIR = ROOT_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

RESULTS_DIR = ROOT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Training toggle
HEADLESS = False          # True → no window, maximum speed and  False → live game + graph panel

DEMO_FPS = 15             # FPS for the post-checkpoint greedy demo
TRAIN_FPS = 0             # 0 = uncapped during live training episodes

ENV_INFO = {
    "grid_layout": (5, 5),
    "grid_size": GRID_SIZE,
    "grid_location": GRID_LOC,
    "apple_count": 1,
}

CELLS = ENV_INFO['grid_layout'][0] * ENV_INFO['grid_layout'][1]

AGENT_INFO = {
    "state_size": 11,
    "num_actions": 3,
    "hidden_size": 128,
    "lr": 1e-3,
    "gamma": 0.99,
    "epsilon_start": 1.0,
    "epsilon_end": 0.05,
    "epsilon_decay_steps": 300 * CELLS,
    "buffer_capacity": max(50_000, 100 * CELLS),
    "batch_size": 64,
    "min_buffer_size": max(1000, 10 * CELLS),
    "target_sync_every": max(500, CELLS),
    "seed": 0,
}

NUM_EPISODES = 2000
MAX_STEPS_PER_EPISODE = 500   # safety cap so a stuck agent can't run forever
PRINT_EVERY = 100

def save_model_with_log(agent, env_class, agent_class,
                        env_info: dict, agent_info: dict,
                        num_episodes: int, max_steps: int,
                        models_dir: Path):
    """Save the model checkpoint and append a row to trained_model_log.csv """
    env_name = env_class.__name__
    agent_name = agent_class.__name__
    dt_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"model_{env_name}_{agent_name}_{dt_str}.pt"
    model_path = models_dir / filename

    agent.save(model_path)

    log_path = models_dir / "trained_model_log.csv"
    fieldnames = [
        "model_name", "environment_name", "agent_name",
        "grid_layout", "apple_count", "hidden_neurons",
        "num_episodes", "max_steps", "datetime_string",
    ]
    row = {
        "model_name": filename,
        "environment_name": env_name,
        "agent_name": agent_name,
        "grid_layout": str(env_info.get("grid_layout", "?")),
        "apple_count": env_info.get("apple_count", "?"),
        "hidden_neurons": agent_info.get("hidden_size", "?"),
        "num_episodes": num_episodes,
        "max_steps": max_steps,
        "datetime_string": dt_str,
    }
    write_header = not log_path.exists()
    with open(log_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    return model_path, filename

def run_episode_visual(rl_glue: RLGlue, visualizer: Visualizer,
                       max_steps: int, episode_returns: list,
                       episode: int, num_episodes: int,
                       print_every: int):
    """
    Step through one training episode manually so we can render each frame.

    Returns the episode total-return, or None if the user closed the window.
    """
    rl_glue.rl_start()
    env = rl_glue.environment
    is_terminal = False

    while not is_terminal and (max_steps == 0 or
                               rl_glue.num_steps < max_steps):
        # Check for window-close event
        if not visualizer.handle_events():
            return None

        rl_step_result = rl_glue.rl_step()
        is_terminal = rl_step_result[3]
        action_taken = rl_glue.last_action

        epsilon = rl_glue.rl_agent_message("epsilon")
        score = rl_glue.rl_env_message("score")

        poops = getattr(env, "poops", [])

        visualizer.render_training(
            env.grid, env.apples, env.snake,
            score, rl_glue.total_reward,
            episode_returns, epsilon,
            episode, num_episodes, print_every,
            is_terminal, action_taken, poops
        )

    return rl_glue.rl_return()


def run_demo_episode(rl_glue: RLGlue, visualizer: Visualizer,
                     max_steps: int, demo_fps: int = DEMO_FPS) -> bool:
    """
    Run one greedy demo episode (no exploration, no learning, no buffer push).
    Renders at *demo_fps* so the user can follow the policy.

    Returns False if the user closed the window, True otherwise.
    """
    env = rl_glue.environment
    agent = rl_glue.agent

    obs = env.env_start()
    cumulative_reward = 0.0
    terminal = False
    step = 0

    while not terminal and step < max_steps:
        visualizer.tick_at(demo_fps)

        if not visualizer.handle_events():
            return False

        action = agent.select_greedy_action(obs)
        reward, obs, terminal = env.env_step(action)
        cumulative_reward += reward
        score = env.env_message("score")

        poops = getattr(env, "poops", [])

        visualizer.render_demo(
            env.grid, env.apples, env.snake,
            score, round(cumulative_reward, 2),
            episode_label=f"GREEDY DEMO  step {step + 1}/{max_steps}",
            terminal=terminal, action_taken=action, poops=poops
        )
        step += 1

    return True


def main():
    rl_glue = RLGlue(SELECTED_ENV, SELECTED_AGENT)
    AGENT_INFO["state_size"] = rl_glue.environment.current_state.size
    rl_glue.rl_init(agent_init_info=AGENT_INFO, env_init_info=ENV_INFO)
    visualizer   = None
    window_open  = True

    if not HEADLESS:
        import pygame
        pygame.init()
        visualizer = Visualizer(
            grid_layout=ENV_INFO["grid_layout"],
            fps=TRAIN_FPS,
            win_width=TRAINING_WIN_WIDTH,
            win_height=WIN_HEIGHT,
        )
        visualizer.init()

    episode_returns: list[float] = []
    for episode in range(1, NUM_EPISODES + 1):
        if HEADLESS:
            rl_glue.rl_episode(MAX_STEPS_PER_EPISODE)
            episode_return = rl_glue.rl_return()
        else:
            if not window_open:
                break

            episode_return = run_episode_visual(
                rl_glue, visualizer, MAX_STEPS_PER_EPISODE,
                episode_returns, episode, NUM_EPISODES, PRINT_EVERY,
            )

            if episode_return is None:      # user closed window
                window_open = False
                break

        episode_returns.append(episode_return)

        if episode % PRINT_EVERY == 0:
            recent_avg = float(np.mean(episode_returns[-PRINT_EVERY:]))
            epsilon = rl_glue.rl_agent_message("epsilon")
            step_count = rl_glue.rl_agent_message("step_count")
            best_return = max(episode_returns)

            print(
                f"Episode {episode:5d}/{NUM_EPISODES} | "
                f"return: {episode_return:8.2f} | "
                f"avg({PRINT_EVERY}): {recent_avg:8.2f} | "
                f"best: {best_return:8.2f} | "
                f"epsilon: {epsilon:.4f} | "
                f"total steps: {step_count:,}"
            )

            if not HEADLESS and window_open:
                print(f"\tPlaying greedy demo episode ...")
                window_open = run_demo_episode(
                    rl_glue, visualizer,
                    MAX_STEPS_PER_EPISODE, DEMO_FPS,
                )
                if not window_open:
                    break

    model_path, model_name = save_model_with_log(
        agent = rl_glue.agent,
        env_class = SELECTED_ENV,
        agent_class = SELECTED_AGENT,
        env_info = ENV_INFO,
        agent_info = AGENT_INFO,
        num_episodes = NUM_EPISODES,
        max_steps = MAX_STEPS_PER_EPISODE,
        models_dir = MODELS_DIR,
    )
    print(f"\nModel saved  → {model_path}")
    print(f"Log updated  → {MODELS_DIR / 'trained_model_log.csv'}")

    # Save the last frame
    if not HEADLESS and visualizer is not None:
        model_name_no_ext = model_name.replace(".pt", "")
        frame_path = RESULTS_DIR / f"result_{model_name_no_ext}.png"
        visualizer.save_frame(str(frame_path))
        print(f"Last frame saved → {frame_path}")

    rl_glue.rl_cleanup()

    if visualizer is not None:
        visualizer.close()


if __name__ == "__main__":
    main()
