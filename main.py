import sys
import json
import signal
import os
import threading
import time
from datetime import datetime, timezone
from logging import config, getLogger

import requests

from constants import *
from api import InversePerp, BybitAPIError


config.fileConfig( 'logging.conf', disable_existing_loggers=False)
logger = getLogger('frbot')


def send_message(msg):
    if os.environ['SLACK_WEBHOOK_URL']:
        requests.post(os.environ['SLACK_WEBHOOK_URL'], data=json.dumps({'text': msg}))


class FundingRateBot():

    def __init__(self, api_key: str, api_secret: str, test: bool = True):
        self.test = test
        self.alive = True
        self.min_entry_fr: float = 0.0000
        self.min_exit_fr: float = 0.0000
        self.client = InversePerp(api_key, api_secret, test)
        self.perp_symbols = {s['name']: s for s in self.client.public_symbols()}
        self.alive = True

    def get_perp_best_price(self, symbol: str, side: str) -> str:
        res = self.client.public_orderbook_l2(symbol)
        best = [r for r in res if r['side'] == side][0]
        name = 'Bid' if side == 'Buy' else 'Ask'
        logger.info(f"Best {name} of {best['symbol']}: price={best['price']}, size={best['size']}")
        return best['price']

    def create_invperp_order(self, symbol: str, side: str, usdqty: int, price: float) -> str:
        logger.info(f'Create an invert perpetual order to {side.lower()} {symbol}. qty={usdqty}, price={price}')
        res = self.client.private_order_create(symbol=symbol,
                                                side=side,
                                                order_type='Limit',
                                                qty=usdqty,
                                                price=price,
                                                time_in_force='PostOnly')
        return res['order_id']

    def create_perp_short(self, symbol: str):
        logger.info(f'Create short position of {symbol}.')

        # create new sell order
        price = self.get_perp_best_price(symbol, 'Sell')
        qty = self.__calc_qty(symbol[:3], price)  # NOTE: min_trading_qty = US dollar
        min_qty = self.perp_symbols[symbol]['lot_size_filter']['min_trading_qty']
        if qty < min_qty:
            logger.info(f"Can't create an order because qty({qty}) is less than min_trading_qty({min_qty}).")
            return

        order_id = self.create_invperp_order(symbol, 'Sell', qty, price)
        logger.info('Sleep for 20 seconds.')
        time.sleep(20)

        while self.alive:

            # get active orders
            logger.info(f'Get active order: order_id={order_id}')
            order = self.client.private_order(symbol=symbol, order_id=order_id)
            logger.info(f'Active Order:\n{json.dumps(order, indent=True)}')

            if order['order_status'] == 'Filled' and order['leaves_qty'] == 0:
                logger.info(f'Order was filled. order_id={order_id}')
                send_message(f"Created short position for {order['qty']} {order['symbol']}.")
                break

            elif order['order_status'] == 'Cancelled':
                logger.info(f"Order was cancelled. order_id={order_id}, reason={order['reject_reason']}")
                price = self.get_perp_best_price(symbol, order['side'])
                qty = self.__calc_qty(symbol[:3], price)
                order_id = self.create_invperp_order(symbol, order['side'], qty, price)

            else:
                logger.info(f'Order is not filled yet. order_id={order_id}')

                price = self.get_perp_best_price(symbol, order['side'])
                if order['price'] != price:
                    logger.info(f'Update order price. order_id={order_id}')

                    # cancel & create order
                    logger.info(f'Cancel sell order to change price. order_id={order_id}')
                    res = self.client.private_order_cancel(symbol=symbol, order_id=order_id)
                    time.sleep(2)

                    qty = self.__calc_qty(symbol[:3], price)
                    min_qty = self.perp_symbols[symbol]['lot_size_filter']['min_trading_qty']
                    if qty < min_qty:
                        logger.info(f"Can't create an order because qty({qty}) is less than min_trading_qty({min_qty}).")
                        return

                    order_id = self.create_invperp_order(symbol, order['side'], qty, price)

            logger.info('Sleep for 20 seconds.')
            time.sleep(20)

    def __calc_qty(self, coin: str, price) -> int:
        '''
        Returns
        -------
        int
            quantity of US dollar
        '''
        balance = self.client.private_wallet_balance()[coin]['available_balance']
        logger.info(f'Available balance: account=derivative, coin={coin}, balance={balance :.8f}')
        qty = float(price) * balance
        market_order_cost = qty * DERIVATIVE_TAKER_FEE_RATE # market order cost = qty * 0.075%
        return int(qty - market_order_cost)

    def close_perp_short(self, symbol: str, usdqty):
        logger.info(f'Close short position of {usdqty} {symbol}.')

        price = self.get_perp_best_price(symbol, 'Buy')
        order_id = self.create_invperp_order(
                symbol=symbol, side='Buy', usdqty=usdqty, price=price)

        while self.alive:
            logger.info('Sleep for 20 seconds.')
            time.sleep(20)

            # get active orders
            logger.info(f'Get active order: order_id={order_id}')
            order = self.client.private_order(symbol=symbol, order_id=order_id)
            logger.info(f'Active Order:\n{json.dumps(order, indent=True)}')

            if order['order_status'] == 'Filled' and order['leaves_qty'] == 0:
                logger.info(f'Order was filled. order_id={order_id}')
                send_message(f"Short position was closed for {order['qty']} {order['symbol']}.")
                break

            elif order['order_status'] == 'Cancelled':
                logger.info(f"Order was cancelled. order_id={order_id}, reason={order['reject_reason']}")
                price = self.get_perp_best_price(symbol, order['side'])
                order_id = self.create_invperp_order(symbol, order['side'], str(order['qty']), price)

            else:
                logger.info(f'Order is not filled yet. order_id={order_id}')
                price = self.get_perp_best_price(symbol, order['side'])
                if order['price'] != price:
                    logger.info(f'Update order price. order_id={order_id}')

                    logger.info(f"Replace {order['side']} order: symbol={symbol}, price={price}, qty={usdqty}")
                    res = self.client.private_order_replace(
                            symbol=symbol,
                            order_id=order_id,
                            p_r_qty=usdqty,
                            p_r_price=price)
                    logger.info(f"Order was replaced:\n{json.dumps(res, indent=True)}")
                    order_id = res['order_id']

                else:
                    logger.info('No need to update order.')

    def maintain_position(self, symbol: str) -> None:

        # get previous fr
        prev_fr = self.client.public_funding_prevfundingrate(symbol=symbol)
        fr = float(prev_fr['funding_rate'])
        fr_t = datetime.fromtimestamp(prev_fr['funding_rate_timestamp']).astimezone(timezone.utc)
        logger.info(f"Previous {prev_fr['symbol']} FR: {fr:.6%} ({fr_t.isoformat()})")

        # get current position
        pos = self.client.private_position_list(symbol)
        logger.info(f"Current {symbol} position size: {pos['size']}")

        # close position since fr is less than self.min_exit_fr.
        if pos['size'] > 0 and fr < self.min_exit_fr:
            self.close_perp_short(symbol=symbol, usdqty=pos['size'])

        # create short position
        if fr >= self.min_entry_fr:
            self.create_perp_short(symbol)

        # send notification
        msg = f"{symbol}'s previous FR is {fr:.6%} and will be executed at {fr_t.isoformat()}. Current position size is {pos['size']}."
        logger.info(msg)

    def receive_signal(self, signum, stack):
        logger.info(f"Received {signum} signal.")
        logger.info('Stop bot.')
        for s in INV_PERP_SYMBOLS:
            try:
                self.client.private_order_cancelall(s)
            except Exception as e:
                logger.error(f'Failed to cancel order for {s}')
                logger.exception(e)
        sys.exit(0)

    def send_pos_maintenance_result(self) -> None:

        # get previous fr
        frs = [self.client.public_funding_prevfundingrate(symbol=s) for s in INV_PERP_SYMBOLS]
        fr_time = datetime.fromtimestamp(
                frs[0]['funding_rate_timestamp']).astimezone(timezone.utc)
        fr_s = ', '.join([f"{f['symbol']}={float(f['funding_rate']):.6%}" for f in frs])

        # position
        pos = self.client.private_position_list()
        p_s = [f"{p['data']['symbol']}={p['data']['size']}" for p in pos if p['data']['size'] > 0]

        # balance
        balance = self.client.private_wallet_balance()
        s = '%s: balance=%.6f, unrealised_pnl=%.6f'
        b_s = [s % (k, v['wallet_balance'], v['unrealised_pnl']) for k, v in balance.items() if v['wallet_balance']]

        now = datetime.now(timezone.utc)
        msg = f"""bybit-fr-bot maintained result ({now.strftime('%Y-%m-%d %H:%M:%S')} UTC).
```
[PrevFR]
{fr_s} ({fr_time.strftime('%Y-%m-%d %H:%M:%S')} UTC)

[Balance(derivative)]
{', '.join(b_s)}

[Positions]
{', '.join(p_s)}
```
"""
        send_message(msg)

    def run(self):
        signal.signal(signal.SIGTERM, self.receive_signal)
        signal.signal(signal.SIGINT, self.receive_signal)

        env = 'TESTNET' if self.test else 'MAINNET'
        m = f'Run bybit-frbot in {env}.'
        logger.info(m)
        send_message(m)

        BEFORE_FR_HOURS = [7, 15, 23]
        START_MIN = 45

        last_maintened_time = None
        while self.alive:

            now = datetime.now(tz=timezone.utc)
            if now.hour in BEFORE_FR_HOURS and now.minute >= START_MIN \
                    and (not last_maintened_time or now.hour != last_maintened_time.hour):
                logger.info(f"Start to maintain position.")

                threads = []
                for symbol in INV_PERP_SYMBOLS:
                    t = threading.Thread(target=self.maintain_position, args=(symbol,))
                    threads.append(t)
                    t.start()
                for t in threads:
                    t.join()

                last_maintened_time = now
                self.send_pos_maintenance_result()
                logger.info(f"Sleep until next funding time approaches.")

            time.sleep(5)


if __name__ == '__main__':
    try:
        bot = FundingRateBot(api_key=os.environ['BYBIT_APIKEY'],
                             api_secret=os.environ['BYBIT_SECRET'],
                             test=os.environ['BYBIT_TEST'].lower() == 'true')
        bot.run()
    except Exception as e:
        logger.exception(e)
        send_message(f"An error has occurred.\n```{e}```")
