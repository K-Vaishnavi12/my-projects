"""Stock history downloader & loader.

Pulls 5 years of daily OHLCV from Yahoo Finance for each ticker in
``YF_TICKERS`` and caches as Parquet (falls back to CSV if pyarrow missing)
under ``ml_data_dir/stock_history/<symbol>.csv``.

If yfinance / internet is unavailable, ``synthesize_history`` produces
realistic geometric-Brownian-motion paths so training and tests still work.
"""
from __future__ import annotations
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from src.ml.config import YF_TICKERS, YF_TO_DISPLAY, ml_data_dir


def _history_dir() -> Path:
    p = ml_data_dir() / "stock_history"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _csv_path(display_symbol: str) -> Path:
    return _history_dir() / f"{display_symbol}.csv"


# ── Online fetch ────────────────────────────────────────────────────
def download_history(tickers: Iterable[str] = YF_TICKERS,
                     period: str = "5y",
                     interval: str = "1d",
                     pause_sec: float = 0.4) -> dict[str, Path]:
    """Download daily OHLCV for each ticker. Returns {display_symbol: csv_path}.

    Skips tickers that fail (no internet, delisted, etc.).
    """
    try:
        import yfinance as yf
    except ImportError:
        print("[stock_history] yfinance not installed; skipping download")
        return {}

    saved: dict[str, Path] = {}
    for tk in tickers:
        display = YF_TO_DISPLAY.get(tk, tk.replace("^", "").replace(".NS", ""))
        try:
            df = yf.download(tk, period=period, interval=interval,
                             progress=False, auto_adjust=False, threads=False)
            if df is None or df.empty:
                print(f"[stock_history] {tk}: empty")
                continue
            # Yahoo sometimes returns a MultiIndex column when called with one ticker
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df.rename(columns=str.lower)
            df.index.name = "date"
            df = df[["open", "high", "low", "close", "volume"]].dropna()
            out = _csv_path(display)
            df.to_csv(out)
            saved[display] = out
            print(f"[stock_history] {display}: {len(df)} rows -> {out.name}")
            time.sleep(pause_sec)
        except Exception as e:
            print(f"[stock_history] {tk} failed: {e}")
            continue
    return saved


# ── Synthetic fallback ──────────────────────────────────────────────
def synthesize_history(symbol: str, n_days: int = 1200,
                       start_price: float = 1000.0, seed: int = 42) -> pd.DataFrame:
    """Geometric Brownian motion + occasional jumps. Realistic enough for
    forecasting / anomaly demos when no internet is available.
    """
    rng = np.random.default_rng(seed + hash(symbol) % 10_000)
    mu, sigma = 0.0004, 0.012
    log_returns = rng.normal(mu, sigma, size=n_days)
    # Inject a few "shock" days that anomaly detectors should catch
    shock_idx = rng.choice(n_days, size=max(3, n_days // 250), replace=False)
    log_returns[shock_idx] += rng.choice([-1, 1], size=len(shock_idx)) * 0.06
    close = start_price * np.exp(np.cumsum(log_returns))
    high = close * (1 + np.abs(rng.normal(0, 0.005, n_days)))
    low = close * (1 - np.abs(rng.normal(0, 0.005, n_days)))
    open_ = close * (1 + rng.normal(0, 0.003, n_days))
    volume = rng.integers(1_000_000, 10_000_000, n_days)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n_days, freq="B")
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": volume,
    }, index=pd.Index(dates, name="date"))


def ensure_history(symbol: str, n_synth_days: int = 1200) -> pd.DataFrame:
    """Load cached CSV; if missing, synthesize and cache it."""
    path = _csv_path(symbol)
    if path.exists():
        df = pd.read_csv(path, index_col="date", parse_dates=True)
        if not df.empty:
            return df
    df = synthesize_history(symbol, n_days=n_synth_days)
    df.to_csv(path)
    return df


def load_history(symbol: str) -> pd.DataFrame:
    """Strict loader — errors if not cached. Use ``ensure_history`` for fallback."""
    path = _csv_path(symbol)
    if not path.exists():
        raise FileNotFoundError(
            f"No cached history for {symbol}. Run "
            f"`python -m src.ml.data.stock_history` to download or synthesize."
        )
    return pd.read_csv(path, index_col="date", parse_dates=True)


def list_available_symbols() -> list[str]:
    return sorted(p.stem for p in _history_dir().glob("*.csv"))


# ── CLI ─────────────────────────────────────────────────────────────
def main() -> None:
    """Download all configured tickers; synthesize any that fail."""
    saved = download_history()
    # Fill gaps with synthetic data so training never blocks on missing files
    for display in YF_TO_DISPLAY.values():
        if display not in saved and not _csv_path(display).exists():
            df = synthesize_history(display)
            df.to_csv(_csv_path(display))
            print(f"[stock_history] {display}: synthesized {len(df)} rows (offline fallback)")
    print(f"\nReady symbols: {list_available_symbols()}")


if __name__ == "__main__":
    main()
