from __future__ import annotations

# abac.py - Attribute-Based Access Control with FHE Integration

import time
from collections import defaultdict
from typing import Any, Dict, Optional, Set, Tuple

import numpy as np
from dataclasses import dataclass


@dataclass
class AttributePolicy:
    """Policy definition for attribute-based access control."""
    required_attributes: Set[str]
    allowed_actions: Set[str]
    time_restrictions: Optional[Dict[str, tuple]]
    location_restrictions: Optional[Set[str]]


class ABAC:
    """
    Attribute-Based Access Control (ABAC) with trust integration.
    """

    def __init__(self, fhe_enabled: bool = False) -> None:
        self.policies: Dict[str, AttributePolicy] = {}
        self.user_attributes: Dict[str, Set[str]] = {}
        self.fhe_enabled: bool = fhe_enabled
        self._init_default_policies()

        self.access_history: list = []
        self.policy_confidence: Dict[str, float] = defaultdict(lambda: 1.0)
        self.learning_rate: float = 0.1
        self.trust_threshold: float = 0.5

        self.total_requests: int = 0
        self.granted_requests: int = 0
        self.denied_requests: int = 0

        self._fhe: Optional[Any] = None

    def _init_default_policies(self) -> None:
        self.policies["admin"] = AttributePolicy(
            required_attributes={"admin_role", "security_clearance"},
            allowed_actions={"read", "write", "execute", "modify"},
            time_restrictions={"weekday": (0, 24), "weekend": (9, 17)},
            location_restrictions={"secure_location", "headquarters"},
        )
        self.policies["user"] = AttributePolicy(
            required_attributes={"user_role"},
            allowed_actions={"read", "write"},
            time_restrictions={"weekday": (9, 17), "weekend": None},
            location_restrictions=None,
        )
        self.policies["guest"] = AttributePolicy(
            required_attributes={"guest_role"},
            allowed_actions={"read"},
            time_restrictions={"weekday": (9, 17), "weekend": (10, 16)},
            location_restrictions=None,
        )

    def _get_fhe(self) -> Optional[Any]:
        if self._fhe is None and self.fhe_enabled:
            try:
                from src.abac.fhe import FullyHomomorphicEncryption
                self._fhe = FullyHomomorphicEncryption(use_real_fhe=True)
            except ImportError:
                from src.utils.logger import get_logger
                get_logger(__name__).warning("FHE module not available, using plaintext")
                self.fhe_enabled = False
        return self._fhe

    def add_user_attributes(self, user_id: str, attributes: Set[str]) -> None:
        self.user_attributes[user_id] = attributes

    def check_attribute_requirements(self, user_id: str, policy: AttributePolicy) -> bool:
        user_attrs = self.user_attributes.get(user_id, set())
        return policy.required_attributes.issubset(user_attrs)

    def check_time_restrictions(
        self, policy: AttributePolicy, time_of_day: int, day_type: str
    ) -> bool:
        if policy.time_restrictions is None:
            return True
        time_range = policy.time_restrictions.get(day_type)
        if time_range is None:
            return False
        start_hour, end_hour = time_range
        return start_hour <= time_of_day < end_hour

    def check_location_restrictions(self, policy: AttributePolicy, location: str) -> bool:
        if policy.location_restrictions is None:
            return True
        return location in policy.location_restrictions

    def enforce_policy(
        self,
        user_id: str,
        requested_action: str,
        time_of_day: int,
        day_type: str,
        location: str,
    ) -> bool:
        for policy_name, policy in self.policies.items():
            if not self.check_attribute_requirements(user_id, policy):
                continue
            if requested_action not in policy.allowed_actions:
                continue
            if not self.check_time_restrictions(policy, time_of_day, day_type):
                continue
            if not self.check_location_restrictions(policy, location):
                continue
            return True
        return False

    def enforce_policy_with_fhe(
        self,
        user_id: str,
        requested_action: str,
        time_of_day: int,
        day_type: str,
        location: str,
        trust_score: float = 1.0,
    ) -> Tuple[bool, float, str]:
        fhe = self._get_fhe()
        if fhe is None or not self.fhe_enabled:
            return self.enforce_policy_with_learning(
                user_id, requested_action, time_of_day, day_type, location, trust_score
            )

        encrypted_trust = fhe.encrypt_value(trust_score)
        trust_check_result = fhe.compute_encrypted_comparison(encrypted_trust, self.trust_threshold)
        trust_passed = fhe.decrypt_value(trust_check_result) > 0.5

        base_decision = self.enforce_policy(user_id, requested_action, time_of_day, day_type, location)
        final_decision = base_decision and trust_passed
        confidence = trust_score if trust_passed else (1.0 - trust_score)

        self.total_requests += 1
        if final_decision:
            reason = "FHE-verified: policy and trust checks passed"
            self.granted_requests += 1
        else:
            if not base_decision:
                reason = "FHE-verified: policy restrictions not met"
            else:
                reason = f"FHE-verified: trust below threshold ({trust_score:.2f})"
            self.denied_requests += 1

        return final_decision, confidence, reason

    def enforce_policy_with_learning(
        self,
        user_id: str,
        requested_action: str,
        time_of_day: int,
        day_type: str,
        location: str,
        trust_score: float = 1.0,
    ) -> Tuple[bool, float, str]:
        self.total_requests += 1

        base_decision = self.enforce_policy(user_id, requested_action, time_of_day, day_type, location)
        final_decision = base_decision
        confidence = 0.5
        reason = "No matching policy"

        if base_decision:
            if trust_score >= self.trust_threshold:
                final_decision = True
                confidence = min(1.0, trust_score + 0.2)
                reason = "Policy and trust verified"
                self.granted_requests += 1
            else:
                final_decision = False
                confidence = 0.9
                reason = f"Low trust ({trust_score:.2f} < {self.trust_threshold})"
                self.denied_requests += 1
        else:
            final_decision = False
            confidence = 0.8
            reason = "Policy restrictions not met"
            self.denied_requests += 1

        context: Dict[str, Any] = {
            "time": time_of_day,
            "day": day_type,
            "location": location,
            "trust": trust_score,
            "action": requested_action,
        }
        self.access_history.append({
            "user": user_id,
            "action": requested_action,
            "context": context,
            "decision": final_decision,
            "reason": reason,
            "timestamp": time.time(),
        })

        return final_decision, confidence, reason

    def learn_from_feedback(self, user_id: str, action: str, was_correct: bool) -> None:
        user_attrs = self.user_attributes.get(user_id, set())
        for policy_name, policy in self.policies.items():
            if policy.required_attributes.issubset(user_attrs):
                if was_correct:
                    self.policy_confidence[policy_name] += self.learning_rate
                else:
                    self.policy_confidence[policy_name] -= self.learning_rate
                self.policy_confidence[policy_name] = float(
                    np.clip(self.policy_confidence[policy_name], 0.0, 2.0)
                )
                break

    def adjust_trust_threshold(self, new_threshold: float) -> None:
        self.trust_threshold = float(np.clip(new_threshold, 0.0, 1.0))

    def get_policy_effectiveness(self) -> Dict[str, Any]:
        if self.total_requests == 0:
            return {
                "total_requests": 0,
                "granted_ratio": 0.0,
                "denied_ratio": 0.0,
                "policy_confidences": {},
                "trust_threshold": self.trust_threshold,
            }
        return {
            "total_requests": self.total_requests,
            "granted_count": self.granted_requests,
            "denied_count": self.denied_requests,
            "granted_ratio": self.granted_requests / self.total_requests,
            "denied_ratio": self.denied_requests / self.total_requests,
            "policy_confidences": dict(self.policy_confidence),
            "trust_threshold": self.trust_threshold,
        }

    def reset_statistics(self) -> None:
        self.access_history = []
        self.policy_confidence = defaultdict(lambda: 1.0)
        self.total_requests = 0
        self.granted_requests = 0
        self.denied_requests = 0
