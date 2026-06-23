import sys
from pathlib import Path
from datetime import datetime
from visualizer.pygame_visualizer import GRID_LOC, GRID_SIZE

import numpy as np

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rlglue.rl_glue import RLGlue
from environment.snake_env import WinkerSnake
from agents.dqn_agent import DQNAgent

MODELS_DIR = ROOT_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Format: YYYY-MM-DD_HH-MM-SS
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"model_{current_time}.pt"

MODEL_PATH = MODELS_DIR / filename

ENV_INFO = {
    "grid_layout": (10, 10),
    "grid_size": GRID_SIZE,
    "grid_location": GRID_LOC,
    "apple_count": 1,
}

AGENT_INFO = {
    "state_size": 13,
    "num_actions": 4,
    "hidden_size": 128,
    "lr": 1e-3,
    "gamma": 0.99,
    "epsilon_start": 1.0,
    "epsilon_end": 0.05,
    "epsilon_decay_steps": 20_000,
    "buffer_capacity": 50_000,
    "batch_size": 64,
    "min_buffer_size": 1_000,
    "target_sync_every": 500,
    "seed": 0,
}

NUM_EPISODES = 2000
MAX_STEPS_PER_EPISODE = 500  # safety cap so a stuck/looping agent can't run forever
PRINT_EVERY = 10


def main():
    rl_glue = RLGlue(WinkerSnake, DQNAgent)
    rl_glue.rl_init(agent_init_info=AGENT_INFO, env_init_info=ENV_INFO)

    episode_returns = []

    for episode in range(1, NUM_EPISODES + 1):
        rl_glue.rl_episode(MAX_STEPS_PER_EPISODE)   

        episode_return = rl_glue.rl_return()
        episode_returns.append(episode_return)

        if episode % PRINT_EVERY == 0:
            recent_avg = float(np.mean(episode_returns[-PRINT_EVERY:]))
            epsilon = rl_glue.rl_agent_message("epsilon")
            print(
                f"Episode {episode:5d} | "
                f"return: {episode_return:7.2f} | "
                f"avg last {PRINT_EVERY}: {recent_avg:7.2f} | "
                f"epsilon: {epsilon:.3f}"
            )

    rl_glue.agent.save(MODEL_PATH)
    print(f"\nSaved trained model to {MODEL_PATH}")

    rl_glue.rl_cleanup()


if __name__ == "__main__":
    main()
