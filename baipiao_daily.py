#!/usr/bin/env python3
"""Baipiao daily check-in with strict before/after server readback."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

import requests


PROVIDER = "baipiao"
DEFAULT_BASE_URL = "https://ai.baipiao.co"
BASE_URL_ENV = "BAIPIAO_BASE_URL"
ACCOUNTS_ENV = "BAIPIAO_ACCOUNTS"
SESSION_ENV = "BAIPIAO_SESSION"
OVERVIEW_PATH = "/api/overview"
CHECKIN_PATH = "/api/checkin"
REQUEST_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 Baipiao-Daily/1.0"


class ConfigError(ValueError):
    """Configuration or credential input error."""


class APIError(RuntimeError):
    """Classified API failure."""

    def __init__(
        self,
        result: str,
        message: str,
        *,
        http_status: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.result = result
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True)
class Account:
    note: str
    session_token: str


def emit(payload: Mapping[str, Any]) -> None:
    print(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        flush=True,
    )


def _safe_label(raw: str, index: int) -> str:
    text = re.sub(r"[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "account_%d" % index
    if re.fullmatch(r"1\d{10}", text):
        return text[:3] + "****" + text[-4:]
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", text):
        local, domain = text.split("@", 1)
        return (local[:1] or "*") + "***@" + domain
    return text[:64]


def _redact(value: Any, secrets: Sequence[str]) -> str:
    text = str(value)
    unique: list[str] = []
    for secret in secrets:
        secret = str(secret or "")
        if secret and secret not in unique:
            unique.append(secret)
    for secret in sorted(unique, key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    return text


def normalize_session(raw: str) -> str:
    text = str(raw or "").strip()
    text = re.sub(r"^bearer\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^cookie:\s*", "", text, flags=re.IGNORECASE)
    if not text:
        return ""
    if "=" in text:
        for part in text.split(";"):
            name, separator, value = part.partition("=")
            if separator and name.strip() == "bitapi_session":
                return value.strip()
        return ""
    return text


def load_accounts(
    env: Optional[Mapping[str, str]] = None,
) -> list[Account]:
    values = os.environ if env is None else env
    raw = str(values.get(ACCOUNTS_ENV, "") or "").strip()
    accounts: list[Account] = []

    if raw:
        lines = [line.strip() for line in re.split(r"[\r\n]+", raw) if line.strip()]
        for index, line in enumerate(lines, 1):
            if "|" not in line:
                raise ConfigError(
                    "account %d must use label|bitapi_session" % index
                )
            label, pasted = line.split("|", 1)
            token = normalize_session(pasted)
            if not token:
                raise ConfigError(
                    "account %d has no bitapi_session value" % index
                )
            accounts.append(
                Account(
                    note=_safe_label(label, index),
                    session_token=token,
                )
            )
        return accounts

    token = normalize_session(str(values.get(SESSION_ENV, "") or ""))
    if not token:
        raise ConfigError(
            "BAIPIAO_ACCOUNTS or BAIPIAO_SESSION is not configured"
        )
    return [Account(note="account_1", session_token=token)]


def resolve_base_url(env: Optional[Mapping[str, str]] = None) -> str:
    values = os.environ if env is None else env
    raw = str(values.get(BASE_URL_ENV, "") or "").strip()
    text = (raw or DEFAULT_BASE_URL).rstrip("/")
    if not text.startswith("https://") and not text.startswith("http://"):
        raise ConfigError("BAIPIAO_BASE_URL must be an http(s) URL")
    return text


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
    )
    return session


def _headers(account: Account) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "Authorization": "Bearer " + account.session_token,
    }


def _response_text(response: Any) -> str:
    text = getattr(response, "text", "")
    if text:
        return str(text)
    try:
        return json.dumps(response.json(), ensure_ascii=False)
    except Exception:
        return ""


def _payload_message(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    for key in ("detail", "message", "msg", "error"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            nested = _payload_message(value)
            if nested:
                return nested
        elif value not in (None, "", False):
            return str(value)
    return ""


def _business_error(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    if payload.get("ok") is False or payload.get("success") is False:
        return _payload_message(payload) or "request failed"
    error = payload.get("error")
    if error not in (None, "", False, {}, []):
        return _payload_message(payload) or str(error)
    return ""


def _request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str],
    secrets: Sequence[str],
) -> tuple[Any, int]:
    try:
        response = session.request(
            method,
            url,
            headers=dict(headers),
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise APIError(
            "NETWORK_ERROR",
            "network request failed: %s" % _redact(exc, secrets),
        ) from exc

    status = int(getattr(response, "status_code", 0) or 0)
    text = _response_text(response)
    if 300 <= status < 400:
        raise APIError(
            "AUTH_EXPIRED",
            "login session expired (HTTP %d redirect)" % status,
            http_status=status,
        )
    if status in (401, 403):
        raise APIError(
            "AUTH_EXPIRED",
            "bitapi_session is invalid or expired (HTTP %d)" % status,
            http_status=status,
        )
    if status == 429:
        raise APIError(
            "RATE_LIMITED",
            "request was rate limited (HTTP %d)" % status,
            http_status=status,
        )
    if not 200 <= status < 300:
        message = _payload_message(
            _try_json(response)
        )
        if message:
            raise APIError(
                "BUSINESS_ERROR",
                _redact(message, secrets),
                http_status=status,
            )
        raise APIError(
            "HTTP_ERROR",
            "request failed (HTTP %d)" % status,
            http_status=status,
        )
    if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
        raise APIError(
            "BLOCKED",
            "server returned an HTML challenge instead of JSON",
            http_status=status,
        )
    try:
        payload = response.json()
    except Exception as exc:
        raise APIError(
            "INVALID_JSON",
            "response is not JSON: %s" % _redact(exc, secrets),
            http_status=status,
        ) from exc
    if not isinstance(payload, Mapping):
        raise APIError(
            "INVALID_RESPONSE",
            "response is not a JSON object",
            http_status=status,
        )
    business = _business_error(payload)
    if business:
        raise APIError(
            "BUSINESS_ERROR",
            _redact(business, secrets),
            http_status=status,
        )
    return payload, status


def _try_json(response: Any) -> Any:
    try:
        return response.json()
    except Exception:
        return None


def _number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return int(number) if number.is_integer() else number


def parse_overview(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise APIError("STATUS_UNRECOGNIZED", "overview payload is missing")
    checkin = payload.get("checkin")
    if not isinstance(checkin, Mapping):
        raise APIError(
            "STATUS_UNRECOGNIZED",
            "overview.checkin is missing",
        )
    checked_in = checkin.get("checked_in")
    if not isinstance(checked_in, bool):
        raise APIError(
            "STATUS_UNRECOGNIZED",
            "overview.checkin.checked_in is not boolean",
        )
    return {
        "checked_in": checked_in,
        "date": checkin.get("date"),
        "balance": _number(payload.get("balance")),
    }


def parse_checkin(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise APIError("INVALID_RESPONSE", "check-in payload is missing")
    claimed = payload.get("claimed")
    checked_in = payload.get("checked_in")
    if not isinstance(claimed, bool):
        raise APIError(
            "INVALID_RESPONSE",
            "check-in response claimed field is not boolean",
        )
    if not isinstance(checked_in, bool):
        raise APIError(
            "INVALID_RESPONSE",
            "check-in response checked_in field is not boolean",
        )
    reward = _number(payload.get("reward"))
    return {
        "claimed": claimed,
        "checked_in": checked_in,
        "reward": reward,
        "date": payload.get("date"),
        "balance": _number(payload.get("balance")),
    }


def _read_overview(
    session: requests.Session,
    base_url: str,
    account: Account,
    secrets: Sequence[str],
) -> tuple[dict[str, Any], int]:
    payload, status = _request_json(
        session,
        "GET",
        base_url + OVERVIEW_PATH,
        headers=_headers(account),
        secrets=secrets,
    )
    return parse_overview(payload), status


def _result(
    account: Account,
    result: str,
    ok: bool,
    message: str,
    *,
    http_status: Optional[int] = None,
    claimed: bool = False,
    checked_in: Optional[bool] = None,
    reward: Optional[float] = None,
    date: Any = None,
    before: Optional[Mapping[str, Any]] = None,
    after: Optional[Mapping[str, Any]] = None,
    response_balance: Optional[float] = None,
) -> dict[str, Any]:
    before = before or {}
    after = after or {}
    balance_before = before.get("balance")
    balance_after = after.get("balance")
    balance_delta = None
    if isinstance(balance_before, (int, float)) and isinstance(
        balance_after, (int, float)
    ):
        balance_delta = round(balance_after - balance_before, 10)
        if isinstance(balance_delta, float) and balance_delta.is_integer():
            balance_delta = int(balance_delta)
    return {
        "account": account.note,
        "provider": PROVIDER,
        "result": result,
        "ok": ok,
        "message": message,
        "http_status": http_status,
        "claimed": claimed,
        "checked_in": checked_in,
        "reward": reward,
        "date": date,
        "before_checked_in": before.get("checked_in"),
        "after_checked_in": after.get("checked_in"),
        "before_date": before.get("date"),
        "after_date": after.get("date"),
        "balance_before": balance_before,
        "balance_after": balance_after,
        "balance_delta": balance_delta,
        "response_balance": response_balance,
    }


def check_account(
    account: Account,
    *,
    mode: str = "claim",
    base_url: Optional[str] = None,
    session_factory: Callable[[], requests.Session] = make_session,
) -> dict[str, Any]:
    try:
        resolved_base_url = (
            base_url.rstrip("/") if base_url else resolve_base_url()
        )
    except ConfigError as exc:
        return _result(account, "CONFIG_ERROR", False, str(exc))
    secrets = [account.session_token]
    session = None
    try:
        session = session_factory()
        before, before_status = _read_overview(
            session,
            resolved_base_url,
            account,
            secrets,
        )
        if before["checked_in"]:
            return _result(
                account,
                "ALREADY_CLAIMED",
                True,
                "today's check-in was already recorded before this run",
                http_status=before_status,
                claimed=True,
                checked_in=True,
                before=before,
                after=before,
            )
        if mode == "query":
            return _result(
                account,
                "AVAILABLE",
                True,
                "today's check-in is available",
                http_status=before_status,
                before=before,
                after=before,
            )

        raw_response, claim_status = _request_json(
            session,
            "POST",
            resolved_base_url + CHECKIN_PATH,
            headers=_headers(account),
            secrets=secrets,
        )
        response = parse_checkin(raw_response)
        if not response["claimed"]:
            if not response["checked_in"]:
                return _result(
                    account,
                    "INACTIVE",
                    False,
                    "the portal reports no active daily check-in",
                    http_status=claim_status,
                    before=before,
                )
            after, after_status = _read_overview(
                session,
                resolved_base_url,
                account,
                secrets,
            )
            if not after["checked_in"]:
                return _result(
                    account,
                    "STATE_CONFLICT",
                    False,
                    "check-in response says checked in but overview still says false",
                    http_status=after_status or claim_status,
                    before=before,
                    after=after,
                )
            return _result(
                account,
                "ALREADY_CLAIMED",
                True,
                "the portal reports today's check-in was already completed",
                http_status=after_status or claim_status,
                claimed=True,
                checked_in=True,
                reward=response["reward"],
                date=response["date"],
                before=before,
                after=after,
                response_balance=response["balance"],
            )

        if not response["checked_in"]:
            raise APIError(
                "INVALID_RESPONSE",
                "check-in response claimed=true but checked_in=false",
                http_status=claim_status,
            )
        reward = response["reward"]
        if reward is None:
            raise APIError(
                "INVALID_RESPONSE",
                "check-in response has no numeric reward",
                http_status=claim_status,
            )
        if reward <= 0:
            return _result(
                account,
                "CREDIT_UNCONFIRMED",
                False,
                "check-in response did not report a positive reward",
                http_status=claim_status,
                checked_in=True,
                reward=reward,
                date=response["date"],
                before=before,
                response_balance=response["balance"],
            )

        after, after_status = _read_overview(
            session,
            resolved_base_url,
            account,
            secrets,
        )
        if not after["checked_in"]:
            return _result(
                account,
                "CLAIM_NOT_APPLIED",
                False,
                "check-in request returned success but overview.checked_in is false",
                http_status=after_status or claim_status,
                reward=reward,
                date=response["date"],
                before=before,
                after=after,
                response_balance=response["balance"],
            )
        response_date = response["date"]
        overview_date = after.get("date")
        if (
            response_date not in (None, "")
            and overview_date not in (None, "")
            and str(response_date) != str(overview_date)
        ):
            return _result(
                account,
                "STATE_CONFLICT",
                False,
                "check-in date and overview date do not match",
                http_status=after_status or claim_status,
                reward=reward,
                date=response_date,
                before=before,
                after=after,
                response_balance=response["balance"],
            )
        return _result(
            account,
            "CLAIMED",
            True,
            "check-in confirmed by reward and overview.checked_in",
            http_status=after_status or claim_status,
            claimed=True,
            checked_in=True,
            reward=reward,
            date=response_date,
            before=before,
            after=after,
            response_balance=response["balance"],
        )
    except APIError as exc:
        return _result(
            account,
            exc.result,
            False,
            exc.message,
            http_status=exc.http_status,
        )
    except ConfigError as exc:
        return _result(account, "CONFIG_ERROR", False, str(exc))
    except Exception as exc:
        return _result(
            account,
            "UNEXPECTED_ERROR",
            False,
            "unexpected error: %s" % _redact(exc, secrets),
        )
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()


def run_accounts(
    accounts: Sequence[Account],
    *,
    mode: str = "claim",
    base_url: Optional[str] = None,
    session_factory: Callable[[], requests.Session] = make_session,
    output: Callable[[Mapping[str, Any]], None] = emit,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for account in accounts:
        result = check_account(
            account,
            mode=mode,
            base_url=base_url,
            session_factory=session_factory,
        )
        results.append(result)
        output(result)
    return results


def build_summary(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    success = sum(1 for result in results if result.get("ok") is True)
    return {
        "provider": PROVIDER,
        "accounts": len(results),
        "success": success,
        "failed": len(results) - success,
        "claimed_now": sum(
            1 for result in results if result.get("result") == "CLAIMED"
        ),
        "already_claimed": sum(
            1 for result in results if result.get("result") == "ALREADY_CLAIMED"
        ),
        "results": [dict(result) for result in results],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Claim the Baipiao daily check-in reward."
    )
    parser.add_argument("--query", "--status", action="store_true", dest="query")
    parser.add_argument("--only", type=int, default=0)
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    env: Optional[Mapping[str, str]] = None,
    session_factory: Callable[[], requests.Session] = make_session,
    output: Callable[[Mapping[str, Any]], None] = emit,
) -> int:
    args = build_parser().parse_args(argv)
    mode = "query" if args.query else "claim"
    try:
        accounts = load_accounts(env)
        base_url = resolve_base_url(env)
        if args.only:
            if args.only < 1 or args.only > len(accounts):
                raise ConfigError("--only is outside the configured account range")
            accounts = [accounts[args.only - 1]]
    except ConfigError as exc:
        result = _result(
            Account("config", ""),
            "CONFIG_ERROR",
            False,
            str(exc),
        )
        summary = build_summary([result])
        output(result)
        output(summary)
        return 2

    results = run_accounts(
        accounts,
        mode=mode,
        base_url=base_url,
        session_factory=session_factory,
        output=output,
    )
    summary = build_summary(results)
    output(summary)
    return 0 if summary["failed"] == 0 else 1


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    _configure_utf8_stdio()
    sys.exit(main())
