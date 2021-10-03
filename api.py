from logging import getLogger
import json
import hashlib
import hmac
import time

import requests
from requests import status_codes

from constants import MAINNET_API, TESTNET_API


logger = getLogger(__name__)


class BybitAPIError(Exception):
    pass


class ByBit(object):

    def __init__(self, api_key: str, api_secret: str, test: bool = True):
        self.__api_key = api_key
        self.__api_secret = api_secret
        self.__test = test
        self.__base_url = TESTNET_API if test else MAINNET_API

    def _base_url(self) -> str:
        return TESTNET_API if self.__test else MAINNET_API

    def _auth_get_parmas(self, params = {}) -> str:
        param_str = self._sorted_param_str(params)
        return f'{param_str}&sign={self._sign(param_str)}'

    def _auth_post_data(self, params = {}) -> dict:
        param_str = self._sorted_param_str(params)
        params.update({'sign': self._sign(param_str)})
        return params

    def _sorted_param_str(self, params: dict) -> str:
        params.update({
            'api_key': self.__api_key,
            'timestamp': str(round(time.time() * 1000)),
        })
        s = ''
        for k in sorted(params.keys()):
            v = params[k]
            if isinstance(params[k], bool):
                v = 'true' if v else 'false'
            s += f"{k}={v}&"
        return s[:-1]

    def _sign(self, param_str: str) -> str:
        hash = hmac.new(
                bytes(self.__api_secret, "utf-8"),
                param_str.encode("utf-8"), hashlib.sha256)
        return hash.hexdigest()

    def _handle_response(self, res) -> dict:
        res.raise_for_status()
        body = json.loads(res.text)
        logger.debug('Response body: ' + json.dumps(body, indent=True))
        if body['ret_code'] != 0:
            raise BybitAPIError(f"Failed to call api: {body}")
        return body['result']


class InversePerp(ByBit):

    def __init__(self, api_key: str, api_secret: str, test: bool = True):
        super().__init__(api_key, api_secret, test)

    def private_wallet_balance(self):
        path = '/v2/private/wallet/balance'
        url = f'{self._base_url()}{path}?{self._auth_get_parmas()}'
        logger.debug(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def private_wallet_fund_records(self):
        path = '/v2/private/wallet/fund/records'
        url = f'{self._base_url()}{path}?{self._auth_get_parmas()}'
        logger.debug(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def private_funding_prevfunding(self, symbol: str):
        params = {'symbol': symbol}
        path = '/v2/private/funding/prev-funding'
        url = f'{self._base_url()}{path}?{self._auth_get_parmas(params)}'
        logger.debug(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def private_position_list(self, symbol: str = None):
        params = {}
        if symbol:
            params.update({'symbol': symbol})
        path = '/v2/private/position/list'
        url = f'{self._base_url()}{path}?{self._auth_get_parmas(params)}'
        logger.debug(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def private_order(self, symbol: str, order_id: str = None, order_link_id: str = None):
        params = {'symbol': symbol,}
        if order_id:
            params.update({'order_id': order_id})
        if order_link_id:
            params.update({'order_link_id': order_link_id})
        path = '/v2/private/order'
        url = f'{self._base_url()}{path}?{self._auth_get_parmas(params)}'
        logger.debug(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def public_symbols(self) -> list:
        path = '/v2/public/symbols'
        url = f'{self._base_url()}{path}'
        logger.debug(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def public_funding_prevfundingrate(self, symbol: str):
        params = {'symbol': symbol}
        path = '/v2/public/funding/prev-funding-rate'
        url = f'{self._base_url()}{path}?{self._sorted_param_str(params)}'
        logger.debug(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def public_tickers(self, symbol: str = None):
        p = ''
        if symbol:
            p = '?' + self._sorted_param_str({'symbol': symbol})
        path = '/v2/public/tickers'
        url = f'{self._base_url()}{path}{p}'
        logger.info(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def public_orderbook_l2(self, symbol: str = None):
        p = ''
        if symbol:
            p = '?' + self._sorted_param_str({'symbol': symbol})
        path = '/v2/public/orderBook/L2'
        url = f'{self._base_url()}{path}{p}'
        logger.info(f'GET {url}')
        res = requests.get(url=url)
        return self._handle_response(res)

    def private_order_create(self,
                             symbol: str,
                             side: str,
                             order_type: str,
                             qty: str,
                             price: str,
                             time_in_force: str = None):
        params = {
                'symbol': symbol,
                'side': side,
                'order_type': order_type,
                'qty': qty,
                'price': price,
                }

        if time_in_force:
            params.update({'time_in_force': time_in_force})

        headers = {"Content-Type": "application/json"}
        path = '/v2/private/order/create'
        data = self._auth_post_data(params)
        url = f'{self._base_url()}{path}'
        logger.debug(f'POST {url}\n{json.dumps(data, indent=True)}')
        res = requests.post(headers=headers, url=url, data=json.dumps(data))
        return self._handle_response(res)

    def private_order_cancel(self,
                             symbol: str,
                             order_id: str = None,
                             order_link_id: str = None):
        params = {'symbol': symbol,}
        if order_id:
            params.update({'order_id': order_id})
        if order_link_id:
            params.update({'order_link_id': order_link_id})

        headers = {"Content-Type": "application/json"}
        path = '/v2/private/order/cancel'
        data = self._auth_post_data(params)
        url = f'{self._base_url()}{path}'
        logger.debug(f'POST {url}\n{json.dumps(data, indent=True)}')
        res = requests.post(headers=headers, url=url, data=json.dumps(data))
        return self._handle_response(res)

    def private_order_replace(self,
                              symbol: str,
                              order_id: str = None,
                              order_link_id: str = None,
                              p_r_qty: str = None,
                              p_r_price: str = None):
        params = {'symbol': symbol,}
        if order_id:
            params.update({'order_id': order_id})
        if order_link_id:
            params.update({'order_link_id': order_link_id})
        if p_r_qty:
            params.update({'p_r_qty': p_r_qty})
        if p_r_price:
            params.update({'p_r_price': p_r_price})

        headers = {"Content-Type": "application/json"}
        path = '/v2/private/order/replace'
        data = self._auth_post_data(params)
        url = f'{self._base_url()}{path}'
        logger.debug(f'POST {url}\n{json.dumps(data, indent=True)}')
        res = requests.post(headers=headers, url=url, data=json.dumps(data))
        return self._handle_response(res)

    def private_order_cancelall(self, symbol: str):
        params = {'symbol': symbol,}
        headers = {"Content-Type": "application/json"}
        path = '/v2/private/order/cancelAll'
        data = self._auth_post_data(params)
        url = f'{self._base_url()}{path}'
        logger.debug(f'POST {url}\n{json.dumps(data, indent=True)}')
        res = requests.post(headers=headers, url=url, data=json.dumps(data))
        return self._handle_response(res)
