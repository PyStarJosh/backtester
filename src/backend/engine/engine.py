import pandas as pd
import numpy as np
import numpy.typing as npt

from ..risk import Exits, Entry, Sizing
from ..portfolio import Portfolio
from ..data import DataManager
from .positions import Positions
from ..strategy import Indicators

class Engine:
    '''Executes all backtester operations'''
    
    def __init__(self, initial_equity: float, asset_type: str, interval: str, symbol: str | None = None, commodity_type: str | None = None, start_date: str | None = None, end_date: str | None = None, atr_period: int = 14):
        self._pos_records: list[dict] = []
        self.data_manager = DataManager()
        self.asset_type = asset_type
        
        if self.asset_type == 'tseries':
            self.price_data_df = self.data_manager.get_formatted_time_series_data(symbol, interval, start_date, end_date)
            self.atr_series = Indicators.atr(
            self.price_data_df['high'], self.price_data_df['low'],
            self.price_data_df['close'], atr_period)
        else:
            self.price_data_df = self.data_manager.get_formatted_commodities_data(commodity_type, interval)
            self.atr_series = self.price_data_df['price'].diff().abs().rolling(window=atr_period).mean()

        self.portfolio = Portfolio(initial_equity, self.price_data_df.index)
    
    def trade_entry_execution(self, signal_df: pd.DataFrame, risk_pct: float, atr_multiplier: int):
        index: pd.DatetimeIndex = self.price_data_df.index
        is_tseries: bool = self.asset_type == 'tseries'
        price_column_name: str = 'close' if is_tseries else 'price'
        symbol_column_name: str = 'symbol' if is_tseries else 'commodity_type'
        prices: npt.NDArray[np.float64] = self.price_data_df[price_column_name].to_numpy()
        symbols: npt.NDArray[np.object_] = self.price_data_df[symbol_column_name].to_numpy()
        
        if is_tseries:
            highs: npt.NDArray[np.float64] = self.price_data_df['high'].to_numpy()
            lows: npt.NDArray[np.float64] = self.price_data_df['low'].to_numpy()
        else:
            highs = lows = prices

        signals: npt.NDArray[np.number] = self._align_to_bars(signal_df['signal'], index, 'signal', required=True)
        atrs = self._align_to_bars(self.atr_series, index, 'ATR', required=False)

        open_records = []  # positions still open, in the order they were opened

        for i, timestamp in enumerate(index):
            signal = signals[i]

            if signal != 0:
                atr = atrs[i]
                if pd.notna(atr) and atr > 0:
                    open_records.append(
                        self._open_position(risk_pct, timestamp, prices[i], symbols[i], signal, atr=atr, atr_multiplier=atr_multiplier)
                    )

            if not open_records:
                continue

            # Exits read their prices by key, so a plain dict satisfies them
            # without the cost of materialising a Series per bar.
            price_row = {'high': highs[i], 'low': lows[i]} if is_tseries else {'price': prices[i]}

            # Only rescan positions that are actually open — walking every
            # record ever opened made this loop O(bars * trades).
            still_open = []
            for record in open_records:
                # skip the bar the position opened on — its high/low already printed before we entered at the close
                if record['entry_time'] >= timestamp:
                    still_open.append(record)
                    continue

                if is_tseries:
                    exit_signal = Exits.check_tseries_trade(price_row, record)
                else:
                    exit_signal = Exits.check_commodity_trade(price_row, record)

                if not exit_signal:
                    still_open.append(record)
                    continue

                record['exit_time'] = timestamp
                record['exit_price'] = exit_signal.price
                record['exit_reason'] = exit_signal.reason
                record['status'] = 'closed'
                if record['side'] == 1:
                    record['pnl'] = (record['exit_price'] - record['entry_price']) * record['quantity']
                else:
                    record['pnl'] = (record['entry_price'] - record['exit_price']) * record['quantity']
                new_equity = self.portfolio.adjust_equity(record['pnl'])
                self.portfolio.equity_df.at[timestamp, 'price'] = new_equity

            open_records = still_open

        self.portfolio.equity_df['price'] = self.portfolio.equity_df['price'].ffill()
        self.pos_df = pd.DataFrame(self._pos_records)
        return self.pos_df, self.portfolio.equity_df

    def _align_to_bars(self, series: pd.Series, index: pd.DatetimeIndex, label: str, required: bool):
        '''Reindexes a series onto the price bars and returns it as an array'''
        aligned = series.reindex(index)
        # Preserves the contract the old per-bar .at[] lookup enforced: a bar
        # with no value is an error, not a bar to silently skip.
        if required and aligned.isna().any():
            missing = aligned.index[aligned.isna()][0]
            raise KeyError(f'{label} missing for bar {missing}')
        return aligned.to_numpy()

    def _open_position(self, risk_pct: float, timestamp, price: float, symbol: str, signal: int, atr: float, atr_multiplier: int) -> dict:
        shares = Sizing.volatility_targeted_sizing(risk_pct, self.portfolio.equity, atr_multiplier, atr)
        pos = Positions(
                    entry_time=timestamp,
                    entry_price=price,
                    symbol=symbol,
                    side=signal,
                    quantity=shares,
                    tp=Entry.set_tp(signal, price, atr, atr_multiplier),
                    sl=Entry.set_sl(signal, price, atr, atr_multiplier),
                    exit_time=None,
                    exit_price=None,
                    pnl=None,
                    exit_reason=None,
                    status='open',
                )
        record = vars(pos)
        self._pos_records.append(record)
        return record