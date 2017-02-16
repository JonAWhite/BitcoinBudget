from coinbase.wallet.client import Client
import argparse
import json

def find_account(accounts, name):
    for x in range(len(accounts)):
        account = accounts[x] 
        if account.name == name:
            return account

parser = argparse.ArgumentParser()
parser.add_argument("budget_file", help='JSON file in the form [{"name":"Budget Item 1", "amount_usd":5.50}]')
parser.add_argument("bitcoin_paid_price", help='The price you paid for the coins')
parser.add_argument("coinbase_api_key", help='Get this from coinbase.com')
parser.add_argument("coinbase_api_secret", help='Get this from coinbase.com')
args = parser.parse_args()

with open(args.budget_file) as data_file:
    budget_accounts = json.load(data_file)

client = Client(args.coinbase_api_key, args.coinbase_api_secret)
primary_account = client.get_primary_account()
bitcoin_spot_price_in_usd = client.get_spot_price(currency_pair = 'BTC-USD')["amount"]
bitcoin_paid_price_in_usd = args.bitcoin_paid_price
accounts_obj = client.get_accounts(limit="100")
assert (accounts_obj.pagination is None) or isinstance(accounts_obj.pagination, dict)
accounts = accounts_obj[::]

total_usd = 0
for budget_account in budget_accounts:
    total_usd += budget_account["amount_usd"]

total_btc = 0
for budget_account in budget_accounts:
    budget_account_name = budget_account["name"]
    budget_account_id = find_account(accounts, budget_account_name).id
    budget_account_amount_usd = budget_account["amount_usd"]
    budget_account_amount_btc = float("{0:.8f}".format(budget_account_amount_usd / float(bitcoin_paid_price_in_usd)))
    total_btc += budget_account_amount_btc
    print 'Transfering ' + str(budget_account_amount_btc) + ' BTC from ' + primary_account.name + ' (' + primary_account.id + ') to ' + budget_account_name + ' (' + budget_account_id + ')' 
    #client.transfer_money(primary_account.id, to=budget_account_id, amount=str(budget_account_amount_btc), currency="BTC")

print 'BTC-USD Spot Price: ' + str(bitcoin_spot_price_in_usd)
print 'BTC-USD Paid Price: ' + bitcoin_paid_price_in_usd
print 'Budget Total: $' + str("%.2f" % total_usd) 
print 'Budget Total: ' + str("%.8f" % total_btc) + ' BTC' 
