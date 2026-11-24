import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import baipiao_daily


class FakeResponse:
    def __init__(self, payload=None, *, status_code=200, text=None):
        self.status_code = status_code
        self.payload = payload
        self.text = (
            text
            if text is not None
            else json.dumps(payload, ensure_ascii=False)
            if payload is not None
            else ""
        )

    def json(self):
        if self.payload is None:
            raise ValueError("no json")
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.closed = False

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)

    def close(self):
        self.closed = True


class SessionFactory:
    def __init__(self, groups):
        self.groups = [list(group) for group in groups]
        self.sessions = []

    def __call__(self):
        session = FakeSession(self.groups.pop(0))
        self.sessions.append(session)
        return session


def overview(checked=False, date="2026-11-24", balance=12.5):
    return FakeResponse(
        {
            "ok": True,
            "balance": balance,
            "checkin": {"date": date, "checked_in": checked},
        }
    )


def checkin(
    claimed=True,
    checked=True,
    reward=0.05,
    date="2026-11-24",
    balance=12.55,
):
    payload = {
        "ok": True,
        "date": date,
        "checked_in": checked,
        "claimed": claimed,
    }
    if reward is not None:
        payload["reward"] = reward
    if balance is not None:
        payload["balance"] = balance
    return FakeResponse(payload)


def account(token="session-secret"):
    return baipiao_daily.load_accounts({"BAIPIAO_SESSION": token})[0]


class BaipiaoDailyTests(unittest.TestCase):
    def test_load_multi_account_and_cookie_header(self):
        accounts = baipiao_daily.load_accounts(
            {
                "BAIPIAO_ACCOUNTS": (
                    "demo@example.com|bitapi_session=jwt-one; bitapi_csrf=other\n"
                    "second|jwt-two"
                )
            }
        )
        self.assertEqual(2, len(accounts))
        self.assertEqual("d***@example.com", accounts[0].note)
        self.assertEqual("jwt-one", accounts[0].session_token)
        self.assertEqual("jwt-two", accounts[1].session_token)

    def test_claim_uses_no_body_and_confirms_before_after(self):
        factory = SessionFactory(
            [[overview(False), checkin(), overview(True, balance=12.55)]]
        )
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("CLAIMED", result["result"])
        self.assertTrue(result["ok"])
        self.assertEqual(False, result["before_checked_in"])
        self.assertEqual(True, result["after_checked_in"])
        self.assertEqual(0.05, result["reward"])
        self.assertEqual(0.05, result["balance_delta"])

        calls = factory.sessions[0].calls
        self.assertEqual(["GET", "POST", "GET"], [call[0] for call in calls])
        post_kwargs = calls[1][2]
        self.assertNotIn("json", post_kwargs)
        self.assertNotIn("data", post_kwargs)
        self.assertEqual(
            "Bearer session-secret",
            post_kwargs["headers"]["Authorization"],
        )
        self.assertEqual(
            "https://example.test/api/checkin",
            calls[1][1],
        )

    def test_already_claimed_skips_post(self):
        factory = SessionFactory([[overview(True)]])
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("ALREADY_CLAIMED", result["result"])
        self.assertTrue(result["ok"])
        self.assertEqual(1, len(factory.sessions[0].calls))

    def test_query_mode_does_not_post(self):
        factory = SessionFactory([[overview(False)]])
        result = baipiao_daily.check_account(
            account(),
            mode="query",
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("AVAILABLE", result["result"])
        self.assertTrue(result["ok"])
        self.assertEqual(["GET"], [call[0] for call in factory.sessions[0].calls])

    def test_duplicate_response_still_needs_overview_readback(self):
        factory = SessionFactory(
            [[overview(False), checkin(False, True), overview(True)]]
        )
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("ALREADY_CLAIMED", result["result"])
        self.assertTrue(result["ok"])

    def test_inactive_portal_is_failure(self):
        factory = SessionFactory(
            [[overview(False), checkin(False, False, reward=None)]]
        )
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("INACTIVE", result["result"])
        self.assertFalse(result["ok"])

    def test_claim_not_applied_is_failure(self):
        factory = SessionFactory(
            [[overview(False), checkin(True, True), overview(False)]]
        )
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("CLAIM_NOT_APPLIED", result["result"])
        self.assertFalse(result["ok"])

    def test_date_conflict_is_failure(self):
        factory = SessionFactory(
            [
                [
                    overview(False, date="2026-11-24"),
                    checkin(date="2026-11-24"),
                    overview(True, date="2026-11-25"),
                ]
            ]
        )
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("STATE_CONFLICT", result["result"])
        self.assertFalse(result["ok"])

    def test_missing_boolean_fields_are_not_success(self):
        factory = SessionFactory(
            [[overview(False), FakeResponse({"ok": True, "claimed": True})]]
        )
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("INVALID_RESPONSE", result["result"])
        self.assertFalse(result["ok"])

    def test_401_is_auth_expired(self):
        factory = SessionFactory(
            [[FakeResponse({"detail": "expired"}, status_code=401)]]
        )
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("AUTH_EXPIRED", result["result"])
        self.assertFalse(result["ok"])

    def test_business_error_redacts_session(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        {
                            "ok": False,
                            "detail": "bad session-secret",
                        }
                    )
                ]
            ]
        )
        result = baipiao_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        rendered = json.dumps(result, ensure_ascii=False)
        self.assertEqual("BUSINESS_ERROR", result["result"])
        self.assertNotIn("session-secret", rendered)
        self.assertIn("[REDACTED]", rendered)

    def test_multi_account_isolation(self):
        accounts = baipiao_daily.load_accounts(
            {
                "BAIPIAO_ACCOUNTS": (
                    "one|token-one\n"
                    "two|token-two"
                )
            }
        )
        factory = SessionFactory(
            [
                [overview(True)],
                [FakeResponse({"detail": "expired"}, status_code=403)],
            ]
        )
        results = baipiao_daily.run_accounts(
            accounts,
            base_url="https://example.test",
            session_factory=factory,
            output=lambda _: None,
        )
        self.assertEqual("ALREADY_CLAIMED", results[0]["result"])
        self.assertEqual("AUTH_EXPIRED", results[1]["result"])
        self.assertIsNot(factory.sessions[0], factory.sessions[1])
        self.assertTrue(all(session.closed for session in factory.sessions))

    def test_config_error_summary(self):
        output = []
        code = baipiao_daily.main(
            [],
            env={},
            session_factory=SessionFactory([]),
            output=output.append,
        )
        self.assertEqual(2, code)
        self.assertEqual("CONFIG_ERROR", output[0]["result"])
        self.assertEqual("baipiao", output[-1]["provider"])

    def test_empty_base_url_uses_default(self):
        self.assertEqual(
            "https://ai.baipiao.co",
            baipiao_daily.resolve_base_url({"BAIPIAO_BASE_URL": ""}),
        )


if __name__ == "__main__":
    unittest.main()
