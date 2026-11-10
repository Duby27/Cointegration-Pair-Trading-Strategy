import pandas as pd
from statsmodels.tsa.stattools import coint

df = pd.read_csv('data/all_time_daily_prices.csv')
df['Date'] = pd.to_datetime(df['Date'])
df = df.set_index('Date')
train = df.loc["2020":"2023"]

tickers = df.columns.tolist()
qualified_pairs = []
for i in range(0,len(tickers)):
    for j in range(i+1, len(tickers)):
        x = train[tickers[i]]
        y = train[tickers[j]]
        test_stats, p_value, critic_values = coint(y, x, trend = 'c')
        if p_value < 0.05:
            qualified_pairs.append({
                'tic1' : tickers[i],
                'tic2' : tickers[j],
                'p_value': p_value 
            })

pairs = pd.DataFrame(qualified_pairs)
print(pairs.head(20))
pairs.to_csv("data/qualified_pairs.csv", index=False)

