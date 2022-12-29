from position import Position
import pandas as pd

class Wallet:
    def __init__(self,positions):
        self.positions = positions

    def calculate_sum(self):
        for position in self.positions:


