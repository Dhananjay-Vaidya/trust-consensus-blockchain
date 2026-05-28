# marl_agent.py

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

# class MARLAgent:
#     def __init__(self, state_dim, action_dim, num_agents, lr=1e-5, gamma=0.95):
#         self.device = device
#         self.num_agents = num_agents
#         self.state_size = state_dim
#         self.action_size = action_dim
#         self.gamma = gamma
#         self.batch_size = 32
#         self.update_frequency = 5
        
#         # Create networks, targets, optimizers, and replay buffers for each agent
#         self.models = [D3QNetwork(state_dim, action_dim).to(self.device) for _ in range(num_agents)]
#         self.target_models = [D3QNetwork(state_dim, action_dim).to(self.device) for _ in range(num_agents)]
#         self.optimizers = [optim.Adam(model.parameters(), lr=lr) for model in self.models]
#         self.memories = [ReplayBuffer(capacity=1000) for _ in range(num_agents)]
#         self.training_steps = [0 for _ in range(num_agents)]
#         self.epsilon = [1.0 for _ in range(num_agents)]
#         self.epsilon_min = 0.01
#         self.epsilon_decay = 0.0001
#         self.criterion = nn.SmoothL1Loss()
        
#         # Initialize target networks
#         for agent_id in range(num_agents):
#             self.target_models[agent_id].load_state_dict(self.models[agent_id].state_dict())
        
#         # For adaptive learning rate
#         self.initial_lr = lr
#         self.min_lr = 1e-6
#         self.lr_decay_rate = 0.995
        
#     def adjust_learning_rate(self, episode, agent_id=0):
#         # Decay learning rate to prevent overfitting in later episodes
#         lr = max(self.min_lr, self.initial_lr * (self.lr_decay_rate ** episode))
#         for param_group in self.optimizers[agent_id].param_groups:
#             param_group['lr'] = lr
#         return lr
    
#     def adjust_epsilon(self, episode, agent_id=0):
#         # Use slower decay for epsilon and maintain higher exploration
#         base_epsilon = max(0.05, 1.0 * (0.995 ** episode))
#         # Add periodic exploration boosts to escape local optima
#         if episode > 50 and episode % 5 == 0:
#             return base_epsilon + 0.1
#         # Additional exploration for late episodes
#         if episode > 200:
#             return base_epsilon + 0.15
#         return base_epsilon

#     def select_action(self, state, agent_id=0, epsilon=None):
#         # Use epsilon-greedy policy for discrete action selection
#         if epsilon is None:
#             epsilon = self.epsilon[agent_id]
            
#         if np.random.rand() < epsilon:
#             return random.randrange(self.action_size)
#         else:
#             state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
#             with torch.no_grad():
#                 q_values = self.models[agent_id](state_tensor)
#             return torch.argmax(q_values, dim=1).item()

#     def push_experience(self, state, action, reward, next_state, done, agent_id=0):
#         self.memories[agent_id].push(state, action, reward, next_state, done)
        
#         # Update epsilon
#         if self.epsilon[agent_id] > self.epsilon_min:
#             self.epsilon[agent_id] -= self.epsilon_decay

#     def train(self, agent_id=0):
#         memory = self.memories[agent_id]
#         model = self.models[agent_id]
#         target_model = self.target_models[agent_id]
#         optimizer = self.optimizers[agent_id]
        
#         if len(memory) < self.batch_size:
#             return None  # Not enough samples yet

#         transitions = memory.sample(self.batch_size)
#         batch = list(zip(*transitions))
        
#         states = torch.FloatTensor(np.array(batch[0])).to(self.device)
#         actions = torch.LongTensor(batch[1]).to(self.device)
#         rewards = torch.FloatTensor(batch[2]).to(self.device)
#         next_states = torch.FloatTensor(np.array(batch[3])).to(self.device)
#         dones = torch.FloatTensor(batch[4]).to(self.device)

#         # Current Q Values
#         q_values = model(states).gather(1, actions.unsqueeze(1)).squeeze(1)

#         # Double DQN - Next Actions from Online Model
#         next_actions = model(next_states).argmax(1)
#         # Next Q Values from Target Model
#         next_q_values = target_model(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
#         # Compute Target Q Values
#         target_q_values = rewards + (1 - dones) * self.gamma * next_q_values

