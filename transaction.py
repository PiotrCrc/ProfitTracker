from datetime import datetime
from dataclasses import dataclass

@dataclass
class Transaction:
    date: datetime
    amount: float
    price: float
    fee: float = 0

