import yfinance as yf
import pandas as pd
from abc import ABC, abstractmethod
from matplotlib import pyplot as plt
from transaction import Transaction
import numpy as np


class BasicPosition(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker_data = yf.Ticker(self.symbol)
        # get current price from yfinance ticker
        self.current_price = self.ticker_data.history().tail(1)['Close'].iloc[0]


class Position(BasicPosition):
    def __init__(self, symbol: str, currency: str, transactions: list = []):
        super().__init__(symbol)

        self.currency = currency
        self.transactions = transactions

        self.avg_purchase_price = 0
        self.current_amount = 0

        if len(self.transactions) > 0:
            # create dataframe based on data from yfinance ticker with starting date of first transaction
            self._df = self.ticker_data.history(period="max")[self.transactions[0].date:][["Close", "Low", "High",
                                                                                           'Dividends', 'Stock Splits']]
            # create extra rows that are going to be calculated
            self._df["Amount"] = 0
            self._df.loc[:, "RealizedProfit"] = 0
            self._df.loc[:, "CostOfPosition"] = 0
            self._df.loc[:, "Profit%"] = 0
            self._df.loc[:, "Profit"] = 0
            self._df.loc[:, "TotalProfit"] = 0
            self._df.loc[:, "AvgPrice"] = 0

            self.apply_transactions()
        else:
            # if no transactions to be added just clear
            self._df = self.ticker_data.history(period="max")[["Close"]]

    def apply_transactions(self):
        for transaction in self.transactions:
            # create mask for df for dates from transaction up until end
            df_mask = pd.to_datetime(self._df.index) >= transaction.date
            if transaction.amount > 0:
                self._df.loc[df_mask, "AvgPrice"] = (self._df.loc[df_mask, "AvgPrice"] *
                                                     self.current_amount +
                                                     transaction.amount * transaction.price
                                                     ) / ( transaction.amount + self.current_amount)
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
        self._df["Value"] = self._df["Close"] * (self._df["Amount"])

    def show_chart(self) -> None:
        plt.figure();

        self._df["RealizedProfit"].plot();
        self._df["Close"].plot(secondary_y=True);
        plt.show()

    @property
    def dataframe(self):
        return self._df
