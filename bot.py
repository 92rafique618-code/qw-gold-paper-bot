import json, time
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import yfinance as yf

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "paper_state.json"
TRADES = ROOT / "trades.csv"
SYMBOL = "XAUUSD=X"
START = 500.0
RISK = 2.50
DAILY_STOP = 5.0
MAX_DD = 25.0
MAX_NOTIONAL = 500.0
SLIPPAGE_BPS = 5
FEE_BPS = 2

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def initial_state():
    return {"balance": START, "equity": START, "peak_equity": START,
            "day": datetime.now(timezone.utc).date().isoformat(),
            "daily_realized": 0.0, "position": None, "last_processed_bar": None,
            "last_price": None, "last_signal": "Waiting for market data",
            "last_update": None, "mode": "PAPER ONLY"}

def load_state():
    if STATE.exists():
        try: return json.loads(STATE.read_text())
        except Exception: pass
    s = initial_state(); save_state(s); return s

def save_state(s):
    STATE.write_text(json.dumps(s, indent=2))

def fetch_hourly():
    df = yf.Ticker(SYMBOL).history(period="730d", interval="1h", auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError("No Yahoo Finance XAUUSD=X hourly data returned.")
    df = df.rename(columns=str.title).dropna(subset=["Close"])
    if df.index.tz is None: df.index = df.index.tz_localize("UTC")
    else: df.index = df.index.tz_convert("UTC")
    # Only completed hourly candles.
    df = df[df.index < pd.Timestamp.now(tz="UTC").floor("h")]
    if len(df) < 250: raise RuntimeError(f"Insufficient hourly history: {len(df)} bars.")
    return df

def indicators(df):
    x = df.copy()
    x["EMA20"] = x["Close"].ewm(span=20, adjust=False).mean()
    delta = x["Close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI14"] = 100 - 100/(1+rs)
    pc = x["Close"].shift()
    tr = pd.concat([(x["High"]-x["Low"]), (x["High"]-pc).abs(), (x["Low"]-pc).abs()], axis=1).max(axis=1)
    x["ATR14"] = tr.ewm(alpha=1/14, adjust=False).mean()
    h = x.resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna()
    h["EMA50"] = h["Close"].ewm(span=50, adjust=False).mean()
    h["EMA200"] = h["Close"].ewm(span=200, adjust=False).mean()
    now = pd.Timestamp.now(tz="UTC").floor("h")
    h = h[h.index + pd.Timedelta(hours=4) <= now]
    mapped = h[["EMA50","EMA200"]].reindex(x.index, method="ffill")
    x["H4_EMA50"], x["H4_EMA200"] = mapped["EMA50"], mapped["EMA200"]
    return x

def log_trade(row):
    pd.DataFrame([row]).to_csv(TRADES, mode="a" if TRADES.exists() else "w",
                               header=not TRADES.exists(), index=False)

def close_position(s, price, reason, bar_time):
    p = s["position"]
    side, qty = p["side"], p["quantity_oz"]
    fill = price*(1-SLIPPAGE_BPS/10000 if side=="LONG" else 1+SLIPPAGE_BPS/10000)
    gross = ((fill-p["entry"]) if side=="LONG" else (p["entry"]-fill))*qty
    fees = (p["entry"]*qty + fill*qty)*FEE_BPS/10000
    net = gross-fees
    s["balance"] = round(s["balance"]+net, 2)
    s["daily_realized"] = round(s["daily_realized"]+net, 2)
    log_trade({"opened_at":p["opened_at"],"closed_at":bar_time,"symbol":"XAUUSD",
      "side":side,"quantity_oz":qty,"entry":p["entry"],"exit":round(fill,4),
      "stop":p["stop"],"target":p["target"],"gross_pnl":round(gross,2),
      "estimated_fees":round(fees,2),"net_pnl":round(net,2),"reason":reason})
    s["position"] = None

def run_cycle():
    s = load_state()
    day = datetime.now(timezone.utc).date().isoformat()
    if s.get("day") != day:
        s["day"], s["daily_realized"] = day, 0.0
    raw = fetch_hourly()
    x = indicators(raw).dropna(subset=["EMA20","RSI14","ATR14","H4_EMA50","H4_EMA200"])
    if len(x) < 3: raise RuntimeError("Not enough indicator history.")
    b, prev = x.iloc[-1], x.iloc[-2]
    t = x.index[-1].isoformat()
    price = float(b["Close"])
    s["last_price"], s["last_update"] = round(price,4), utcnow()
    if s.get("last_processed_bar") == t:
        s["last_signal"] = "Waiting for next completed 1H candle"
        save_state(s); return s

    p = s.get("position")
    if p:
        if p["side"]=="LONG":
            if float(b["Low"]) <= p["stop"]: close_position(s,p["stop"],"STOP_LOSS",t)
            elif float(b["High"]) >= p["target"]: close_position(s,p["target"],"TAKE_PROFIT",t)
        else:
            if float(b["High"]) >= p["stop"]: close_position(s,p["stop"],"STOP_LOSS",t)
            elif float(b["Low"]) <= p["target"]: close_position(s,p["target"],"TAKE_PROFIT",t)

    p = s.get("position")
    unreal = 0.0 if not p else ((price-p["entry"]) if p["side"]=="LONG" else (p["entry"]-price))*p["quantity_oz"]
    s["equity"] = round(s["balance"]+unreal,2)
    s["peak_equity"] = max(float(s.get("peak_equity",START)),s["equity"])
    dd = s["peak_equity"]-s["equity"]

    if s["daily_realized"] <= -DAILY_STOP: signal = "Daily loss stop: entries paused"
    elif dd >= MAX_DD: signal = "Max drawdown stop: entries paused"
    elif p: signal = "Position open: "+p["side"]
    else:
        bull = b["H4_EMA50"]>b["H4_EMA200"] and b["Close"]>b["H4_EMA50"]
        bear = b["H4_EMA50"]<b["H4_EMA200"] and b["Close"]<b["H4_EMA50"]
        up = prev["Close"]<=prev["EMA20"] and b["Close"]>b["EMA20"]
        down = prev["Close"]>=prev["EMA20"] and b["Close"]<b["EMA20"]
        go_long = bull and up and 50<=b["RSI14"]<=70
        go_short = bear and down and 30<=b["RSI14"]<=50
        signal = "No setup"
        if go_long or go_short:
            side = "LONG" if go_long else "SHORT"
            dist = 2*float(b["ATR14"])
            qty = min(RISK/dist, MAX_NOTIONAL/price) if dist>0 else 0
            planned = qty*dist
            if qty*price < 1 or planned > 7.50:
                signal = "Risk sizing blocked entry"
            else:
                entry = price*(1+SLIPPAGE_BPS/10000 if side=="LONG" else 1-SLIPPAGE_BPS/10000)
                stop = entry-dist if side=="LONG" else entry+dist
                target = entry+2*dist if side=="LONG" else entry-2*dist
                s["position"]={"side":side,"entry":round(entry,4),"stop":round(stop,4),
                  "target":round(target,4),"quantity_oz":round(qty,6),
                  "planned_risk":round(planned,2),"opened_at":t}
                signal = "SIMULATED "+side+" opened"
    s["last_signal"], s["last_processed_bar"], s["last_bar_time"] = signal,t,t
    p=s.get("position")
    unreal=0 if not p else ((price-p["entry"]) if p["side"]=="LONG" else (p["entry"]-price))*p["quantity_oz"]
    s["equity"]=round(s["balance"]+unreal,2)
    save_state(s)
    return s

def reset_account():
    if STATE.exists(): STATE.unlink()
    if TRADES.exists(): TRADES.unlink()
    return load_state()

def trades_frame():
    return pd.read_csv(TRADES) if TRADES.exists() else pd.DataFrame()
