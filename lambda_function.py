import os
from py3cw.request import Py3CW

def lambda_handler(event, context): 

    ####################
    # 3c configuration #
    ####################
    threecommas_key = os.environ['key']
    threecommas_secret = os.environ['secret']
    
#####################
#  test run only?   #
#####################
test_run = 'no'


#####################
# bot configuration #
#####################
account_name = 'Paper Account' # your account name
bot_name = 'Paper_DCA_Bot' # your bot name
bot_id = 'xxxxxxx' # 3commas ID of the bot you want to auto calculate the Base and Safety orders - get it from the bot url (https://3commas.io/bots/xxxxxxx/edit)
bot_take_profit = '1.7'
bot_trailing_enabled = True
bot_trailing_deviation = '0.5'
bot_max_safety_orders_count = 25
bot_max_active_deals = 6
bot_active_safety_orders_count = 1
bot_pairs = ['USDT_AAVE', 'USDT_AKRO', ...] # list your pairs here
bot_safety_order_size = int(2)
bot_strategy_list = [{'options': {'time': '1m', 'type': 'strong_buy'}, 'strategy': 'trading_view'}, {'options': {'time': '5m', 'type': 'strong_buy'}, 'strategy': 'trading_view'}, {'options': {'time': '15m', 'type': 'strong_buy'}, 'strategy': 'trading_view'}, {'options': {'time': '1h', 'type': 'strong_buy'}, 'strategy': 'trading_view'}, {'options': {'time': '4h', 'type': 'buy_or_strong_buy'}, 'strategy': 'trading_view'}, {'options': {'time': '1d', 'type': 'buy_or_strong_buy'}, 'strategy': 'trading_view'}] # list your strategy here
bot_martingale_volume_coefficient = '1.05'
bot_martingale_step_coefficient = '1.0'
bot_safety_order_step_percentage = '2'
bot_take_profit_type = 'total'


######################
# risk configuration #
######################
# How much of your bankroll do you want to use
risk_percentage = 325


###################################
# init python wrapper for 3commas #
###################################
p3cw = Py3CW(
    key=threecommas_key,
    secret=threecommas_secret,
    request_options={
        'request_timeout': 10,
        'nr_of_retries': 1,
        'retry_status_codes': [502]
    }
)


######################
# auto configuration #
######################

error, data_accounts = p3cw.request(
    entity='accounts',
    action=''
)

for datapoint_account in data_accounts:
    if datapoint_account['name'] == account_name:
        account_balance = round(float(datapoint_account['usd_amount']),2)
        account_id = str(datapoint_account['id'])  # Account ID of your Exchange in 3commas
        # print("Account Balance ($):", account_balance)

if account_balance > 0:
    pass
else:
    exit("Bad account information, balance = 0")

p3cw.request
error, data_bots = p3cw.request(
    entity='bots',
    action=''
)


######################
#  auto calculation  #
######################
print("----------START-----------")
base_order_size = int(bot_safety_order_size / bot_safety_order_size)
adj_safety_order_size = bot_safety_order_size
total_final_required_balance_array = []
total_final_required_balance = 0

# Calculate Safety Order Maximum Volume
for adj_safety_order_size in range(bot_safety_order_size, bot_safety_order_size + 100000):
    step_value = float(0)
    total_value = float(0)
    step_value = step_value + adj_safety_order_size

    total_value = round(float(base_order_size), 2)
    x = 0
    for x in range(1, bot_max_safety_orders_count + 1):
        base_order_size = int(adj_safety_order_size / 2)
        if x == 1:
            step_value = round(step_value, 2)
        else:
            step_value = round((step_value * 1.05), 2)
        total_value = round(total_value + step_value, 2)
        # print("#", x, " - ", float(step_value), " - ", float(total_value))
        total_final_required_balance = round(total_value * int(bot_max_active_deals), 2)

    if total_final_required_balance > (account_balance*(float(risk_percentage)/100)):
        print("Recommended Safety Order ($):", adj_safety_order_size - 1)
        break
    else:
        total_final_required_balance_array.append(total_final_required_balance)
        total_final_required_balance = 0

total_final_required_balance = 0
adj_base_order_size = base_order_size
final_safety_order = adj_safety_order_size - 1

# Calculate Base Order Maximum Volume
for adj_base_order_size in range(base_order_size, base_order_size + 1000000):
    step_value = float(0)
    total_value = float(0)
    step_value = step_value + final_safety_order
    total_value = round(float(adj_base_order_size), 2)
    x = 0
    for x in range(1, bot_max_safety_orders_count + 1):
        if x == 1:
            step_value = round(step_value, 2)
        else:
            step_value = round((step_value * 1.05), 2)
        total_value = round(total_value + step_value, 2)
        total_final_required_balance = round(total_value * int(bot_max_active_deals), 2)

    if (total_final_required_balance > (account_balance*(float(risk_percentage)/100))) or ((adj_base_order_size+1)>adj_safety_order_size/2):
        print("Recommended Base Order ($):", adj_base_order_size - 1)
        print("This configuration will use: $", total_final_required_balance_array[-1], ", which is $", round((account_balance*(risk_percentage/100))-total_final_required_balance_array[-1], 2), "below allowed maximum: $", round(account_balance + ((account_balance*(risk_percentage/100))-account_balance),2), "(account balance of $", account_balance, "+", risk_percentage, "% risk: $", round((account_balance*(risk_percentage/100))-account_balance,2), ")")
        break
    else:
        total_final_required_balance_array.append(total_final_required_balance)
        total_final_required_balance = 0


######################
# update 3commas bot #
######################

if 'yes' in test_run:
    print("Test Run Completed!")
else:
    error, update_bot = p3cw.request(
        entity='bots',
        action='update',
        action_id=bot_id,
        payload={
            'account_id': account_id,
            'bot_id': bot_id,
            'name': bot_name,
            'pairs': bot_pairs,
            'base_order_volume': adj_base_order_size - 1,  # this is auto calculated value that we're changing
            'safety_order_volume': adj_safety_order_size - 1,  # this is auto calculated value that we're changing
            'take_profit': bot_take_profit,
            'martingale_volume_coefficient': bot_martingale_volume_coefficient,
            'martingale_step_coefficient': bot_martingale_step_coefficient,
            'max_safety_orders': bot_max_safety_orders_count,
            'active_safety_orders_count': bot_active_safety_orders_count,
            'safety_order_step_percentage': bot_safety_order_step_percentage,
            'take_profit_type': bot_take_profit_type,
            'strategy_list': bot_strategy_list,
            'max_active_deals': str(bot_max_active_deals),
            'trailing_enabled': bot_trailing_enabled,
            'trailing_deviation': bot_trailing_deviation
        }
    )
    if error == {}:
        print("Bot update completed!")
    else:
        print(error)
        print("Bot update NOT completed!")