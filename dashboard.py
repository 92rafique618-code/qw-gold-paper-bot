import streamlit as st
from bot import load_state, run_cycle, reset_account, trades_frame, START

st.set_page_config(page_title="QW Gold Paper Bot", page_icon="🥇", layout="wide")
st.title("🥇 QW Gold Paper Trading")
st.caption("XAU/USD • Automatic strategy • $500 virtual balance • PAPER ONLY")
st.warning("No broker connection or real orders. Yahoo Finance data availability and delays may vary.")

@st.fragment(run_every="60s")
def live_panel():
    try:
        s=run_cycle()
        st.success("Bot checked. Signals use completed 1-hour candles only.")
    except Exception as e:
        s=load_state()
        st.error(f"Data/bot error: {e}")
    a,b,c=st.columns(3)
    a.metric("Virtual balance",f"${s.get('balance',START):,.2f}")
    b.metric("Equity",f"${s.get('equity',START):,.2f}")
    c.metric("Latest gold quote",f"${s['last_price']:,.2f}" if s.get("last_price") else "Waiting")
    d,e,f=st.columns(3)
    d.metric("Today's realized P&L",f"${s.get('daily_realized',0):,.2f}")
    e.metric("Last signal",s.get("last_signal","Waiting"))
    f.metric("Mode","PAPER ONLY")
    st.subheader("Open simulated position")
    if s.get("position"):
        st.json(s["position"])
    else:
        st.info("No open simulated position.")
    st.caption("Last update UTC: "+str(s.get("last_update") or "Not started"))
    st.subheader("Closed paper trades")
    trades=trades_frame()
    if trades.empty: st.write("No closed trades yet.")
    else: st.dataframe(trades.tail(30),use_container_width=True,hide_index=True)

live_panel()
with st.sidebar:
    st.header("Risk settings")
    st.write("Starting balance: $500")
    st.write("Risk per trade: $2.50")
    st.write("Daily realized loss stop: $5")
    st.write("Maximum drawdown stop: $25")
    st.write("Simulated notional cap: $500 (1x)")
    st.write("Stop: 2 × ATR(14) | Target: 2R")
    if st.button("Reset virtual account"):
        reset_account()
        st.success("Reset to $500.")
        st.rerun()
    st.caption("Prototype only. Not for live trading.")
