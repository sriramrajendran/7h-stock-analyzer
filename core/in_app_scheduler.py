import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from core.alerts_runner import load_config, load_state, log_line, run_etf, run_market, save_state


def _sleep_until(dt: datetime) -> None:
    while True:
        now = datetime.now(dt.tzinfo)
        remaining = (dt - now).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 30))


def _next_local_time(hour: int, minute: int) -> datetime:
    now = datetime.now()
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate = candidate + timedelta(days=1)
    return candidate


def _next_hour() -> datetime:
    now = datetime.now()
    base = now.replace(minute=0, second=0, microsecond=0)
    if base <= now:
        base = base + timedelta(hours=1)
    return base


def _market_loop(repo_root: Path) -> None:
    cfg = load_config()

    while True:
        try:
            state = load_state(cfg)
            _, state = run_market(cfg, repo_root, state)
            save_state(cfg, state)
        except Exception as e:
            log_line(cfg, f"Market scheduler error: {str(e)}")

        _sleep_until(_next_hour())


def _etf_loop() -> None:
    cfg = load_config()

    etf_hour = int(os.getenv('ALERT_ETF_RUN_HOUR', '8'))
    etf_minute = int(os.getenv('ALERT_ETF_RUN_MINUTE', '0'))

    while True:
        try:
            state = load_state(cfg)
            _, state = run_etf(cfg, state)
            save_state(cfg, state)
        except Exception as e:
            log_line(cfg, f"ETF scheduler error: {str(e)}")

        _sleep_until(_next_local_time(etf_hour, etf_minute))


_started = False


def start_background_schedulers() -> None:
    global _started
    if _started:
        return

    repo_root = Path(__file__).resolve().parents[1]

    market_t = threading.Thread(target=_market_loop, args=(repo_root,), name="market-alerts", daemon=True)
    etf_t = threading.Thread(target=_etf_loop, name="etf-alerts", daemon=True)

    market_t.start()
    etf_t.start()

    _started = True