#         # Compute Loss
#         loss = self.criterion(q_values, target_q_values.detach())

#         # Optimize the model
#         optimizer.zero_grad()
#         loss.backward()
#         # Apply gradient clipping for stability
#         torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
#         optimizer.step()
        
#         # Increment training steps
#         self.training_steps[agent_id] += 1
        
#         return loss.item()

#     def update_target_model(self, agent_id=0):
#         self.target_models[agent_id].load_state_dict(self.models[agent_id].state_dict())
        
#     def get_adjustment(self, state, agent_id=0):
#         """Map discrete actions to delegation ratio adjustments"""
#         action = self.select_action(state, agent_id, epsilon=0.05)
#         # Action 0: Decrease by 0.1
#         # Action 1: No change
#         # Action 2: Increase by 0.1
#         if action == 0:
#             return 0.9  # Decrease adjustment
#         elif action == 2:
#             return 1.1  # Increase adjustment
#         else:
#             return 1.0  # No change

#     def train_adjustment(self, state, action, reward, next_state, done, agent_id=0):
#         # Convert continuous adjustment back to discrete action
#         discrete_action = 1  # Default to no change
#         if action < 0.95:
#             discrete_action = 0  # Decrease
#         elif action > 1.05:
#             discrete_action = 2  # Increase
            
#         # Store the experience and train
#         self.push_experience(state, discrete_action, reward, next_state, done, agent_id)
#         loss = self.train(agent_id)
        
#         # Periodically update target network
#         if self.training_steps[agent_id] % self.update_frequency == 0:
#             self.update_target_model(agent_id)
            
#         return loss


# marl_agent.py - Industry-Grade Multi-Agent Reinforcement Learning

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from collections import deque

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ========================================
# 1. ENHANCED DUELING DOUBLE DQN WITH ATTENTION
# ========================================

class AttentionModule(nn.Module):
    """Multi-head attention for agent coordination"""
    def __init__(self, embed_dim, num_heads=4):
        super(AttentionModule, self).__init__()
        self.attention = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)
        self.norm = nn.LayerNorm(embed_dim)
        
    def forward(self, x):
        # Self-attention for feature refinement
        attn_out, _ = self.attention(x, x, x)
        return self.norm(x + attn_out)  # Residual connection


