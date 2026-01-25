import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"


@dataclass(frozen=True)
class AlertConfig:
    api_base_url: str
    pushover_app_token: str
    pushover_user_key: str

    # Market scan (hourly)
    market_enabled: bool
    market_min_score: int
    market_top_n: int
    market_period: str
    market_portfolio_only: bool

    # ETF scan (daily)
    etf_enabled: bool
    etf_min_score: int
    etf_top_n: int
    etf_period: str

    # Behavior
    state_file: Path
    log_file: Optional[Path]


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _env_str(name: str, default: str) -> str:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return default
    return val.strip()


def load_config() -> AlertConfig:
    repo_root = Path(__file__).resolve().parents[1]

    pushover_app_token = os.getenv("PUSHOVER_APP_TOKEN", "").strip()
    pushover_user_key = os.getenv("PUSHOVER_USER_KEY", "").strip()

    if not pushover_app_token or not pushover_user_key:
        raise RuntimeError(
            "Missing Pushover credentials. Set PUSHOVER_APP_TOKEN and PUSHOVER_USER_KEY environment variables."
        )

    state_file = Path(_env_str("ALERT_STATE_FILE", str(repo_root / "input" / ".alerts_state.json")))
    log_file_raw = os.getenv("ALERT_LOG_FILE")
    log_file = Path(log_file_raw).expanduser() if log_file_raw else None

    return AlertConfig(
        api_base_url=_env_str("ALERT_API_BASE_URL", "http://127.0.0.1:80"),
        pushover_app_token=pushover_app_token,
        pushover_user_key=pushover_user_key,
        market_enabled=_env_bool("ALERT_MARKET_ENABLED", True),
        market_min_score=_env_int("ALERT_MARKET_MIN_SCORE", 3),
        market_top_n=_env_int("ALERT_MARKET_TOP_N", 10),
        market_period=_env_str("ALERT_MARKET_PERIOD", "1y"),
        market_portfolio_only=_env_bool("ALERT_MARKET_PORTFOLIO_ONLY", True),
        etf_enabled=_env_bool("ALERT_ETF_ENABLED", True),
        etf_min_score=_env_int("ALERT_ETF_MIN_SCORE", 3),
        etf_top_n=_env_int("ALERT_ETF_TOP_N", 10),
        etf_period=_env_str("ALERT_ETF_PERIOD", "1y"),
        state_file=state_file,
        log_file=log_file,
    )


def log_line(cfg: AlertConfig, msg: str) -> None:
    line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line)
    if cfg.log_file:
        cfg.log_file.parent.mkdir(parents=True, exist_ok=True)
        with cfg.log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def now_et() -> datetime:
    if ZoneInfo is None:
        raise RuntimeError("zoneinfo is required (Python 3.9+)")
    return datetime.now(tz=ZoneInfo("America/New_York"))


def is_us_market_hours(now: Optional[datetime] = None) -> bool:
    n = now or now_et()
    if n.weekday() >= 5:
        return False

    t = n.time()
    start = dtime(9, 30)
    end = dtime(16, 0)
    return start <= t <= end


def read_portfolio_symbols(repo_root: Path) -> Set[str]:
    symbols: Set[str] = set()
    cfg_path = repo_root / "input" / "config_portfolio.txt"
    if not cfg_path.exists():
        return symbols

    for raw in cfg_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        symbols.add(line.upper())

    return symbols


def http_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data_bytes = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data_bytes = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url=url, method=method.upper(), data=data_bytes, headers=headers)
    with urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def pushover_send(cfg: AlertConfig, title: str, message: str) -> None:
    form = {
        "token": cfg.pushover_app_token,
        "user": cfg.pushover_user_key,
        "title": title,
        "message": message,
    }

    data = urlencode(form).encode("utf-8")
    req = Request(PUSHOVER_API_URL, data=data, method="POST")

    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            try:
                j = json.loads(body)
                status = j.get("status")
                req_id = j.get("request")
                if status != 1:
                    log_line(cfg, f"Pushover: unexpected response status={status} body={body}")
                else:
                    log_line(cfg, f"Pushover: ok request={req_id}")
            except Exception:
                # Non-JSON success; ignore
                pass
    except HTTPError as e:
        # Attempt to extract JSON error details
        try:
            body = e.read().decode("utf-8")
            j = json.loads(body)
            errors = j.get("errors") or j.get("error") or body
            log_line(cfg, f"Pushover HTTPError {e.code}: {errors}")
        except Exception:
            log_line(cfg, f"Pushover HTTPError {e.code}: {e.reason}")
        raise


