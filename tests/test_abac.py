from __future__ import annotations

import pytest
from abac import ABAC


@pytest.fixture
def abac():
    a = ABAC()
    a.add_user_attributes("admin_user", {"admin_role", "security_clearance"})
    a.add_user_attributes("plain_user", {"user_role"})
    a.add_user_attributes("no_attr_user", set())
    return a


def test_admin_passes_enforce_policy(abac):
    result = abac.enforce_policy(
        user_id="admin_user",
        requested_action="write",
        time_of_day=10,
        day_type="weekday",
        location="secure_location",
    )
    assert result is True


def test_missing_attribute_fails_enforce_policy(abac):
    result = abac.enforce_policy(
        user_id="no_attr_user",
        requested_action="write",
        time_of_day=10,
        day_type="weekday",
        location="secure_location",
    )
    assert result is False


def test_enforce_policy_with_learning_updates_statistics(abac):
    before_total = abac.total_requests
    abac.enforce_policy_with_learning(
        user_id="admin_user",
        requested_action="write",
        time_of_day=10,
        day_type="weekday",
        location="secure_location",
        trust_score=0.9,
    )
    assert abac.total_requests == before_total + 1


def test_low_trust_denies_even_with_valid_policy(abac):
    decision, _, reason = abac.enforce_policy_with_learning(
        user_id="admin_user",
        requested_action="write",
        time_of_day=10,
        day_type="weekday",
        location="secure_location",
        trust_score=0.1,  # Below threshold
    )
    assert decision is False
    assert "trust" in reason.lower()


def test_plain_user_write_allowed_in_business_hours(abac):
    result = abac.enforce_policy(
        user_id="plain_user",
        requested_action="write",
        time_of_day=12,
        day_type="weekday",
        location="anywhere",
    )
    assert result is True