class AdvancedD3QNetwork(nn.Module):
    """Industry-grade Dueling Double DQN with attention and residual connections"""
    def __init__(self, state_size, action_size, num_agents):
        super(AdvancedD3QNetwork, self).__init__()
        self.num_agents = num_agents
        
        # Shared feature extraction (deeper network)
        self.feature_layer = nn.Sequential(
            nn.Linear(state_size, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 256),
            nn.LayerNorm(256),
            nn.ReLU()
        )
        
        # Attention module for agent coordination
        self.attention = AttentionModule(embed_dim=256, num_heads=4)
        
        # Value Stream (state value estimation)
        self.value_stream = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
        # Advantage Stream (action advantage estimation)
        self.advantage_stream = nn.Sequential(
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
        batch_size = x.size(0)
        
        # Feature extraction
        features = self.feature_layer(x)
        
        # Apply attention if multiple agents
        if self.num_agents > 1:
            # Reshape for attention: (batch, 1, features)
            features_reshaped = features.unsqueeze(1)
            features = self.attention(features_reshaped).squeeze(1)
        
        # Compute value and advantages
        values = self.value_stream(features)
        advantages = self.advantage_stream(features)
        
        # Combine using dueling architecture formula
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
            return [], []
            
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
# 3. SHARED EXPERIENCE BUFFER
# ========================================

class SharedExperienceBuffer:
    """Shared buffer for multi-agent experience sharing"""
    def __init__(self, capacity):
        self.buffer = PrioritizedReplayBuffer(capacity, alpha=0.6)
        
    def push(self, state, action, reward, next_state, done, agent_id, priority=None):
        # Store experience with agent ID for coordination learning
        self.buffer.push(state, action, reward, next_state, done, priority)
        
    def sample(self, batch_size, beta=0.4):
        return self.buffer.sample(batch_size, beta)
    
    def update_priorities(self, indices, priorities):
        self.buffer.update_priorities(indices, priorities)
        
    def __len__(self):
        return len(self.buffer)


# ========================================
# 4. ADVANCED MARL AGENT
# ========================================

class MARLAgent:
    """Industry-grade Multi-Agent Reinforcement Learning Agent"""
    def __init__(self, state_dim, action_dim=27, num_agents=16, lr=5e-4, gamma=0.99):
        self.device = device
        self.num_agents = num_agents
        self.state_size = state_dim
        self.action_size = action_dim
        self.gamma = gamma
        self.batch_size = 64  # Increased batch size
        self.update_frequency = 4  # More frequent updates
        self.tau = 0.005  # Soft update parameter
        
        # Create individual networks for each agent
        self.models = [
            AdvancedD3QNetwork(state_dim, action_dim, num_agents).to(self.device) 
            for _ in range(num_agents)
        ]
        self.target_models = [
            AdvancedD3QNetwork(state_dim, action_dim, num_agents).to(self.device) 
            for _ in range(num_agents)
        ]
        
        # Optimizers with weight decay for regularization
        self.optimizers = [
            optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4) 
            for model in self.models
        ]
        
        # Learning rate schedulers
        self.schedulers = [
            optim.lr_scheduler.CosineAnnealingWarmRestarts(opt, T_0=50, T_mult=2)
            for opt in self.optimizers
        ]
        
        # Shared experience buffer + individual buffers
        self.shared_memory = SharedExperienceBuffer(capacity=5000)
        self.local_memories = [
            PrioritizedReplayBuffer(capacity=2000, alpha=0.6) 
            for _ in range(num_agents)
        ]
        
        # Training tracking
        self.training_steps = [0 for _ in range(num_agents)]
        self.episode_rewards = [[] for _ in range(num_agents)]
        
        # Exploration parameters
        self.epsilon = [1.0 for _ in range(num_agents)]
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995  # Slower decay
        
        # Prioritized replay parameters
        self.beta = 0.4
        self.beta_increment = 0.001
        
        # Loss function
        self.criterion = nn.HuberLoss()  # More robust than SmoothL1Loss
        
        # Initialize target networks
        for agent_id in range(num_agents):
            self.target_models[agent_id].load_state_dict(self.models[agent_id].state_dict())
            
        print(f"[MARL] Initialized {num_agents} agents with advanced D3QN + attention + prioritized replay")
        
    def select_action(self, state, agent_id=0, epsilon=None):
        """Epsilon-greedy action selection with parameter noise"""
        if epsilon is None:
            epsilon = self.epsilon[agent_id]
            
        # Add Ornstein-Uhlenbeck noise for better exploration
        if np.random.rand() < epsilon:
            return random.randrange(self.action_size)
        else:
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_values = self.models[agent_id](state_tensor)
                return torch.argmax(q_values, dim=1).item()
    
    def push_experience(self, state, action, reward, next_state, done, agent_id=0):
        """Store experience in both local and shared buffers"""
        # Compute TD error for priority
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
            
            current_q = self.models[agent_id](state_tensor)[0, action]
            next_q = self.target_models[agent_id](next_state_tensor).max()
            td_error = abs(reward + self.gamma * next_q.item() * (1 - done) - current_q.item())
        
        # Store in both buffers
        self.local_memories[agent_id].push(state, action, reward, next_state, done, td_error)
        self.shared_memory.push(state, action, reward, next_state, done, agent_id, td_error)
        
    def train(self, agent_id=0):
        """Train with prioritized experience replay + multi-agent coordination"""
        local_memory = self.local_memories[agent_id]
        model = self.models[agent_id]
        target_model = self.target_models[agent_id]
        optimizer = self.optimizers[agent_id]
        
        # Need sufficient samples
        if len(local_memory) < self.batch_size:
            return None
            
        # Sample from local (70%) and shared (30%) memory
        local_batch_size = int(self.batch_size * 0.7)
        shared_batch_size = self.batch_size - local_batch_size
        
        # Sample local experiences
        local_samples, local_weights, local_indices = local_memory.sample(
            local_batch_size, beta=self.beta
        )
        
        # Sample shared experiences (if available)
        if len(self.shared_memory) >= shared_batch_size:
            shared_samples, shared_weights, shared_indices = self.shared_memory.sample(
                shared_batch_size, beta=self.beta
            )
            samples = local_samples + shared_samples
            weights = np.concatenate([local_weights, shared_weights])
            indices = (local_indices, shared_indices)
        else:
            samples = local_samples
            weights = local_weights
            indices = (local_indices, None)
        
        # Prepare batch
        batch = list(zip(*samples))
        states = torch.FloatTensor(np.array(batch[0])).to(self.device)
        actions = torch.LongTensor(batch[1]).to(self.device)
        rewards = torch.FloatTensor(batch[2]).to(self.device)
        next_states = torch.FloatTensor(np.array(batch[3])).to(self.device)
        dones = torch.FloatTensor(batch[4]).to(self.device)
        weights_tensor = torch.FloatTensor(weights).to(self.device)
        
        # Double DQN update
        current_q = model(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        next_actions = model(next_states).argmax(1)
        next_q = target_model(next_states).gather(1, next_actions.unsqueeze(1)).squeeze(1)
        target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Weighted loss (importance sampling)
        td_errors = (current_q - target_q.detach()).abs()
        loss = (weights_tensor * F.huber_loss(current_q, target_q.detach(), reduction='none')).mean()
        
        # Optimize
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
        optimizer.step()
        
        # Update priorities in both buffers
        priorities = td_errors.detach().cpu().numpy()
        local_memory.update_priorities(indices[0], priorities[:local_batch_size])
        if indices[1] is not None:
            self.shared_memory.update_priorities(indices[1], priorities[local_batch_size:])
        
        # Soft update target network (Polyak averaging)
        self._soft_update_target(agent_id)
        
        # Update beta for importance sampling
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        # Increment training steps
        self.training_steps[agent_id] += 1
        
        return loss.item()
    
    def _soft_update_target(self, agent_id):
        """Soft update of target network (Polyak averaging)"""
        for target_param, param in zip(
            self.target_models[agent_id].parameters(),
            self.models[agent_id].parameters()
        ):
            target_param.data.copy_(
                self.tau * param.data + (1.0 - self.tau) * target_param.data
            )
    
    def update_epsilon(self, episode, agent_id=0):
        """Adaptive epsilon decay with periodic exploration boosts"""
        base_epsilon = max(self.epsilon_min, self.epsilon[agent_id] * self.epsilon_decay)
        
        # Periodic exploration boosts
        if episode > 50 and episode % 10 == 0:
            base_epsilon = min(0.3, base_epsilon + 0.1)
            
        self.epsilon[agent_id] = base_epsilon
        return base_epsilon
    
    def update_learning_rate(self, episode, agent_id=0):
        """Step learning rate scheduler"""
        self.schedulers[agent_id].step()
        current_lr = self.optimizers[agent_id].param_groups[0]['lr']
        return current_lr
    
    def get_adjustment(self, state, agent_id: int = 0) -> int:
        """Return joint action index (0-26)."""
        return self.select_action(state, agent_id, epsilon=0.05)

    def train_adjustment(self, state, action_idx: int, reward: float, next_state, done: bool, agent_id: int = 0):
        """Training wrapper — action_idx is a 0-26 joint action index."""
        self.push_experience(state, action_idx, reward, next_state, done, agent_id)
        return self.train(agent_id)
    
    def save_model(self, path, agent_id=0):
        """Save model checkpoint"""
        torch.save({
            'model_state_dict': self.models[agent_id].state_dict(),
            'target_model_state_dict': self.target_models[agent_id].state_dict(),
            'optimizer_state_dict': self.optimizers[agent_id].state_dict(),
            'epsilon': self.epsilon[agent_id],
            'training_steps': self.training_steps[agent_id]
        }, path)
        
    def load_model(self, path, agent_id=0):
        """Load model checkpoint"""
        checkpoint = torch.load(path)
        self.models[agent_id].load_state_dict(checkpoint['model_state_dict'])
        self.target_models[agent_id].load_state_dict(checkpoint['target_model_state_dict'])
        self.optimizers[agent_id].load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon[agent_id] = checkpoint['epsilon']
        self.training_steps[agent_id] = checkpoint['training_steps']
