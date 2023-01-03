import yfinance as yf
import pandas as pd
import pickle
from matplotlib import pyplot as plt
from transaction import Transaction
import numpy as np


class Position:
    def __init__(self, symbol: str, currency: str, transactions: list[Transaction] = (), save_data=False, load_data=False):
        self.load_data = load_data
        self.save_data = save_data

        self.symbol = symbol
        self.currency = currency
        self.transactions = transactions

        self.ticker_data = None
        self.current_price = 0
        self.update_ticker_data(self.symbol)

        self.avg_purchase_price = 0
        self.current_amount = 0

        if len(self.transactions) > 0:
            self._df = self.ticker_data.history(period="max")[self.transactions[0].date:][["Close", "Low", "High",
                                                                                           'Dividends', 'Stock Splits']]
            self.apply_transactions()
        else:
            self._df = self.ticker_data.history(period="max")[["Close"]]

    def update_ticker_data(self, symbol):
        if self.load_data:  # just
            pickle_file = open(self.load_data, 'rb')
            self.ticker_data = pickle.load(pickle_file)
            pickle_file.close()
        else:
            self.ticker_data = yf.Ticker(self.symbol)
            if self.save_data:
                pickle_file = open(self.save_data, 'wb')
                pickle.dump(self.ticker_data, pickle_file)
                pickle_file.close()
        self.current_price = self.ticker_data.history().tail(1)['Close'].iloc[0]

    def apply_transactions(self):
        self._df["Amount"] = 0
        self._df.loc[:, "RealizedProfit"] = 0
        self._df.loc[:, "CostOfPosition"] = 0
        self._df.loc[:, "Profit%"] = 0
        self._df.loc[:, "Profit"] = 0
        self._df.loc[:, "TotalProfit"] = 0
        self._df.loc[:, "TotalProfitWithDiv"] = 0
        self._df.loc[:, "AvgPrice"] = 0

        for transaction in self.transactions:
            df_mask = pd.to_datetime(self._df.index).tz_localize(None) >= transaction.date
            if transaction.amount > 0:
                self._df.loc[df_mask, "AvgPrice"] = (self._df.loc[df_mask, "AvgPrice"] *
                                                     self.current_amount +
                                                     transaction.amount * transaction.price
                                                     ) / (
                                                     transaction.amount + self.current_amount)
                self.current_amount += transaction.amount
                self._df.loc[df_mask, "Amount"] = self._df.loc[df_mask, "Amount"] + transaction.amount

                self._df.loc[df_mask, "CostOfPosition"] = self._df.loc[df_mask, "AvgPrice"] * \
                                                          self._df.loc[df_mask, "Amount"]
            elif transaction.amount < 0:
                if abs(transaction.amount) > self.current_amount:
                    raise ValueError(f"You are selling more ({abs(transaction.amount)})"
                                     f" that You have ({self.current_amount})! ")
                self._df.loc[df_mask, "RealizedProfit"] += (transaction.price -
                                                            self._df.loc[df_mask, "AvgPrice"]) * \
                                                           (-transaction.amount)
                self.current_amount += transaction.amount
                self._df.loc[df_mask, "Amount"] = self._df.loc[df_mask, "Amount"] + transaction.amount
                self._df.loc[df_mask, "CostOfPosition"] = self._df.loc[df_mask, "CostOfPosition"] + \
                                                          self._df.loc[df_mask, "AvgPrice"] * \
                                                          transaction.amount
            self._df.loc[df_mask, "TotalProfit"] = (self._df.loc[df_mask, "RealizedProfit"] +
                                                    self._df.loc[df_mask, "Close"] *
                                                    self._df.loc[df_mask, "Amount"]) - \
                                                    self._df.loc[df_mask, "CostOfPosition"]

        self._df["DividendValue"] = self._df["Dividends"] * self._df["Amount"]
        self._df["DividendProfit"] = self._df["DividendValue"].cumsum()
        self._df["TotalProfitWithDiv"] = self._df["DividendProfit"] + self._df["TotalProfit"]
        self._df["Value"] = self._df["Close"] * (self._df["Amount"])


    def show_chart(self) -> None:
        plt.figure()


        self._df["TotalProfit"].plot()
        self._df["Close"].plot(secondary_y = True)
        plt.show()


    @property
    def dataframe(self):
        return self._df
