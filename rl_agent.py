# import torch
# import torch.nn as nn
# import torch.optim as optim
# import torch.nn.functional as F
# import numpy as np
# import random
# from collections import deque

# # Select device (CPU or GPU)
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# class D3QNetwork(nn.Module):
#     def __init__(self, state_size, action_size):
#         super(D3QNetwork, self).__init__()
#         self.feature_layer = nn.Sequential(
#             nn.Linear(state_size, 128),
#             nn.ReLU()
#         )
#         # Value Stream
#         self.value_layer = nn.Sequential(
#             nn.Linear(128, 64),
#             nn.ReLU(),
#             nn.Linear(64, 1)
#         )
#         # Advantage Stream
#         self.advantage_layer = nn.Sequential(
#             nn.Linear(128, 64),
#             nn.ReLU(),
#             nn.Linear(64, action_size)
#         )
        
#         # Apply weight initialization for better training dynamics
#         self._initialize_weights()
    
#     def _initialize_weights(self):
#         for m in self.modules():
#             if isinstance(m, nn.Linear):
#                 nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
#                 if m.bias is not None:
#                     nn.init.constant_(m.bias, 0)

#     def forward(self, x):
#         features = self.feature_layer(x)
#         values = self.value_layer(features)
#         advantages = self.advantage_layer(features)
#         qvals = values + (advantages - advantages.mean(dim=1, keepdim=True))
#         return qvals

# class ReplayBuffer:
#     def __init__(self, capacity):
#         self.capacity = capacity
#         self.buffer = []
#         self.pos = 0

#     def push(self, state, action, reward, next_state, done):
#         if len(self.buffer) < self.capacity:
#             self.buffer.append((state, action, reward, next_state, done))
#         else:
#             self.buffer[self.pos] = (state, action, reward, next_state, done)
#         self.pos = (self.pos + 1) % self.capacity

#     def sample(self, batch_size):
#         return random.sample(self.buffer, batch_size)

#     def __len__(self):
#         return len(self.buffer)

# class RLAgent:
#     def __init__(self, state_dim, action_dim, lr=1e-5, gamma=0.95):
#         self.device = device
#         self.state_size = state_dim
#         self.action_size = action_dim
#         self.gamma = gamma
#         self.epsilon = 1.0
#         self.epsilon_min = 0.01
#         self.epsilon_decay = 0.0001
#         self.batch_size = 32
#         self.update_frequency = 5
#         self.training_steps = 0
        
#         self.model = D3QNetwork(state_dim, action_dim).to(self.device)
#         self.target_model = D3QNetwork(state_dim, action_dim).to(self.device)
#         self.target_model.load_state_dict(self.model.state_dict())
#         self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
#         self.criterion = nn.SmoothL1Loss()
        
#         self.memory = ReplayBuffer(capacity=1000)
        
#         # For adaptive learning rate
#         self.initial_lr = lr
#         self.min_lr = 1e-6
#         self.lr_decay_rate = 0.995
        
#     def adjust_learning_rate(self, episode):
#         # Decay learning rate to prevent overfitting in later episodes
#         lr = max(self.min_lr, self.initial_lr * (self.lr_decay_rate ** episode))
#         for param_group in self.optimizer.param_groups:
#             param_group['lr'] = lr
#         return lr
    
#     def adjust_epsilon(self, episode):
#         # Use slower decay for epsilon and maintain higher exploration
#         base_epsilon = max(0.05, 1.0 * (0.995 ** episode))
#         # Add periodic exploration boosts to escape local optima
#         if episode > 50 and episode % 5 == 0:
#             return base_epsilon + 0.1
#         # Additional exploration for late episodes
#         if episode > 200:
#             return base_epsilon + 0.15
#         return base_epsilon

#     def select_action(self, state, epsilon=None):
#         # Use epsilon-greedy policy for discrete action selection
#         if epsilon is None:
#             epsilon = self.epsilon
            
#         if np.random.rand() < epsilon:
#             return random.randrange(self.action_size)
#         else:
#             state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
#             with torch.no_grad():
#                 q_values = self.model(state_tensor)
#             return torch.argmax(q_values, dim=1).item()

#     def push_experience(self, state, action, reward, next_state, done):
#         self.memory.push(state, action, reward, next_state, done)
        
#         # Update epsilon
#         if self.epsilon > self.epsilon_min:
#             self.epsilon -= self.epsilon_decay

#     def train(self):
#         if len(self.memory) < self.batch_size:
#             return None  # Not enough samples yet

#         transitions = self.memory.sample(self.batch_size)
#         batch = list(zip(*transitions))
        
#         states = torch.FloatTensor(np.array(batch[0])).to(self.device)
#         actions = torch.LongTensor(batch[1]).to(self.device)
#         rewards = torch.FloatTensor(batch[2]).to(self.device)
#         next_states = torch.FloatTensor(np.array(batch[3])).to(self.device)
#         dones = torch.FloatTensor(batch[4]).to(self.device)

