import pandas as pd
import statsmodels.api as sm
resdf = pd.read_csv('data/pairs_results.csv')
atdp = pd.read_csv('data/all_time_daily_prices.csv')
atdp['Date'] = pd.to_datetime(atdp['Date'])
atdp = atdp.set_index('Date')

trade_data = atdp.loc['2024':'2025']

tickers = []
for i in resdf.index:
    tickers.append(resdf['ticx'].iloc[i])
    tickers.append(resdf['ticy'].iloc[i])
tickers = sorted(set(tickers))

daily_positions = pd.DataFrame(
    0.0,
    index=trade_data.index,
    columns=tickers,
)
daily_cashflow = []
pair_positions = [0] * len(resdf)
gross_per_trade = 1000.0
entry_units = [0.0] * len(resdf)
entry_value = [0.0] * len(resdf)

pair_summary = pd.DataFrame(
    index = resdf.index,
    columns = ['ticx', 'ticy', 'opens', 'closes', 'realized_PnL', 'floating_PnL', 'overall_PnL' ]
)
pair_summary = resdf[["ticx", "ticy"]].copy()
pair_summary["opens"] = 0
pair_summary["closes"] = 0
pair_summary["realized_PnL"] = 0.0
pair_summary["floating_PnL"] = 0.0
pair_summary["overall_PnL"] = 0.0


open_trades = {}
trade_log = []


for date in trade_data.index:
    cashflow_today = 0
    for i in resdf.index:
        pair = resdf.loc[i]
        x_price = trade_data.loc[date, pair['ticx']]
        y_price = trade_data.loc[date, pair['ticy']]
        spread = y_price - pair['alpha'] - pair['beta'] * x_price
        z = (spread - pair['spread_mean']) / pair['spread_std']
        beta = pair['beta']

        if pair_positions[i] != 0:
            if (pair_positions[i] == 1 and z >= 0) or (pair_positions[i] == -1 and z <= 0):
                delta_x = pair_positions[i] *beta*entry_units[i]
                delta_y = -pair_positions[i]*entry_units[i]
                daily_positions.loc[date, pair["ticx"]] += delta_x
                daily_positions.loc[date, pair["ticy"]] += delta_y
                cashflow_today -= delta_x * x_price + delta_y * y_price

                pair_positions[i] = 0
                entry_units[i] = 0.0
                pair_summary.loc[i, 'closes'] += 1
                exit_value = -(delta_x * x_price + delta_y * y_price)
                trade_pnl = exit_value - entry_value[i]
                pair_summary.loc[i, "realized_PnL"] += trade_pnl

                
                trade = open_trades.pop(i)
                trade.update(
                    exit_date=date,
                    exit_x=x_price,
                    exit_y=y_price,
                    exit_z=z,
                    status="closed",
                    pnl=trade_pnl,
                )
                trade_log.append(trade)
        else:
            if z >= 2:
                entry_units[i] = gross_per_trade / (y_price + abs(beta) * x_price)
                delta_x = beta * entry_units[i]
                delta_y = -entry_units[i]

                daily_positions.loc[date, pair['ticx']] += delta_x
                daily_positions.loc[date, pair['ticy']] += delta_y
                entry_value[i] = delta_x * x_price + delta_y * y_price
                cashflow_today -= entry_value[i]

                pair_summary.loc[i, 'opens'] += 1
                pair_positions[i] = -1
            if z <= -2:
                entry_units[i] = gross_per_trade / (y_price + abs(beta) * x_price)
                delta_x = -beta * entry_units[i]
                delta_y = entry_units[i]

                daily_positions.loc[date, pair['ticx']] += delta_x
                daily_positions.loc[date, pair['ticy']] += delta_y
                entry_value[i] = delta_x * x_price + delta_y * y_price
                cashflow_today -= entry_value[i]

                pair_summary.loc[i, 'opens'] += 1
                pair_positions[i] = 1

            
            if pair_positions[i] != 0:
                open_trades[i] = {
                    "pair_id": i,
                    "ticx": pair["ticx"],
                    "ticy": pair["ticy"],
                    "entry_date": date,
                    "direction": pair_positions[i],
                    "shares_x": delta_x,
                    "shares_y": delta_y,
                    "entry_x": x_price,
                    "entry_y": y_price,
                    "entry_z": z,
                }
                
        if date == trade_data.index[-1] and pair_positions[i] != 0:
            shares_y = pair_positions[i] * entry_units[i]
            shares_x = -beta * shares_y
            final_value = shares_x * x_price + shares_y * y_price
            pair_summary.loc[i, "floating_PnL"] = final_value - entry_value[i]

           
            trade = open_trades.pop(i)
            trade.update(
                mark_date=date,
                mark_x=x_price,
                mark_y=y_price,
                mark_z=z,
                status="open",
                pnl=final_value - entry_value[i],
            )
            trade_log.append(trade)

    daily_cashflow.append(cashflow_today)

# daily_positions.to_csv('data/daily_share_changes.csv')

# cashflow = pd.Series(
#     daily_cashflow,
#     index=trade_data.index,
#     name='cashflow',
# )
# cashflow.to_csv('data/daily_cashflow.csv')
# print(daily_positions.head(20))
# print(daily_cashflow)
# final_shares = daily_positions.sum(axis=0)
# final_prices = trade_data.iloc[-1][final_shares.index]

# final_position_value = (final_shares * final_prices).sum()
# total_pnl = sum(daily_cashflow) + final_position_value

# print("期末持仓市值:", final_position_value)
# print("总盈亏:", total_pnl)

pair_summary["overall_PnL"] = (
    pair_summary["realized_PnL"] + pair_summary["floating_PnL"]
)
pair_summary.to_csv("data/pair_summary.csv", index=False)


pd.DataFrame(trade_log).to_csv("data/trade_log.csv", index=False)

final_shares = daily_positions.sum(axis=0)
final_prices = trade_data.iloc[-1][final_shares.index]
total_pnl = sum(daily_cashflow) + (final_shares * final_prices).sum()

print("组合 P&L:", total_pnl)
print("逐对 P&L:", pair_summary["overall_PnL"].sum())
print("逐笔 P&L:", sum(trade["pnl"] for trade in trade_log))
print("日志笔数 / 开仓次数:", len(trade_log), pair_summary["opens"].sum())