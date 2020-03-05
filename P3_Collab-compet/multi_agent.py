import numpy as np

import random
import copy
from collections import namedtuple, deque

import torch
import torch.nn.functional as F
import torch.optim as optim

from ddpg import DDPGAgent

BUFFER_SIZE = int(1e5)  # Replay buffer size
BATCH_SIZE = 128        # Minibatch size
GAMMA = 0.99            # Discount factor
TAU = 1e-3              # For soft update of target parameters
UPDATE_EVERY = 1        # Update the network
UPDATE_TIMES = 5        # Update the network

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class MultiAgent:
    def __init__(self, num_agents, state_size, action_size, random_seed):
        self.agents = [Agent(state_size, action_size, random_seed) for _ in range(num_agents)]

        # Replay memory
        self.memory = ReplayBuffer(action_size, BUFFER_SIZE, BATCH_SIZE, random_seed)

        # Initialize time step (for updating every UPDATE_EVERY steps)
        self.t_step = 0

    def reset(self):
        for agent in self.agents:
            agent.reset()

    def act(self, states):
        """get actions from all agents"""
        actions = [agent.act(np.expand_dims(_states, axis=0)) for agent, _states in zip(self.agents, states)]
        return actions

    def step(self, states, actions, rewards, next_states, dones):
        # Save experience in replay memory
        for state, action, reward, next_state, done in zip(states, actions, rewards, next_states, dones):
            self.memory.add(state, action, reward, next_state, done)

        # Learn every UPDATE_EVERY time steps.
        self.t_step = (self.t_step + 1) % UPDATE_EVERY
        if self.t_step == 0:
            # Learn, if enough samples are available in memory
            if len(self.memory) > BATCH_SIZE:
                for _ in range(UPDATE_TIMES):
                    for agent in self.agents:
                        experiences = self.memory.sample()
                        agent.learn(experiences, GAMMA, TAU)


class ReplayBuffer:
    """Fixed-size buffer to store experience tuples."""

    def __init__(self, action_size, buffer_size, batch_size, seed):
        """Initialize a ReplayBuffer object.
        Params
        ======
            buffer_size (int): maximum size of buffer
            batch_size (int): size of each training batch
        """
        self.action_size = action_size
        self.memory = deque(maxlen=buffer_size)  # internal memory (deque)
        self.batch_size = batch_size
        self.experience = namedtuple("Experience", field_names=["state", "action", "reward", "next_state", "done"])
        self.seed = random.seed(seed)

    def add(self, state, action, reward, next_state, done):
        """Add a new experience to memory."""
        e = self.experience(state, action, reward, next_state, done)
        self.memory.append(e)

    def sample(self):
        """Randomly sample a batch of experiences from memory."""
        experiences = random.sample(self.memory, k=self.batch_size)

        states = torch.from_numpy(np.vstack([e.state for e in experiences if e is not None])).float().to(device)
        actions = torch.from_numpy(np.vstack([e.action for e in experiences if e is not None])).float().to(device)
        rewards = torch.from_numpy(np.vstack([e.reward for e in experiences if e is not None])).float().to(device)
        next_states = torch.from_numpy(np.vstack([e.next_state for e in experiences if e is not None])).float().to(device)
        dones = torch.from_numpy(np.vstack([e.done for e in experiences if e is not None]).astype(np.uint8)).float().to(device)

        return (states, actions, rewards, next_states, dones)

    def __len__(self):
        """Return the current size of internal memory."""
        return len(self.memory)
