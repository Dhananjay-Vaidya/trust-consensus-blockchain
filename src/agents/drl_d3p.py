import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from collections import deque

# Select device (CPU or GPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class D3QNetwork(nn.Module):
    def __init__(self, state_size, action_size, use_noisy=True):
        super(D3QNetwork, self).__init__()
        self.use_noisy = use_noisy
        
        # Shared feature extraction with BatchNorm
        self.feature_layer = nn.Sequential(
            nn.Linear(state_size, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU()
        )
        
        # Value Stream (deeper for better state value estimation)
        if use_noisy:
            self.value_layer = nn.Sequential(
                NoisyLinear(128, 128),
                nn.ReLU(),
                NoisyLinear(128, 64),
                nn.ReLU(),
                NoisyLinear(64, 1)
            )
            
            # Advantage Stream
            self.advantage_layer = nn.Sequential(
                NoisyLinear(128, 128),
                nn.ReLU(),
                NoisyLinear(128, 64),
                nn.ReLU(),
                NoisyLinear(64, action_size)
            )
        else:
            self.value_layer = nn.Sequential(
                nn.Linear(128, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, 1)
            )
            
            self.advantage_layer = nn.Sequential(
                nn.Linear(128, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, action_size)
            )
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        features = self.feature_layer(x)
        values = self.value_layer(features)
        advantages = self.advantage_layer(features)
        
        # Dueling aggregation with mean subtraction
        qvals = values + (advantages - advantages.mean(dim=1, keepdim=True))
        return qvals
    
    def reset_noise(self):
        """Reset noise for NoisyLinear layers"""
        if self.use_noisy:
            for module in self.modules():
                if isinstance(module, NoisyLinear):
                    module.reset_noise()

class PrioritizedReplayBuffer:
    def __init__(self, capacity, alpha=0.7, n_step=1, gamma=0.95):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = 0.3
        self.beta_increment = 0.0001  # Adjust as needed
        self.buffer = []
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.pos = 0
        self.n_step = n_step
        self.gamma = gamma
        self.n_step_buffer = deque(maxlen=n_step)

    def add(self, td_error, experience):
        self.n_step_buffer.append(experience)
        if len(self.n_step_buffer) < self.n_step:
            return
        reward, next_state, done = self._get_n_step_info()
        state, action = self.n_step_buffer[0][:2]
        n_step_experience = (state, action, reward, next_state, done)

        max_prio = self.priorities.max() if self.buffer else 1.0
        if len(self.buffer) < self.capacity:
            self.buffer.append(n_step_experience)
        else:
            self.buffer[self.pos] = n_step_experience
        self.priorities[self.pos] = max(abs(td_error), max_prio) ** self.alpha
        self.pos = (self.pos + 1) % self.capacity

    def _get_n_step_info(self):
        reward, next_state, done = self.n_step_buffer[-1][2:]
        for transition in reversed(list(self.n_step_buffer)[:-1]):
            r, next_s, d = transition[2:]
            reward = r + self.gamma * reward * (1 - d)
            next_state, done = (next_s, d) if d else (next_state, done)
        return reward, next_state, done

    def sample(self, batch_size):
        if len(self.buffer) == self.capacity:
            prios = self.priorities
        else:
            prios = self.priorities[:len(self.buffer)]
        probs = prios / prios.sum()
        self.beta = min(1.0, self.beta + self.beta_increment)
        indices = np.random.choice(len(self.buffer), batch_size, p=probs)
        experiences = [self.buffer[idx] for idx in indices]
        total = len(self.buffer)
        weights = (total * probs[indices]) ** (-self.beta)
        weights /= weights.max()
        return experiences, indices, weights

    def update_priorities(self, indices, td_errors):
        for idx, td_error in zip(indices, td_errors):
            self.priorities[idx] = abs(td_error) ** self.alpha
            
    def __len__(self):
        return len(self.buffer)

class NoisyLinear(nn.Module):
    """Noisy Linear Layer for better exploration"""
    def __init__(self, in_features, out_features, sigma_init=0.5):
        super(NoisyLinear, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.sigma_init = sigma_init
        
        # Learnable parameters
        self.weight_mu = nn.Parameter(torch.FloatTensor(out_features, in_features))
        self.weight_sigma = nn.Parameter(torch.FloatTensor(out_features, in_features))
        self.bias_mu = nn.Parameter(torch.FloatTensor(out_features))
        self.bias_sigma = nn.Parameter(torch.FloatTensor(out_features))
        
        # Factorized noise
        self.register_buffer('weight_epsilon', torch.FloatTensor(out_features, in_features))
        self.register_buffer('bias_epsilon', torch.FloatTensor(out_features))
        
        self.reset_parameters()
        self.reset_noise()
    
    def reset_parameters(self):
        mu_range = 1 / np.sqrt(self.in_features)
        self.weight_mu.data.uniform_(-mu_range, mu_range)
        self.bias_mu.data.uniform_(-mu_range, mu_range)
        
        self.weight_sigma.data.fill_(self.sigma_init / np.sqrt(self.in_features))
        self.bias_sigma.data.fill_(self.sigma_init / np.sqrt(self.out_features))
    
    def reset_noise(self):
        epsilon_in = self._scale_noise(self.in_features)
        epsilon_out = self._scale_noise(self.out_features)
        self.weight_epsilon.copy_(epsilon_out.outer(epsilon_in))
        self.bias_epsilon.copy_(epsilon_out)
    
    def _scale_noise(self, size):
        x = torch.randn(size)
        return x.sign().mul(x.abs().sqrt())
    
    def forward(self, x):
        if self.training:
            weight = self.weight_mu + self.weight_sigma * self.weight_epsilon
            bias = self.bias_mu + self.bias_sigma * self.bias_epsilon
        else:
            weight = self.weight_mu
            bias = self.bias_mu
        return F.linear(x, weight, bias)

class DDQN:
    def __init__(self, state_dim, action_dim=27, lr=1e-5, gamma=0.95, buffer_capacity=10000):
        self.device = device
        self.state_size = state_dim
        self.action_size = action_dim
        self.gamma = gamma
        self.epsilon = 1.0
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.998
        self.batch_size = 256
        self.update_frequency = 5
        self.training_steps = 0
        self.simulate_cra = False
        self.warmup_episodes = 50
        self.episode_count = 0
        
        self.model = D3QNetwork(state_dim, action_dim).to(self.device)
        self.target_model = D3QNetwork(state_dim, action_dim).to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.SmoothL1Loss()
        
        self.memory = PrioritizedReplayBuffer(capacity=buffer_capacity, alpha=0.7)
        
        # For adaptive learning rate
        self.initial_lr = lr
        self.min_lr = 1e-5
        self.lr_decay_rate = 0.999

    def adjust_learning_rate(self, episode):
        lr = max(self.min_lr, self.initial_lr * (self.lr_decay_rate ** episode))
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr
        return lr
    
    def step_scheduler(self):
        """
        Step the learning rate scheduler after each episode.
        Uses cosine annealing with warm restarts for better exploration.
        
        Returns:
            float: Current learning rate
        """
        # Manual step decay (already implemented in adjust_learning_rate)
        # But can be enhanced with PyTorch scheduler
        current_lr = self.optimizer.param_groups[0]['lr']
        return current_lr

    def get_training_stats(self):
        """
        Get current training statistics for logging and monitoring.
        
        Returns:
            dict: Training statistics
        """
        return {
            'epsilon': self.epsilon,
            'learning_rate': self.optimizer.param_groups[0]['lr'],
            'buffer_size': len(self.memory),
            'training_steps': self.training_steps,
            'beta': self.memory.beta if hasattr(self.memory, 'beta') else 0.0
        }

    def get_adaptive_epsilon(self):
        """
        Adaptive epsilon with warmup period.
        Maintains high exploration early, then gradually decays.
        """
        if self.episode_count < self.warmup_episodes:
            # Keep epsilon high during warmup
            return max(0.5, self.epsilon)
        else:
            # Normal decay after warmup
            return max(self.epsilon_min, self.epsilon)

    def step_episode(self):
        """Call this at the end of each episode."""
        self.episode_count += 1
        if self.episode_count >= self.warmup_episodes:
            self.epsilon *= self.epsilon_decay

    def enable_cra_simulation(self):
        self.simulate_cra = True

    def disable_cra_simulation(self):
        self.simulate_cra = False

    def select_action(self, state) -> int:
        """Epsilon-greedy selection over 27-action joint space."""
        if random.random() < self.epsilon:
            return random.randrange(self.action_size)
        state_tensor = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        return self.model(state_tensor).argmax().item()

    def get_adjustment(self, state) -> int:
        """Return joint action index (0-26)."""
        if self.simulate_cra:
            return 2  # Index for (dr=1.1, td=1.0, ct=0.0) — boost trust
        return self.select_action(state)

    def train_adjustment(self, state, action_idx: int, reward: float, next_state, done: bool):
        """Train on a (state, action_idx, reward, next_state, done) tuple."""
        with torch.no_grad():
            state_tensor = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            next_state_tensor = torch.tensor(next_state, dtype=torch.float32, device=self.device).unsqueeze(0)
            current_q_estimate = self.model(state_tensor)[0, action_idx]
            next_action = self.model(next_state_tensor).argmax(1).item()
            next_q = self.target_model(next_state_tensor)[0, next_action]
            target = reward + (1 - done) * self.gamma * next_q
            td_error = abs(target.item() - current_q_estimate.item())

        self.memory.add(td_error, (state, action_idx, reward, next_state, done))

        if len(self.memory) < self.batch_size:
            return None

        experiences, indices, weights = self.memory.sample(self.batch_size)

        states = torch.tensor(np.array([exp[0] for exp in experiences]), dtype=torch.float32, device=self.device)
        actions = torch.tensor(np.array([exp[1] for exp in experiences]), dtype=torch.long, device=self.device)
        rewards = torch.tensor(np.array([exp[2] for exp in experiences]), dtype=torch.float32, device=self.device)
        next_states = torch.tensor(np.array([exp[3] for exp in experiences]), dtype=torch.float32, device=self.device)
        dones = torch.tensor(np.array([exp[4] for exp in experiences]), dtype=torch.float32, device=self.device)

        current_q = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_actions = self.model(next_states).argmax(1)
            next_q_values = self.target_model(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
            target_q = rewards + (1 - dones) * self.gamma * next_q_values

        td_errors = (target_q - current_q).detach()
        weights_tensor = torch.tensor(weights, dtype=torch.float32, device=self.device)
        loss = F.smooth_l1_loss(current_q, target_q, reduction='none')
        weighted_loss = (loss * weights_tensor).mean()

        self.optimizer.zero_grad()
        weighted_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=10.0)
        self.optimizer.step()

        self.memory.update_priorities(indices, td_errors.cpu().numpy())
        self.model.reset_noise()
        self.target_model.reset_noise()

        self.training_steps += 1
        if self.training_steps % self.update_frequency == 0:
            self.target_model.load_state_dict(self.model.state_dict())

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        return weighted_loss.item()

