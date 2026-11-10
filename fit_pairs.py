import pandas as pd
import statsmodels.api as sm

pairs = pd.read_csv('data/qualified_pairs.csv')
atdp = pd.read_csv('data/all_time_daily_prices.csv')
atdp['Date'] = pd.to_datetime(atdp['Date'])
atdp = atdp.set_index('Date')
train = atdp.loc["2020":"2023"]

result_list = []
for i in pairs.index:
    tic1 = pairs['tic1'].iloc[i]
    tic2 = pairs['tic2'].iloc[i]
    x = train[tic1]
    x = sm.add_constant(x)
    y = train[tic2]
    model = sm.OLS(y,x)
    results = model.fit()
    result_list.append({
        'ticx':tic1,
        'ticy':tic2,
        'alpha' : results.params["const"],
        'beta' : results.params[tic1],
        'spread_mean' : results.resid.mean(),
        'spread_se' :results.resid.std()
    })
resdf = pd.DataFrame(result_list)
resdf.to_csv('data/pairs_results.csv')