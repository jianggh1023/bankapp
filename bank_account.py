from __future__ import annotations

import json
import os
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional


class BankAccount:
    """银行存取款与按平均日余额计算利息的核心类。"""

    def __init__(self, owner: str = "用户", initial_balance: float = 0.0, annual_rate: float = 0.015, opening_date: Optional[date] = None, storage_path: Optional[str] = None):
        self.owner = owner
        self.initial_balance = self._money(Decimal(str(initial_balance)))
        self.balance = self.initial_balance
        self.annual_rate = Decimal(str(annual_rate))
        self.opening_date = opening_date or date.today()
        self.last_interest_date: Optional[date] = None
        self.transactions: List[Dict[str, object]] = []
        self.storage_path = storage_path or os.path.join(os.path.dirname(__file__), "bank_account_data.json")
        self._load_from_disk()

    def deposit(self, amount: float, description: str, transaction_date: Optional[date] = None) -> Decimal:
        amount_dec = self._normalize_amount(amount)
        if amount_dec <= 0:
            raise ValueError("存款金额必须大于 0")
        tx_date = transaction_date or date.today()
        self.balance += amount_dec
        transaction = {
            "date": tx_date,
            "description": description,
            "deposit": amount_dec,
            "withdraw": Decimal("0.00"),
            "balance": self._money(self.balance),
        }
        self.transactions.append(transaction)
        self._save_to_disk()
        return self._money(self.balance)

    def withdraw(self, amount: float, description: str, transaction_date: Optional[date] = None) -> Decimal:
        amount_dec = self._normalize_amount(amount)
        if amount_dec <= 0:
            raise ValueError("取款金额必须大于 0")
        if self.balance < amount_dec:
            raise ValueError("余额不足，无法取款")
        tx_date = transaction_date or date.today()
        self.balance -= amount_dec
        transaction = {
            "date": tx_date,
            "description": description,
            "deposit": Decimal("0.00"),
            "withdraw": amount_dec,
            "balance": self._money(self.balance),
        }
        self.transactions.append(transaction)
        self._save_to_disk()
        return self._money(self.balance)

    def settle_interest(self, settle_date: Optional[date] = None) -> Decimal:
        """每年 6 月 30 日和 12 月 31 日各结算一次利息。"""
        settle_date = settle_date or date.today()
        if (settle_date.month == 6 and settle_date.day == 30) or (settle_date.month == 12 and settle_date.day == 31):
            pass
        else:
            raise ValueError("利息只能在每年 6 月 30 日和 12 月 31 日计算")

        if self.last_interest_date and self.last_interest_date == settle_date:
            return Decimal("0.00")

        start_date = self.last_interest_date or self._first_balance_date()
        if settle_date < start_date:
            raise ValueError("结算日期不能早于上次结息日期")

        average_balance = self._calculate_average_daily_balance(start_date, settle_date)
        days = (settle_date - start_date).days + 1
        interest = average_balance * self.annual_rate * Decimal(days) / Decimal(365)
        interest = self._money(interest)

        if interest > 0:
            self.balance += interest
            self.transactions.append({
                "date": settle_date,
                "description": "利息",
                "deposit": interest,
                "withdraw": Decimal("0.00"),
                "balance": self._money(self.balance),
            })

        self.last_interest_date = settle_date
        self._save_to_disk()
        return interest

    def _first_balance_date(self) -> date:
        if self.initial_balance > 0:
            return self.opening_date
        for tx in sorted(self.transactions, key=lambda item: item["date"]):
            tx_date = tx["date"]
            if isinstance(tx_date, date):
                return tx_date
        return self.opening_date

    def _calculate_average_daily_balance(self, start_date: date, end_date: date) -> Decimal:
        balance = self.initial_balance
        sorted_transactions = sorted(self.transactions, key=lambda item: item["date"])

        for tx in sorted_transactions:
            tx_date = tx["date"]
            if isinstance(tx_date, date) and tx_date < start_date:
                balance += self._transaction_delta(tx)

        total = Decimal("0.00")
        current_day = start_date
        tx_index = 0
        while current_day <= end_date:
            while tx_index < len(sorted_transactions):
                tx = sorted_transactions[tx_index]
                tx_date = tx["date"]
                if isinstance(tx_date, date) and tx_date < start_date:
                    tx_index += 1
                    continue
                if isinstance(tx_date, date) and tx_date <= current_day:
                    balance += self._transaction_delta(tx)
                    tx_index += 1
                else:
                    break
            total += balance
            current_day += timedelta(days=1)

        days = (end_date - start_date).days + 1
        return self._money(total / Decimal(days))

    def _transaction_delta(self, tx: Dict[str, object]) -> Decimal:
        deposit = tx.get("deposit", Decimal("0.00"))
        withdraw = tx.get("withdraw", Decimal("0.00"))
        if not isinstance(deposit, Decimal):
            deposit = Decimal(str(deposit))
        if not isinstance(withdraw, Decimal):
            withdraw = Decimal(str(withdraw))
        return deposit - withdraw

    def _normalize_amount(self, amount: float) -> Decimal:
        return self._money(Decimal(str(amount)))

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_statement(self) -> List[Dict[str, object]]:
        return [
            {
                "date": tx["date"],
                "description": tx["description"],
                "deposit": tx["deposit"],
                "withdraw": tx["withdraw"],
                "balance": tx["balance"],
            }
            for tx in self.transactions
        ]

    def show_balance(self) -> str:
        return f"当前余额：{self._money(self.balance)} 元"

    def _save_to_disk(self) -> None:
        data = {
            "owner": self.owner,
            "initial_balance": str(self.initial_balance),
            "balance": str(self.balance),
            "annual_rate": str(self.annual_rate),
            "opening_date": self.opening_date.isoformat() if self.opening_date else None,
            "last_interest_date": self.last_interest_date.isoformat() if self.last_interest_date else None,
            "transactions": [
                {
                    "date": tx["date"].isoformat() if isinstance(tx["date"], date) else str(tx["date"]),
                    "description": tx["description"],
                    "deposit": str(tx["deposit"]),
                    "withdraw": str(tx["withdraw"]),
                    "balance": str(tx["balance"]),
                }
                for tx in self.transactions
            ],
        }
        with open(self.storage_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def _load_from_disk(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return

        self.owner = data.get("owner", self.owner)
        self.initial_balance = self._money(Decimal(str(data.get("initial_balance", self.initial_balance))))
        self.balance = self._money(Decimal(str(data.get("balance", self.balance))))
        self.annual_rate = Decimal(str(data.get("annual_rate", self.annual_rate)))
        self.opening_date = date.fromisoformat(data["opening_date"]) if data.get("opening_date") else self.opening_date
        self.last_interest_date = date.fromisoformat(data["last_interest_date"]) if data.get("last_interest_date") else None
        self.transactions = []
        for item in data.get("transactions", []):
            self.transactions.append({
                "date": date.fromisoformat(item["date"]) if isinstance(item.get("date"), str) else item["date"],
                "description": item.get("description", ""),
                "deposit": self._money(Decimal(str(item.get("deposit", "0")))),
                "withdraw": self._money(Decimal(str(item.get("withdraw", "0")))),
                "balance": self._money(Decimal(str(item.get("balance", "0")))),
            })