def load_state(cfg: AlertConfig) -> Dict[str, Any]:
    if not cfg.state_file.exists():
        return {}
    try:
        return json.loads(cfg.state_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(cfg: AlertConfig, state: Dict[str, Any]) -> None:
    cfg.state_file.parent.mkdir(parents=True, exist_ok=True)
    cfg.state_file.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _signal_key(kind: str, item: Dict[str, Any]) -> str:
    sym = str(item.get("symbol", "")).upper()
    rec = str(item.get("recommendation", ""))
    score = item.get("score")
    return f"{kind}:{sym}:{rec}:{score}"


def _fmt_line(item: Dict[str, Any]) -> str:
    sym = item.get("symbol", "")
    rec = item.get("recommendation", "")
    score = item.get("score", "")
    price = item.get("price")
    rsi = item.get("rsi")

    parts = [f"{sym} {rec} (score {score})"]
    if price is not None:
        parts.append(f"${price}")
    if rsi is not None:
        parts.append(f"RSI {rsi}")

    return " - ".join(parts)


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:
        # Silent fallback if .env parsing fails
        pass


def run_market(cfg: AlertConfig, repo_root: Path, state: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    if not is_us_market_hours():
        log_line(cfg, "Market: skipped (outside US market hours ET)")
        return False, state

    url = cfg.api_base_url.rstrip("/") + "/analyze_market"
    data = http_json("POST", url, {"period": cfg.market_period, "top_n": cfg.market_top_n})

    recs = data.get("buy_recommendations") or []
    if not isinstance(recs, list):
        recs = []

    recs = [r for r in recs if isinstance(r, dict) and (r.get("score") is not None)]
    recs = [r for r in recs if int(r.get("score", -999)) >= cfg.market_min_score]

    if cfg.market_portfolio_only:
        portfolio = read_portfolio_symbols(repo_root)
        recs = [r for r in recs if str(r.get("symbol", "")).upper() in portfolio]

    recs = recs[: cfg.market_top_n]

    last_keys = set(state.get("market_last_keys") or [])
    current_keys = {_signal_key("market", r) for r in recs}

    new_keys = current_keys - last_keys
    new_recs = [r for r in recs if _signal_key("market", r) in new_keys]

    state["market_last_keys"] = sorted(current_keys)
    state["market_last_run_et"] = now_et().isoformat(timespec="seconds")

    if not new_recs:
        log_line(cfg, f"Market: no new BUY alerts (candidates={len(recs)})")
        return False, state

    title = "Market BUY Alerts"
    lines = ["New BUY signals (portfolio-filtered)" if cfg.market_portfolio_only else "New BUY signals"]
    lines += [_fmt_line(r) for r in new_recs[:10]]

    message = "\n".join(lines)
    pushover_send(cfg, title=title, message=message)
    log_line(cfg, f"Market: sent {len(new_recs)} alerts")

    return True, state


def run_etf(cfg: AlertConfig, state: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    url = cfg.api_base_url.rstrip("/") + "/analyze_etf"
    data = http_json("POST", url, {"period": cfg.etf_period, "top_n": cfg.etf_top_n})

    recs = data.get("buy_recommendations") or []
    if not isinstance(recs, list):
        recs = []

    recs = [r for r in recs if isinstance(r, dict) and (r.get("score") is not None)]
    recs = [r for r in recs if int(r.get("score", -999)) >= cfg.etf_min_score]
    recs = recs[: cfg.etf_top_n]

    last_keys = set(state.get("etf_last_keys") or [])
    current_keys = {_signal_key("etf", r) for r in recs}

    new_keys = current_keys - last_keys
    new_recs = [r for r in recs if _signal_key("etf", r) in new_keys]

    state["etf_last_keys"] = sorted(current_keys)
    state["etf_last_run_local"] = datetime.now().isoformat(timespec="seconds")

    if not new_recs:
        log_line(cfg, f"ETF: no new BUY alerts (candidates={len(recs)})")
        return False, state

    title = "ETF BUY Alerts"
    lines = ["New ETF BUY signals"]
    lines += [_fmt_line(r) for r in new_recs[:10]]

    message = "\n".join(lines)
    pushover_send(cfg, title=title, message=message)
    log_line(cfg, f"ETF: sent {len(new_recs)} alerts")

    return True, state


def main(argv: List[str]) -> int:
    mode = (argv[1] if len(argv) > 1 else "all").strip().lower()

    try:
        repo_root = Path(__file__).resolve().parents[1]
        _load_dotenv(repo_root / ".env")
        cfg = load_config()
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[1]

    state = load_state(cfg)
    changed = False

    try:
        if mode in {"test", "pushover_test"}:
            title = "7H Alerts Test"
            message = f"Test push at {now_et().isoformat(timespec='seconds')}"
            pushover_send(cfg, title=title, message=message)
            log_line(cfg, "Test: sent pushover test alert")
            return 0

        if mode in {"all", "market"} and cfg.market_enabled:
            _, state = run_market(cfg, repo_root, state)
            changed = True

        if mode in {"all", "etf"} and cfg.etf_enabled:
            _, state = run_etf(cfg, state)
            changed = True

        if changed:
            save_state(cfg, state)

        return 0

    except HTTPError as e:
        log_line(cfg, f"HTTPError: {e.code} {e.reason}")
        return 1
    except URLError as e:
        log_line(cfg, f"URLError: {e.reason}")
        return 1
    except Exception as e:
        log_line(cfg, f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
