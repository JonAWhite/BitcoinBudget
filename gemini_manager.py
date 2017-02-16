from geminipy import Geminipy
import argparse
import math
import sys
from decimal import *


getcontext().prec = 28 
getcontext().mode = ROUND_HALF_EVEN

def find_balance(balances, currency):
    for x in range(len(balances)):
        balance = balances[x]
        if balance[u'currency'] == currency:
            return balance

def balance_minus_fees(balance, fee):
    one_plus_fee = Decimal('1')+fee
    balance_minus_fee = balance / one_plus_fee 
    return balance_minus_fee.quantize(Decimal('1.00'))

def get_trade_and_fees(usd_to_spend, fee=Decimal('0.0025')):
    usd_to_trade = balance_minus_fees(usd_to_spend, fee)
    usd_in_fees = usd_to_spend - usd_to_trade
    trade_and_fees = {"trade": usd_to_trade, "fees": usd_in_fees}
    return trade_and_fees 

def get_ask_price_and_amount(con):
    book = con.book(limit_bids=1, limit_asks=1)
    book.raise_for_status()
    current_ask = book.json()[u'asks'][0]
    current_ask_amount = Decimal(current_ask[u'amount'])
    current_ask_price = Decimal(current_ask[u'price'])
    return {"price":current_ask_price, "amount":current_ask_amount}

def get_currency_available_for_withdrawl(con, currency):
    balances = con.balances()
    balances.raise_for_status()
    currency_balance = find_balance(balances.json(), currency=currency) 
    currency_balance_available = Decimal(currency_balance[u'availableForWithdrawal'])
    return currency_balance_available

def validate_usd_to_spend(con, usd_to_spend): 
    # Get USD Available for Withdrawl
    usd_balance_available = get_currency_available_for_withdrawl(con, u'USD')
    print 'Available: $' + str(usd_balance_available)
    
    # Confirm that you have enough USD in your account
    if usd_to_spend > usd_balance_available:
        usd_missing = usd_to_spend - usd_balance_available
        print '[ERROR] You need an additional $' + str(usd_missing) + ' to make that trade'
        sys.exit(1)

def validate_btc_to_buy(btc_to_buy, current_ask_amount): 
    if btc_to_buy > current_ask_amount:
        btc_unavailable = btc_to_buy - current_ask_amount
        print '[ERROR] There is ' + str(btc_unavailable) + ' BTC missing at that price'
        sys.exit(1)

def purchase_btc(con, btc_to_buy, current_ask_price):
    print "Buying " + str(btc_to_buy) + " BTC @ $" + str(current_ask_price)
    order = con.new_order(amount=str(btc_to_buy), price=str(current_ask_price), side='buy')
    print order.json()
    return

def spend_usd(con, usd_to_spend):
    # Validate USD to spend 
    validate_usd_to_spend(con, usd_to_spend)

    # Get Trade and Fees
    trade_and_fees = get_trade_and_fees(usd_to_spend)
    usd_to_trade = trade_and_fees["trade"]
    usd_in_fees = trade_and_fees["fees"]    
    print 'Spend: $' + args.usd_to_spend + ' => Trade: $' + str(usd_to_trade) + '; Fees: $' + str(usd_in_fees)
    
    # Get Current Ask
    ask_price_and_amount = get_ask_price_and_amount(con)
    current_ask_price = ask_price_and_amount["price"]
    current_ask_amount = ask_price_and_amount["amount"]
    btc_to_buy = (usd_to_trade / current_ask_price).quantize(Decimal('1.00000000'))
    print 'BTC to Buy: ' + str(btc_to_buy) 
    print 'Ask: ' + str(current_ask_amount) + ' @ $' + str(current_ask_price) 
    
    # Make sure there is enough BTC to cover trade
    validate_btc_to_buy(btc_to_buy, current_ask_amount)
    
    #Place Trade
    purchase_btc(con, btc_to_buy, current_ask_price)

def validate_btc_to_withdraw(con, btc_amount): 
    btc_balance_available = get_currency_available_for_withdrawl(con, u'BTC')
    if btc_amount > btc_balance_available:
        print '[ERROR] You only have ' + str(btc_balance_available) + ' BTC available to withdraw.'
        sys.exit(1)

def withdraw_btc(con, btc_amount, withdrawl_address):
    validate_btc_to_withdraw(con, btc_amount)
    print "Withdrawing " + str(btc_amount) + " BTC to " + withdrawl_address
    withdrawl = con.withdraw(currency='btc', address=withdrawl_address, amount=str(btc_amount))
    print withdrawl.json() 
    return

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--usd_to_spend", help='The amount of USD to use to buy BTC')
    parser.add_argument("--btc_to_withdraw", nargs=2, help='The amount of BTC to withdraw and the address to withdraw to (ex: .01 1HDLnpVFgqgnfiKjxJUPmb82P7XamASuZf)')
    parser.add_argument("gemini_api_key", help='Get this from gemini.com')
    parser.add_argument("gemini_api_secret", help='Get this from gemini.com')
    args = parser.parse_args()
    return args

args = get_args()
con = Geminipy(api_key=args.gemini_api_key, secret_key=args.gemini_api_secret, live=True)
if args.usd_to_spend:
    usd_to_spend = Decimal(args.usd_to_spend)
    spend_usd(con, usd_to_spend)

if args.btc_to_withdraw:
    btc_amount = Decimal(args.btc_to_withdraw[0]).quantize(Decimal('1.00000000'))
    withdrawl_address = args.btc_to_withdraw[1]
    withdraw_btc(con, btc_amount, withdrawl_address) 

