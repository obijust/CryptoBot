import time
from abc import *
from threading import Lock

from config.cst import TradeOrderSide, OrderStatus, TraderOrderType, SIMULATOR_LAST_PRICES_TO_CHECK

""" Order class will represent an open order in the specified exchange
In simulation it will also define rules to be filled / canceled
It is also use to store creation & fill values of the order """


class Order:
    __metaclass__ = ABCMeta

    def __init__(self, trader):
        super().__init__()
        self.trader = trader
        self.exchange = self.trader.get_exchange()
        self.is_simulated = self.trader.simulate
        self.side = None
        self.symbol = None
        self.origin_price = 0
        self.origin_stop_price = 0
        self.origin_quantity = 0
        self.market_total_fees = 0
        self.currency_total_fees = 0
        self.filled_quantity = 0
        self.filled_price = 0
        self.currency, self.market = None, None
        self.order_id = None
        self.status = None
        self.order_type = None
        self.creation_time = 0
        self.canceled_time = 0
        self.executed_time = 0
        self.last_prices = None
        self.created_last_price = None
        self.order_profitability = None
        self.linked_to = None

        self.order_notifier = None

        self.linked_orders = []
        self.lock = Lock()

    # Disposable design pattern
    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()

    # create the order by setting all the required values
    def new(self, order_type, symbol, current_price, quantity,
            price=None,
            stop_price=None,
            status=None,
            order_notifier=None,
            order_id=None,
            quantity_filled=None,
            timestamp=None,
            linked_to=None):

        self.order_id = order_id
        self.origin_price = price
        self.status = status
        self.created_last_price = current_price
        self.origin_quantity = quantity
        self.origin_stop_price = stop_price
        self.symbol = symbol
        self.order_type = order_type
        self.order_notifier = order_notifier
        self.currency, self.market = self.exchange.split_symbol(symbol)
        self.filled_quantity = quantity_filled
        self.linked_to = linked_to

        if timestamp is None:
            self.creation_time = time.time()
        else:
            self.creation_time = timestamp

        if status is None:
            self.status = OrderStatus.OPEN
        else:
            self.status = status

        if self.trader.simulate:
            self.filled_quantity = quantity

    # update_order_status will define the rules for a simulated order to be filled / canceled
    @abstractmethod
    def update_order_status(self):
        raise NotImplementedError("Update_order_status not implemented")

    # check_last_prices is used to collect data to perform the order update_order_status process
    def check_last_prices(self, price, inferior):
        if self.last_prices is not None:
            prices = [p["price"] for p in self.last_prices[-SIMULATOR_LAST_PRICES_TO_CHECK:]]

            if inferior:
                if float(min(prices)) < price:
                    return True
                else:
                    return False
            else:
                if float(max(prices)) > price:
                    return True
                else:
                    return False
        return False

    def cancel_order(self):
        self.status = OrderStatus.CANCELED
        self.canceled_time = time.time()

        # if real order
        if not self.is_simulated:
            self.exchange.cancel_order(self.order_id, self.symbol)

        self.trader.notify_order_cancel(self)

    def close_order(self):
        self.trader.notify_order_close(self)

    def add_linked_order(self, order):
        self.linked_orders.append(order)

    def get_linked_orders(self):
        return self.linked_orders

    def get_currency_and_market(self):
        return self.currency, self.market

    def get_side(self):
        return self.side

    def get_id(self):
        return self.order_id

    def get_market_total_fees(self):
        return self.market_total_fees

    def get_currency_total_fees(self):
        return self.currency_total_fees

    def get_filled_quantity(self):
        return self.filled_quantity

    def get_filled_price(self):
        return self.filled_price

    def get_status(self):
        return self.status

    def get_order_type(self):
        return self.order_type

    def get_order_symbol(self):
        return self.symbol

    def get_exchange(self):
        return self.exchange

    def get_origin_quantity(self):
        return self.origin_quantity

    def get_origin_price(self):
        return self.origin_price

    def get_order_notifier(self):
        return self.order_notifier

    def get_canceled_time(self):
        return self.canceled_time

    def get_executed_time(self):
        return self.executed_time

    def get_creation_time(self):
        return self.creation_time

    def set_last_prices(self, last_prices):
        self.last_prices = last_prices

    def get_create_last_price(self):
        return self.created_last_price

    def get_profitability(self):
        if self.get_filled_price() is not 0 and self.get_create_last_price() is not 0:
            if self.get_filled_price() >= self.get_create_last_price():
                self.order_profitability = 1 - self.get_filled_price() / self.get_create_last_price()
                if self.side == TradeOrderSide.SELL:
                    self.order_profitability *= -1
            else:
                self.order_profitability = 1 - self.get_create_last_price() / self.get_filled_price()
                if self.side == TradeOrderSide.BUY:
                    self.order_profitability *= -1
        return self.order_profitability

    @classmethod
    def get_name(cls):
        return cls.__name__