#         # Current Q Values
#         q_values = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)

#         # Double DQN - Next Actions from Online Model
#         next_actions = self.model(next_states).argmax(1)
#         # Next Q Values from Target Model
#         next_q_values = self.target_model(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
#         # Compute Target Q Values
#         target_q_values = rewards + (1 - dones) * self.gamma * next_q_values

#         # Compute Loss
#         loss = self.criterion(q_values, target_q_values.detach())

#         # Optimize the model
#         self.optimizer.zero_grad()
#         loss.backward()
#         # Apply gradient clipping for stability
#         torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
#         self.optimizer.step()
        
#         # Increment training steps
#         self.training_steps += 1
        
#         return loss.item()

#     def update_target_model(self):
#         self.target_model.load_state_dict(self.model.state_dict())
        
#     def get_adjustment(self, state):
#         """Map discrete actions to delegation ratio adjustments"""
#         action = self.select_action(state, epsilon=0.05)
#         # Action 0: Decrease by 0.1
#         # Action 1: No change
#         # Action 2: Increase by 0.1
#         if action == 0:
#             return 0.9  # Decrease adjustment
#         elif action == 2:
#             return 1.1  # Increase adjustment
#         else:
#             return 1.0  # No change

#     def train_adjustment(self, state, action, reward, next_state, done):
#         # Convert continuous adjustment back to discrete action
#         discrete_action = 1  # Default to no change
#         if action < 0.95:
#             discrete_action = 0  # Decrease
#         elif action > 1.05:
#             discrete_action = 2  # Increase
            
#         # Store the experience and train
#         self.push_experience(state, discrete_action, reward, next_state, done)
#         loss = self.train()
        
#         # Periodically update target network
#         if self.training_steps % self.update_frequency == 0:
#             self.update_target_model()
            
#         return loss

# rl_agent.py - Industry-Grade Reinforcement Learning Agent

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from collections import deque

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ========================================
# 1. ENHANCED DUELING DOUBLE DQN
# ========================================

class EnhancedD3QNetwork(nn.Module):
    """Industry-grade Dueling Double DQN with deeper architecture"""
    def __init__(self, state_size, action_size):
        super(EnhancedD3QNetwork, self).__init__()
        
        # Deeper feature extraction (upgraded from 128)
        self.feature_layer = nn.Sequential(
            nn.Linear(state_size, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 256),
            nn.LayerNorm(256),
            nn.ReLU()
        )
        
        # Enhanced Value Stream (state value estimation)
        self.value_layer = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        # Enhanced Advantage Stream (action advantage estimation)
        self.advantage_layer = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_size)
        )
        
        # Initialize weights with He initialization
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
        
        # Dueling architecture formula
        q_values = values + (advantages - advantages.mean(dim=1, keepdim=True))
        return q_values


# ========================================
# 2. PRIORITIZED EXPERIENCE REPLAY
# ========================================

