#
# URL
#

MAINNET_API: str = 'https://api.bybit.com'
'''mainnet restfull api base url'''

MAINNET_WSS: str = 'wss://stream.bybit.com/realtime'
'''mainnet websocket url'''

TESTNET_API: str = 'https://api-testnet.bybit.com'
'''testnet restfull api base url'''

TESTNET_WSS: str = 'wss://stream-testnet.bybit.com/realtime'
'''testnet websocket url'''

#
# Symbols
#

SYMBOL_BTCUSD: str = 'BTCUSD'
'''symbol: BTCUSD'''

SYMBOL_ETHUSD: str = 'ETHUSD'
'''symbol: ETHUSD'''

SYMBOL_XRPUSD: str = 'XRPUSD'
'''symbol: XRPUSD'''

SYMBOL_EOSUSD: str = 'EOSUSD'
'''symbol: EOSUSD'''

SYMBOL_BTCUSDT: str = 'BTCUSDT'
'''symbol: BTC/USDT'''

SYMBOL_ETHUSDT: str = 'ETHUSDT'
'''symbol: ETH/USDT'''

SYMBOL_XRPUSDT: str = 'XRPUSDT'
'''symbol: XRP/USDT'''

SYMBOL_EOSUSDT: str = 'EOSUSDT'
'''symbol: EOS/USDT'''

INV_PERP_SYMBOLS = [SYMBOL_BTCUSD, SYMBOL_ETHUSD, SYMBOL_XRPUSD, SYMBOL_EOSUSD]
'''inverse perpetual symbols'''

#
# Account Type
#

ACCOUNT_TYPE_SPOT = 'SPOT'
'''Account Type: SPOT'''

ACCOUNT_TYPE_CONTRACT = 'CONTRACT'
'''Account Type: CONTRACT'''

#
# API Parameter Value
#

ORDER_TYPE_LIMIT = 'LIMIT'
'''order type: LIMIT'''

ORDER_TYPE_MARKET = 'MARKET'
'''order type: MARKET'''

ORDER_TYPE_LIMIT_MAKER=  'LIMIT_MAKER'
'''order type: LIMIT_MAKER'''

#
# Fee Rate
#

SPOT_MAKER_FEE_RATE = 0.000

SPOT_TAKER_FEE_RATE = 0.001

DERIVATIVE_MAKER_FEE_RATE = -0.00025

DERIVATIVE_TAKER_FEE_RATE = 0.00075
