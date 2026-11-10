from pathlib import Path
import pandas as pd
import yfinance as yf


url = (
    "https://raw.githubusercontent.com/fja05680/sp500/master/"
    "S%26P%20500%20Historical%20Components%20%26%20Changes%20%28Updated%29.csv"
)

history = pd.read_csv(url, parse_dates=["date"]).sort_values("date")
snapshot = history.loc[history["date"] <= "2023-12-29"].iloc[-1]

tickers = [ticker.strip() for ticker in snapshot["tickers"].split(",")]
universe = pd.DataFrame({"ticker": sorted(set(tickers))})

Path("data").mkdir(exist_ok=True)
universe.to_csv("data/universe_2023.csv", index=False)
print(snapshot['date'].date(), len(universe))

tickers = pd.read_csv('data/universe_2023.csv')

tickers = tickers['ticker'].str.replace(".", "-").tolist()
prices_daily = yf.download(
    tickers,
    start = '2020-01-01',
    end = '2026-01-01',
    auto_adjust= True
)

prices_daily = prices_daily['Close']
prices_daily = prices_daily.loc[:,~prices_daily.isna().all()]
print(prices_daily.head(20))
print(prices_daily.loc[:,prices_daily.isna().sum()>0].isna().sum())
# ABNB    238
# CARR     53
# CEG     516
# GEHC    745
# OTIS     53
# PARA    281
# VLTO    945 exclude them all.
prices_daily = prices_daily.loc[:,prices_daily.isna().sum()==0]
prices_daily.to_csv('data/all_time_daily_prices.csv')
