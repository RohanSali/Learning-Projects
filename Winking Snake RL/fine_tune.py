import sys
import csv
from pathlib import Path
from datetime import datetime

import numpy as np

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rlglue.rl_glue import RLGlue
from environment.snake_env import WinkerSnake
from agents.dqn_agent import DQNAgent
from visualizer.pygame_visualizer import (
    Visualizer,
    GRID_LOC, GRID_SIZE,
    WIN_HEIGHT, TRAINING_WIN_WIDTH,
)
# Re-use shared training utilities from train.py
from train import (
    save_model_with_log,
    run_episode_visual,
    run_demo_episode,
    MODELS_DIR,
)

LOAD_MODEL_PATH = MODELS_DIR / "model_WinkerSnake_DQNAgent_YYYY-MM-DD_HH-MM-SS.pt"

FINETUNE_ENV_INFO = {
    "grid_layout": (10, 10),
    "grid_size": GRID_SIZE,
    "grid_location": GRID_LOC,
    "apple_count": 1,
}

FINETUNE_AGENT_OVERRIDES = {
    "lr": 1e-4,
    "epsilon_start": 0.3,
    "epsilon_end": 0.05,
    "epsilon_decay_steps": 10_000,
    "buffer_capacity": 50_000,
    "batch_size": 64,
    "min_buffer_size": 500,
    "target_sync_every": 500,
    "gamma": 0.99,
}

NUM_EPISODES = 1_000
MAX_STEPS_PER_EPISODE = 500
PRINT_EVERY = 100

HEADLESS = False   # True → headless, False → live window + graph
DEMO_FPS = 5       # FPS for the post-checkpoint greedy demo

GRID_NAME = f"Grid_{FINETUNE_ENV_INFO['grid_layout'][0]}.png"


def main():
    load_path = Path(LOAD_MODEL_PATH)
    if not load_path.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {load_path}\n"
            f"Please check LOAD_MODEL_PATH in fine_tune.py.\n"
            f"Available models in {MODELS_DIR}:\n"
            + "\n".join(f"  • {p.name}" for p in sorted(MODELS_DIR.glob("*.pt")))
        )

    print(f"Loading checkpoint  → {load_path.name}")

    agent = DQNAgent.load_for_finetuning(
        path=load_path,
        agent_info_overrides=FINETUNE_AGENT_OVERRIDES,
    )
    print(
        f"Architecture : state_size={agent.state_size}, "
        f"num_actions={agent.num_actions}, hidden_size={agent.hidden_size}"
    )
    print(
        f"Fine-tune LR : {FINETUNE_AGENT_OVERRIDES.get('lr', 1e-4)} | "
        f"ε: {agent.epsilon:.3f} → {agent.epsilon_end:.3f} "
        f"over {agent.epsilon_decay_steps:,} steps"
    )

    # Wire agent + environment into a minimal RLGlue instance
    env = WinkerSnake()
    env.env_init(FINETUNE_ENV_INFO)

    rl_glue = RLGlue(WinkerSnake, DQNAgent)
    rl_glue.environment = env
    rl_glue.agent = agent
    rl_glue.total_reward = 0.0
    rl_glue.num_steps = 0
    rl_glue.num_episodes = 0
    rl_glue.last_action = None

    # Visualizer
    visualizer = None
    window_open = True

    if not HEADLESS:
        import pygame
        pygame.init()
        visualizer = Visualizer(
            grid_name=GRID_NAME,
            grid_layout=FINETUNE_ENV_INFO["grid_layout"],
            fps=0,   # uncapped during training steps
            win_width=TRAINING_WIN_WIDTH,
            win_height=WIN_HEIGHT,
        )
        visualizer.init()

    # Fine-tuning loop
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
            if episode_return is None:
                window_open = False
                break

        episode_returns.append(episode_return)

        if episode % PRINT_EVERY == 0:
            recent_avg = float(np.mean(episode_returns[-PRINT_EVERY:]))
            epsilon = rl_glue.rl_agent_message("epsilon")
            step_count = rl_glue.rl_agent_message("step_count")
            best_return = max(episode_returns)

            print(
                f"[Fine-Tune] Episode {episode:5d}/{NUM_EPISODES} | "
                f"return: {episode_return:8.2f} | "
                f"avg({PRINT_EVERY}): {recent_avg:8.2f} | "
                f"best: {best_return:8.2f} | "
                f"ε: {epsilon:.4f} | "
                f"total steps: {step_count:,}"
            )

            if not HEADLESS and window_open:
                print(f"  → Playing greedy demo episode …")
                window_open = run_demo_episode(
                    rl_glue, visualizer,
                    MAX_STEPS_PER_EPISODE, DEMO_FPS,
                )
                if not window_open:
                    break

    # Save fine-tuned model + update CSV log
    agent_info_for_log = {
        "hidden_size": agent.hidden_size,
        **FINETUNE_AGENT_OVERRIDES,
    }
    model_path, model_name = save_model_with_log(
        agent = rl_glue.agent,
        env_class = WinkerSnake,
        agent_class = DQNAgent,
        env_info = FINETUNE_ENV_INFO,
        agent_info = agent_info_for_log,
        num_episodes = NUM_EPISODES,
        max_steps = MAX_STEPS_PER_EPISODE,
        models_dir = MODELS_DIR,
    )
    print(f"\n✓  Fine-tuned model saved → {model_path}")
    print(f"✓  Log updated            → {MODELS_DIR / 'trained_model_log.csv'}")

    rl_glue.rl_cleanup()

    if visualizer is not None:
        visualizer.close()


if __name__ == "__main__":
    main()
