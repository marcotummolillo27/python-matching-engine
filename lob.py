from collections import deque, defaultdict          # was "colllection"
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional
import time
import itertools


@dataclass
class Order:
    id: int
    side: str
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)


class OrderBook:
    def __init__(self):                              # was "__int__"
        self.bids: Dict[float, Deque[Order]] = defaultdict(deque)  # was "Deuqe"
        self.asks: Dict[float, Deque[Order]] = defaultdict(deque)
        self.bid_prices: List[float] = []
        self.ask_prices: List[float] = []
        self.orders: Dict[int, Order] = {}
        self._id_gen = itertools.count(1)
        self.trades: List[dict] = []

    def _add_price(self, prices: List[float], price: float, reverse: bool):
        if price in prices:
            return
        prices.append(price)
        prices.sort(reverse=reverse)

    def _remove_price_if_empty(self, side: str, price: float):
        book = self.bids if side == "buy" else self.asks
        prices = self.bid_prices if side == "buy" else self.ask_prices
        if not book[price]:
            del book[price]
            prices.remove(price)

    def best_bid(self) -> Optional[float]:
        return self.bid_prices[0] if self.bid_prices else None

    def best_ask(self) -> Optional[float]:
        return self.ask_prices[0] if self.ask_prices else None

    def add_limit_order(self, side: str, price: float, quantity: float) -> int:
        assert side in ("buy", "sell")
        assert quantity > 0
        order_id = next(self._id_gen)                # was "self.id_gen"
        order = Order(id=order_id, side=side, price=price, quantity=quantity)
        self.orders[order_id] = order

        if side == "buy":
            self._match_buy(order)
            if order.quantity > 0:
                self.bids[price].append(order)
                self._add_price(self.bid_prices, price, reverse=True)
        else:
            self._match_sell(order)
            if order.quantity > 0:
                self.asks[price].append(order)
                self._add_price(self.ask_prices, price, reverse=False)
        return order_id

    def _match_buy(self, buy: Order):
        while buy.quantity > 0 and self.ask_prices and self.ask_prices[0] <= buy.price:
            best_ask_price = self.ask_prices[0]
            level = self.asks[best_ask_price]

            while buy.quantity > 0 and level:
                sell = level[0]
                traded_qty = min(buy.quantity, sell.quantity)   # was broken line
                self._execute_trade(buy, sell, best_ask_price, traded_qty)

                buy.quantity -= traded_qty
                sell.quantity -= traded_qty

                if sell.quantity == 0:
                    level.popleft()
                    del self.orders[sell.id]

            self._remove_price_if_empty("sell", best_ask_price)

    def _match_sell(self, sell: Order):
        while sell.quantity > 0 and self.bid_prices and self.bid_prices[0] >= sell.price:
            best_bid_price = self.bid_prices[0]
            level = self.bids[best_bid_price]

            while sell.quantity > 0 and level:
                buy = level[0]
                traded_qty = min(sell.quantity, buy.quantity)
                self._execute_trade(buy, sell, best_bid_price, traded_qty)

                sell.quantity -= traded_qty
                buy.quantity -= traded_qty

                if buy.quantity == 0:
                    level.popleft()
                    del self.orders[buy.id]

            self._replace_price_if_empty("buy", best_bid_price)  # wait, fix below

    def _execute_trade(self, buy: Order, sell: Order, price: float, qty: float):
        trade = {
            "price": price,
            "quantity": qty,
            "buy_id": buy.id,
            "sell_id": sell.id,
            "timestamp": time.time(),
        }
        self.trades.append(trade)

    def cancel(self, order_id: int) -> bool:
        order = self.orders.get(order_id)
        if not order or order.quantity <= 0:
            return False

        book = self.bids if order.side == "buy" else self.asks
        level = book[order.price]

        for i, o in enumerate(level):
            if o.id == order_id:
                del level[i]
                del self.orders[order_id]
                self._remove_price_if_empty(order.side, order.price)  # was "order.rice"
                return True
        return False

    def market_order(self, side: str, quantity: float):          # was "market_orde"
        extreme_price = float("inf") if side == "buy" else 0.0
        return self.add_limit_order(side, extreme_price, quantity)

    def depth(self, levels: int = 5) -> dict:
        bids = []
        for p in self.bid_prices[:levels]:
            qty = sum(o.quantity for o in self.bids[p])
            bids.append((p, qty))
        asks = []
        for p in self.ask_prices[:levels]:
            qty = sum(o.quantity for o in self.asks[p])
            asks.append((p, qty))
        return {"bids": bids, "asks": asks}

    def __str__(self):
        d = self.depth(5)
        lines = ["      BIDS          ASKS"]
        max_len = max(len(d["bids"]), len(d["asks"]))
        for i in range(max_len):
            bid_str = (
                f"{d['bids'][i][1]:8.2f} @ {d['bids'][i][0]:8.2f}"
                if i < len(d["bids"])
                else " " * 20
            )
            ask_str = (
                f"{d['asks'][i][0]:8.2f} @ {d['asks'][i][1]:8.2f}"
                if i < len(d["asks"])
                else ""
            )
            lines.append(f"{bid_str}  |  {ask_str}")
        return "\n".join(lines)
    
ob = OrderBook()

ob.add_limit_order("buy", 100.0, 10)
ob.add_limit_order("buy", 99.5, 5)
ob.add_limit_order("sell", 101.0, 8)
ob.add_limit_order("sell", 102.0, 12)

print(ob)
#       BIDS          ASKS
#    10.00 @   100.00  |    101.00 @     8.00
#     5.00 @    99.50  |    102.00 @    12.00

ob.add_limit_order("buy", 101.5, 6)   # crosses the book
print(ob)
print("Trades:", ob.trades)
