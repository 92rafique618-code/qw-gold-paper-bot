# QW Gold Paper Bot v1.0

Mobile-friendly Streamlit dashboard and Python automatic paper simulator for Yahoo Finance `XAUUSD=X` gold spot quote.

## Important
- PAPER ONLY: no broker connection, API keys, real orders, deposits or withdrawals.
- Yahoo Finance `XAUUSD=X` data availability and delays may vary; it is not a guaranteed executable broker quote.
- Strategy uses completed 1-hour candles and a completed 4-hour trend filter.
- Strategy is experimental, not proven profitable.
- Simulated slippage/fees are illustrative, not actual broker CFD spreads, swaps or commissions.
- If stop and target are both touched in one hourly candle, simulation assumes stop first.
- Dashboard cycles only while active/refreshing; Streamlit hosting can sleep. It is not guaranteed 24/7.
- A phone browser alone cannot keep a Python bot running continuously.

## Strategy and limits
4H EMA50/EMA200 trend filter; 1H EMA20 crossover; RSI14 filter (50–70 long, 30–50 short); stop = 2 x ATR14; target = 2R.
$500 virtual balance; $2.50 planned risk/trade; $5 daily realized-loss pause; $25 drawdown pause; $500 simulated notional cap (1x); one position at a time; no martingale.

## Run on a computer
1. Install Python 3.10+.
2. Extract the ZIP and open a terminal in the folder.
3. `python -m pip install -r requirements.txt`
4. Automatic engine: `python main.py`
5. In another terminal: `streamlit run dashboard.py`
6. Open the Streamlit network URL on your phone using the same Wi-Fi.

For online dashboard hosting, deploy `dashboard.py` from GitHub to Streamlit Community Cloud. It may sleep after inactivity and is not a continuous bot host. For continuous operation, use an always-on computer/server and persistent storage. Do not expose an unauthenticated dashboard publicly.

## Files
- bot.py: data, indicators, strategy and simulated ledger
- dashboard.py: mobile dashboard
- main.py: continuous polling loop
- requirements.txt: dependencies
- paper_state.json and trades.csv: generated during use
