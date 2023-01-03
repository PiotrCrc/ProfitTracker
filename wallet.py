from position import Position
import pandas as pd

class Wallet:
    def __init__(self,positions):
        self.summary = pd.DataFrame()
        self.positions = positions
        if len(positions) > 0:
            self.calculate_sum()

    def calculate_sum(self):
        for position in self.positions:
            self.summary[position.symbol+"_tp"] = position.dataframe["TotalProfit"]
            self.summary[position.symbol + "_tp_w_div"] = position.dataframe["TotalProfitWithDiv"]
        self.summary.plot()