class BuyMarketOrder(Order):
    def __init__(self, exchange):
        super().__init__(exchange)
        self.side = TradeOrderSide.BUY

    def update_order_status(self):
        if not self.trader.simulate:
            result = self.exchange.get_order(self.order_id)
            new_status = self.trader.parse_status(result)
            if new_status == OrderStatus.FILLED:
                self.trader.parse_exchange_order_to_trade_instance(result)
        else:
            # ONLY FOR SIMULATION
            self.status = OrderStatus.FILLED
            self.filled_price = float(self.last_prices[-1]["price"])
            self.filled_quantity = self.origin_quantity
            self.executed_time = time.time()


class BuyLimitOrder(Order):
    def __init__(self, exchange):
        super().__init__(exchange)
        self.side = TradeOrderSide.BUY

    def update_order_status(self):
        if not self.trader.simulate:
            result = self.exchange.get_order(self.order_id)
            new_status = self.trader.parse_status(result)
            if new_status == OrderStatus.FILLED:
                self.trader.parse_exchange_order_to_trade_instance(result)
        else:
            # ONLY FOR SIMULATION
            if self.check_last_prices(self.origin_price, True):
                self.status = OrderStatus.FILLED
                self.filled_price = self.origin_price
                self.filled_quantity = self.origin_quantity
                self.executed_time = time.time()


class SellMarketOrder(Order):
    def __init__(self, exchange):
        super().__init__(exchange)
        self.side = TradeOrderSide.SELL

    def update_order_status(self):
        if not self.trader.simulate:
            result = self.exchange.get_order(self.order_id)
            new_status = self.trader.parse_status(result)
            if new_status == OrderStatus.FILLED:
                self.trader.parse_exchange_order_to_trade_instance(result)
        else:
            # ONLY FOR SIMULATION
            self.status = OrderStatus.FILLED
            self.filled_price = float(self.last_prices[-1]["price"])
            self.filled_quantity = self.origin_quantity
            self.executed_time = time.time()


class SellLimitOrder(Order):
    def __init__(self, exchange):
        super().__init__(exchange)
        self.side = TradeOrderSide.SELL

    def update_order_status(self):
        if not self.trader.simulate:
            result = self.exchange.get_order(self.order_id)
            new_status = self.trader.parse_status(result)
            if new_status == OrderStatus.FILLED:
                self.trader.parse_exchange_order_to_trade_instance(result)
        else:
            # ONLY FOR SIMULATION
            if self.check_last_prices(self.origin_price, False):
                self.status = OrderStatus.FILLED
                self.filled_price = self.origin_price
                self.filled_quantity = self.origin_quantity
                self.executed_time = time.time()


class StopLossOrder(Order):
    def __init__(self, exchange):
        super().__init__(exchange)
        self.side = TradeOrderSide.SELL

    def update_order_status(self):
        if self.check_last_prices(self.origin_price, True):
            self.status = OrderStatus.FILLED
            self.filled_price = self.origin_price
            self.filled_quantity = self.origin_quantity
            self.executed_time = time.time()
            if not self.trader.simulate:
                market_sell = self.trader.create_order_instance(order_type=TraderOrderType.SELL_MARKET,
                                                                symbol=self.symbol,
                                                                current_price=self.origin_price,
                                                                quantity=self.origin_quantity,
                                                                price=self.origin_price)
                self.trader.create_order(market_sell)


# TODO
class StopLossLimitOrder(Order):
    def __init__(self, exchange):
        super().__init__(exchange)
        self.side = TradeOrderSide.SELL

    def update_order_status(self):
        pass


# TODO
class TakeProfitOrder(Order):
    def __init__(self, exchange):
        super().__init__(exchange)
        self.side = TradeOrderSide.SELL

    def update_order_status(self):
        pass


# TODO
class TakeProfitLimitOrder(Order):
    def __init__(self, exchange):
        super().__init__(exchange)
        self.side = TradeOrderSide.SELL

    def update_order_status(self):
        pass


class OrderConstants:
    TraderOrderTypeClasses = {
        TraderOrderType.BUY_MARKET: BuyMarketOrder,
        TraderOrderType.BUY_LIMIT: BuyLimitOrder,
        TraderOrderType.TAKE_PROFIT: TakeProfitOrder,
        TraderOrderType.TAKE_PROFIT_LIMIT: TakeProfitLimitOrder,
        TraderOrderType.STOP_LOSS: StopLossOrder,
        TraderOrderType.STOP_LOSS_LIMIT: StopLossLimitOrder,
        TraderOrderType.SELL_MARKET: SellMarketOrder,
        TraderOrderType.SELL_LIMIT: SellLimitOrder,
    }
