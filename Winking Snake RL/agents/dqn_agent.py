import random
from collections import deque

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from rlglue.agent import BaseAgent


class QNetwork(nn.Module):
    """Small MLP mapping state -> one Q-value per action."""

    def __init__(self, state_size, action_size, hidden_size=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, action_size),
        )

    def forward(self, x):
        return self.net(x)


class ReplayBuffer:
    """Fixed-size cyclic buffer of (state, action, reward, next_state, done) transitions."""

    def __init__(self, capacity=50_000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32),
        )

    def __len__(self):
        return len(self.buffer)


class DQNAgent(BaseAgent):
    """
    DQN agent with experience replay and a periodically-synced target
    network.

    agent_info keys (all optional, sensible defaults provided):
        state_size           : int, default 13  (must match env observation length)
        num_actions           : int, default 4
        hidden_size            : int, default 128
        lr                      : float, default 1e-3
        gamma                   : float, default 0.99
        epsilon_start            : float, default 1.0
        epsilon_end               : float, default 0.05
        epsilon_decay_steps        : int, default 20_000
        buffer_capacity              : int, default 50_000
        batch_size                    : int, default 64
        min_buffer_size                : int, default 1_000 (pure exploration before training starts)
        target_sync_every                : int, default 500 (steps between target network syncs)
        device                            : "cpu" or "cuda", default auto-detected
        seed                               : int, optional
    """

    def __init__(self):
        self.q_network = None
        self.target_network = None
        self.optimizer = None
        self.replay_buffer = None

        self.last_state = None
        self.last_action = None

        self.step_count = 0
        self.epsilon = 1.0

    def agent_init(self, agent_info=None):
        agent_info = agent_info or {}

        self.state_size = agent_info.get("state_size", 13)
        self.num_actions = agent_info.get("num_actions", 4)
        self.hidden_size = agent_info.get("hidden_size", 128)
        lr = agent_info.get("lr", 1e-3)

        self.gamma = agent_info.get("gamma", 0.99)
        self.epsilon_start = agent_info.get("epsilon_start", 1.0)
        self.epsilon_end = agent_info.get("epsilon_end", 0.05)
        self.epsilon_decay_steps = agent_info.get("epsilon_decay_steps", 20_000)
        self.batch_size = agent_info.get("batch_size", 64)
        self.min_buffer_size = agent_info.get("min_buffer_size", 1_000)
        self.target_sync_every = agent_info.get("target_sync_every", 500)

        seed = agent_info.get("seed")
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)

        device_name = agent_info.get("device")
        if device_name is None:
            device_name = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device_name)

        self.q_network = QNetwork(self.state_size, self.num_actions, self.hidden_size).to(self.device)
        self.target_network = QNetwork(self.state_size, self.num_actions, self.hidden_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()

        self.optimizer = optim.Adam(self.q_network.parameters(), lr=lr)
        self.replay_buffer = ReplayBuffer(agent_info.get("buffer_capacity", 50_000))

        self.step_count = 0
        self.epsilon = self.epsilon_start

    # ---- RL-Glue interface ----

    def agent_start(self, state):
        self.last_state = np.asarray(state, dtype=np.float32)
        self.last_action = self._select_action(self.last_state)
        return self.last_action

    def agent_step(self, reward, state):
        state = np.asarray(state, dtype=np.float32)

        self.replay_buffer.push(self.last_state, self.last_action, reward, state, False)
        self._learn()
        self._update_epsilon()

        action = self._select_action(state)

        self.last_state = state
        self.last_action = action
        return action

    def agent_end(self, reward):
        # Terminal transition: no meaningful "next state", so use a zero
        # vector and mark done=True - the bootstrap term gets multiplied
        # by (1 - done) during learning, so its value doesn't matter.
        terminal_state = np.zeros_like(self.last_state)
        self.replay_buffer.push(self.last_state, self.last_action, reward, terminal_state, True)
        self._learn()
        self._update_epsilon()

    def agent_cleanup(self):
        self.last_state = None
        self.last_action = None

    def agent_message(self, message):
        if message == "epsilon":
            return self.epsilon
        if message == "step_count":
            return self.step_count
        return None

    # ---- Internals ----

    def _select_action(self, state):
        if random.random() < self.epsilon:
            return random.randrange(self.num_actions)
        return self.select_greedy_action(state)

    def select_greedy_action(self, state):
        """Pure greedy action - no exploration, no buffer/learning side effects."""
        state = np.asarray(state, dtype=np.float32)
        with torch.no_grad():
            state_t = torch.from_numpy(state).float().unsqueeze(0).to(self.device)
            q_values = self.q_network(state_t)
            return int(torch.argmax(q_values, dim=1).item())

    def _update_epsilon(self):
        self.step_count += 1
        decay_progress = min(1.0, self.step_count / self.epsilon_decay_steps)
        self.epsilon = self.epsilon_start + decay_progress * (self.epsilon_end - self.epsilon_start)

    def _learn(self):
        if len(self.replay_buffer) < max(self.batch_size, self.min_buffer_size):
            return

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        states = torch.from_numpy(states).to(self.device)
        actions = torch.from_numpy(actions).to(self.device)
        rewards = torch.from_numpy(rewards).to(self.device)
        next_states = torch.from_numpy(next_states).to(self.device)
        dones = torch.from_numpy(dones).to(self.device)

        q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(dim=1)[0]
            targets = rewards + self.gamma * next_q_values * (1.0 - dones)

        loss = nn.functional.smooth_l1_loss(q_values, targets)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.step_count % self.target_sync_every == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

    # ---- Save / Load ----

    def save(self, path):
        torch.save({
            "q_network": self.q_network.state_dict(),
            "state_size": self.state_size,
            "num_actions": self.num_actions,
            "hidden_size": self.hidden_size,
        }, path)

    @classmethod
    def load_for_inference(cls, path, device=None):
        """
        Build a DQNAgent purely for running a trained policy (no replay
        buffer / optimizer / target network needed) - used by test.py.
        """
        checkpoint = torch.load(path, map_location="cpu")

        agent = cls()
        agent.state_size = checkpoint["state_size"]
        agent.num_actions = checkpoint["num_actions"]
        agent.hidden_size = checkpoint["hidden_size"]

        device_name = device or ("cuda" if torch.cuda.is_available() else "cpu")
        agent.device = torch.device(device_name)

        agent.q_network = QNetwork(agent.state_size, agent.num_actions, agent.hidden_size).to(agent.device)
        agent.q_network.load_state_dict(checkpoint["q_network"])
        agent.q_network.eval()

        agent.epsilon = 0.0
        return agent

    @classmethod
    def load_for_finetuning(cls, path, agent_info_overrides=None, device=None):
        """
        Load a checkpoint and prepare the agent for **continued training**.

        The network architecture (state_size, num_actions, hidden_size) is
        taken from the checkpoint and cannot be overridden.  All learning
        hyperparameters can be overridden via *agent_info_overrides*.

        Sensible fine-tuning defaults (lower LR, partial exploration):
            lr                  : 1e-4
            epsilon_start       : 0.3
            epsilon_end         : 0.05
            epsilon_decay_steps : 10_000
            gamma               : 0.99
            buffer_capacity     : 50_000
            batch_size          : 64
            min_buffer_size     : 500
            target_sync_every   : 500
        """
        agent_info_overrides = agent_info_overrides or {}
        checkpoint = torch.load(path, map_location="cpu")

        agent_info = {
            "state_size": checkpoint["state_size"],
            "num_actions": checkpoint["num_actions"],
            "hidden_size": checkpoint["hidden_size"],
            "lr": agent_info_overrides.get("lr", 1e-4),
            "gamma": agent_info_overrides.get("gamma", 0.99),
            "epsilon_start": agent_info_overrides.get("epsilon_start", 0.3),
            "epsilon_end": agent_info_overrides.get("epsilon_end", 0.05),
            "epsilon_decay_steps": agent_info_overrides.get("epsilon_decay_steps", 10_000),
            "buffer_capacity": agent_info_overrides.get("buffer_capacity", 50_000),
            "batch_size": agent_info_overrides.get("batch_size", 64),
            "min_buffer_size": agent_info_overrides.get("min_buffer_size", 500),
            "target_sync_every": agent_info_overrides.get("target_sync_every", 500),
        }
        if device:
            agent_info["device"] = device

        # Initialise a fresh agent (creates networks, optimizer, buffer)
        agent = cls()
        agent.agent_init(agent_info)

        # Load pretrained weights into both q_network and target_network
        dev = agent.device
        q_state = {k: v.to(dev) for k, v in checkpoint["q_network"].items()}
        agent.q_network.load_state_dict(q_state)
        agent.target_network.load_state_dict(q_state)
        agent.target_network.eval()

        return agent