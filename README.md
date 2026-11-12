# QW Gold Paper Bot v1.1

PAPER ONLY. No broker connection, live orders, deposits, or withdrawals.

## Data feeds
- Current indicative XAU/USD spot quote: XAUS `https://xaus.com/api/v1/spot?compact=1` (no API key; cache/update behavior and freshness are shown in the response).
- Historical 1H candles used by the strategy: legacy Yahoo Finance `XAUUSD=X` fallback. This source may return no data. If it does, the strategy remains PAUSED and does not create simulated entries.

The XAUS spot quote is an indicative mid-market spot price, not a broker bid/ask or executable price. A live quote alone is not enough to calculate the existing strategy's 1H EMA20/RSI/ATR and 4H EMA50/EMA200 filters. Do not bypass the history guard or invent candles.

## Existing paper risk settings
- Starting virtual balance: $500
- Risk per trade: $2.50
- Daily realized loss pause: $5
- Maximum drawdown pause: $25
- Simulated notional cap: $500 (1x)
- Stop: 2 x ATR(14), target: 2R

## Deploy
Streamlit Community Cloud main file: `dashboard.py`.
