# Security Model

The project studies trust-aware blockchain-IoT consensus under multiple adversarial behaviors.

## Defensive Components

- `ABAC`: policy-aware transaction filtering
- `FHE`: optional encrypted trust-policy evaluation path
- `TrustManager`: Bayesian trust estimation and delegation support
- `TDCB`: trust-weighted delegated consensus with Byzantine detection
- RL agents: adapt delegation behavior during training

## Attack Families

- `NMA`: naive malicious / noise manipulation
- `CRA`: collusive reputation attack
- `AAA`: adaptive adversarial attack
- `BFI`: Byzantine fault injection
- `TDP`: time-delayed poisoning / sleeper-agent attack

## Evaluation Objectives

- malicious-node detection quality
- trust separation between honest and malicious nodes
- consensus robustness
- throughput and blockchain growth
- resilience under different malicious fractions and scenario settings