class PrioritizedReplayBuffer:
    """Prioritized Experience Replay for better sample efficiency"""
    def __init__(self, capacity, alpha=0.6):
        self.capacity = capacity
        self.alpha = alpha  # Priority exponent
        self.buffer = []
        self.priorities = []
        self.pos = 0
        
    def push(self, state, action, reward, next_state, done, priority=None):
        if priority is None:
            priority = max(self.priorities) if self.priorities else 1.0
            
        if len(self.buffer) < self.capacity:
            self.buffer.append((state, action, reward, next_state, done))
            self.priorities.append(priority)
        else:
            self.buffer[self.pos] = (state, action, reward, next_state, done)
            self.priorities[self.pos] = priority
            
        self.pos = (self.pos + 1) % self.capacity
        
    def sample(self, batch_size, beta=0.4):
        """Sample with prioritization and compute importance sampling weights"""
        if len(self.buffer) == 0:
            return [], [], []
            
        # Convert priorities to probabilities
        priorities = np.array(self.priorities[:len(self.buffer)])
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        # Sample indices based on priorities
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        
        # Compute importance sampling weights
        weights = (len(self.buffer) * probabilities[indices]) ** (-beta)
        weights /= weights.max()  # Normalize weights
        
        samples = [self.buffer[idx] for idx in indices]
        return samples, weights, indices
    
    def update_priorities(self, indices, priorities):
        """Update priorities based on TD error"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority + 1e-5  # Small constant to avoid zero priority
            
    def __len__(self):
        return len(self.buffer)


# ========================================
# 3. ENHANCED RL AGENT
# ========================================

class RLAgent:
    """Industry-grade Reinforcement Learning Agent with prioritized replay"""
    def __init__(self, state_dim, action_dim=27, lr=5e-4, gamma=0.99):
        self.device = device
        self.state_size = state_dim
        self.action_size = action_dim
        self.gamma = gamma
        self.batch_size = 64  # Increased from 32
        self.update_frequency = 4  # More frequent updates
        self.tau = 0.005  # Soft update parameter
        self.training_steps = 0
        
        # Enhanced networks
        self.model = EnhancedD3QNetwork(state_dim, action_dim).to(self.device)
        self.target_model = EnhancedD3QNetwork(state_dim, action_dim).to(self.device)
        self.target_model.load_state_dict(self.model.state_dict())
        
        # Optimizer with weight decay for regularization
        self.optimizer = optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-4)
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
            self.optimizer, T_0=50, T_mult=2
        )
        
        # Prioritized experience replay
        self.memory = PrioritizedReplayBuffer(capacity=10000, alpha=0.6)
        
        # Exploration parameters
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995  # Slower decay
        
        # Prioritized replay parameters
        self.beta = 0.4
        self.beta_increment = 0.001
        
        # Loss function
        self.criterion = nn.HuberLoss()  # More robust than SmoothL1Loss
        
        # Initial learning rate
        self.initial_lr = lr
        self.min_lr = 1e-6
        
        print(f"[RL] Initialized Enhanced RL Agent with D3QN + prioritized replay")
        
    def adjust_learning_rate(self, episode):
        """Step learning rate scheduler"""
        self.scheduler.step()
        current_lr = self.optimizer.param_groups[0]['lr']
        return current_lr
        
    def adjust_epsilon(self, episode):
        """Adaptive epsilon decay with periodic exploration boosts"""
        base_epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Periodic exploration boosts
        if episode > 50 and episode % 10 == 0:
            base_epsilon = min(0.3, base_epsilon + 0.1)
            
        self.epsilon = base_epsilon
        return base_epsilon
        
    def select_action(self, state, epsilon=None):
        """Epsilon-greedy action selection"""
        if epsilon is None:
            epsilon = self.epsilon
            
        if np.random.rand() < epsilon:
            return random.randrange(self.action_size)
        else:
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_values = self.model(state_tensor)
                return torch.argmax(q_values, dim=1).item()
    
    def push_experience(self, state, action, reward, next_state, done):
        """Store experience with computed priority"""
        # Compute TD error for priority
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
            
            current_q = self.model(state_tensor)[0, action]
            next_q = self.target_model(next_state_tensor).max()
            td_error = abs(reward + self.gamma * next_q.item() * (1 - done) - current_q.item())
        
        self.memory.push(state, action, reward, next_state, done, td_error)
    
    def train(self):
        """Train with prioritized experience replay"""
        if len(self.memory) < self.batch_size:
            return None
            
        # Sample from prioritized replay buffer
        samples, weights, indices = self.memory.sample(self.batch_size, beta=self.beta)
        
        if not samples:
            return None
            
        # Prepare batch
        batch = list(zip(*samples))
        states = torch.FloatTensor(np.array(batch[0])).to(self.device)
        actions = torch.LongTensor(batch[1]).to(self.device)
        rewards = torch.FloatTensor(batch[2]).to(self.device)
        next_states = torch.FloatTensor(np.array(batch[3])).to(self.device)
        dones = torch.FloatTensor(batch[4]).to(self.device)
        weights_tensor = torch.FloatTensor(weights).to(self.device)
        
        # Double DQN update
        current_q = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        next_actions = self.model(next_states).argmax(1)
        next_q = self.target_model(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
        target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Weighted loss (importance sampling)
        td_errors = (current_q - target_q.detach()).abs()
        loss = (weights_tensor * F.huber_loss(current_q, target_q.detach(), reduction='none')).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=10.0)
        self.optimizer.step()
        
        # Update priorities
        priorities = td_errors.detach().cpu().numpy()
        self.memory.update_priorities(indices, priorities)
        
        # Soft update target network (Polyak averaging)
        self._soft_update_target()
        
        # Update beta for importance sampling
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        # Increment training steps
        self.training_steps += 1
        
        return loss.item()
    
    def _soft_update_target(self):
        """Soft update of target network (Polyak averaging)"""
        for target_param, param in zip(self.target_model.parameters(), self.model.parameters()):
            target_param.data.copy_(
                self.tau * param.data + (1.0 - self.tau) * target_param.data
            )
    
    def update_target_model(self):
        """Hard update for compatibility (not used with soft updates)"""
        self.target_model.load_state_dict(self.model.state_dict())
    
    def get_adjustment(self, state):
        """Return action index (0-26) for the expanded action space."""
        return self.select_action(state, epsilon=0.05)

    def train_adjustment(self, state, action_idx, reward, next_state, done):
        """Training wrapper — action_idx is already a discrete 0-26 index."""
        self.push_experience(state, action_idx, reward, next_state, done)
        return self.train()
    
    def save_model(self, path):
        """Save model checkpoint"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'target_model_state_dict': self.target_model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'training_steps': self.training_steps
        }, path)
        
    def load_model(self, path):
        """Load model checkpoint"""
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.target_model.load_state_dict(checkpoint['target_model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.training_steps = checkpoint['training_steps']
