import time
from bot import run_cycle
print("QW Gold Paper Bot running — PAPER ONLY. Press Ctrl+C to stop.")
while True:
    try:
        s=run_cycle()
        print(s.get("last_update"),s.get("last_signal"),
              "Balance:",s.get("balance"),"Equity:",s.get("equity"))
    except Exception as err:
        print("Bot error:",err)
    time.sleep(60)
