# **TradeKillSwitch** - a Python 🐍 script for closing open trades impacted by news events 📰

> [!IMPORTANT]
> This project is provided "as is" without any warranty, express or implied. The creator of this project shall not be held liable for any damages arising from the use of this code.


## Description

### This script works on DXtrade, Match-Trader and TradeLocker.
### It fetches news events from ForexFactory and closes the open positions of impacted symbols, minutes/hours before the events.

### Screenshot:
![tks_screenshot](https://github.com/SheikAlgo/TradeKillSwitch/assets/166510758/dfbb0e28-11fe-4cf1-9d4c-2beada24bdfc)


> [!WARNING]
> This script closes open positions only. It does not cancel pending orders.\
> Test the script on demo accounts first to see if it behaves as you expect.

## Quick Start

Follow these steps to get the script up and running:

1. **Download the Script**
   - Download the ZIP file from the [latest release](https://github.com/SheikAlgo/TradeKillSwitch/releases/latest) and extract it.

2. **Install Dependencies**
   - Make sure you have [Python](https://www.python.org/) installed on your system.
   - Install the required Python packages by running `pip install pandas requests` in your terminal or command prompt.

3. **Configure the accounts.json**
   - Open the `accounts.json` file and modify the settings according to your preferences and trading platform credentials.
   - Refer to the [Configuration](#configuration) section for detailed instructions.

4. **Run the Script**
   - Execute the script by opening the 'main.py' file, or by running `python main.py` in your terminal or command prompt.
   - The script will start running based on the configured settings.

## Installation & Requirements
[Initially tested on Python v3.11, pandas v2.2.2, requests v2.31.0]

If you don't have Python already, please install an appropriate version (preferably >= v3.11) for your operating system from: https://www.python.org/downloads/

If you do not have the "pandas" or "requests" packages already installed, you can use "pip" to install them from a command line interface, such as Command Prompt or PowerShell:
```
pip install pandas requests
```

## Downloads

ZIP files can be found on the [Releases page](https://github.com/SheikAlgo/TradeKillSwitch/releases).

## Configuration

Follow the guide below on how to edit the accounts.json file for your accounts.\
Once it is properly configured, you can run "main.py", and it will look something like the screenshot above.

The accounts.json file must be present in the main script directory.\
If unsure how the json format works, use a json editor to edit the json file.


### Editing the accounts.json file:

> [!IMPORTANT]
> All data must be in string/text format, including the account number. For example: the integer 287457 should be a string "287457" instead.

**`"id"`**: can be any string/text that helps you identify that account. It's not used to login.

**`"platform"`**: can be one of "dxtrade", "matchtrader", or "tradelocker".

**`"base_url"`**: is the base url for interacting with the server.
Examples:
```
"https://dxtrade.ftmo.com/dxsca-web/"
"https://demo.match-trade.com/"
"https://demo.tradelocker.com/backend-api/"
```

**`"account"`**: the account number, for example "2983429"

**`"password"`**: the account's password.

**`"past_delta"`**: how far back in time to look for past news events.\
Examples of valid "past_delta" values: "15 minutes", "1 hour", "360 seconds".
> [!NOTE]
> "past delta" is for informational purposes only. Positions impacted by past events are not closed if found.

**`"future_delta"`**: how far ahead in time to look for future news events.\
Examples of valid "future_delta" values: "3 hours", "45 minutes", "18000 seconds".\
It is recommended to pick a large enough time to allow timely closure of positions.\
At least 1 hour should be good enough.

**`"event_impact"`**: should be a list that contains at least one of these: "high", "medium", "low"\
Examples of valid "event_impact" values:\
`["high"]` if you want the script to consider events of high impact only.\
`["high", "medium"]` if you want both events of high and medium impacts.\

**`"country_symbols"`**: is a dictionary that associates events of such countries to those symbols.\
The supported countries are: `AUD CAD CHF CNY EUR GBP JPY NZD USD`\
Example 1:  `{"USD": ["ALL"]}` will close all symbols if there is any upcoming USD event.\
Example 2:  `{"USD": ["EURUSD", "GBPJPY"]}` will close EURUSD and GBPJPY only.\
Example 3:  `{"USD": ["ALL"], "EUR": ["ALL"]}` will close all symbols if USD or EUR events are found.


Below is a basic template for the accounts.json for a DXtrade account.\
Note: Match-Trader also requires **`"email"`**. Similarly, TradeLocker requires **`"email"`** and **`"server"`**.

```
{
 "accounts": [
  {
   "id": "any_id_is_fine_1",
   "platform": "dxtrade",
   "base_url": "https://dxtrade.ftmo.com/dxsca-web/",
   "account": "123456789",
   "password": "12345qwerty",
   "past_delta": "15 minutes",
   "future_delta": "3 hours",
   "event_impact": ["high"],
   "country_symbols": {"USD": ["ALL"]}
  }
}
```

> [!NOTE]
> You might encounter errors while running the script and obtain error codes in the terminal. Sometimes the error descriptions might be vague. Search what they mean online, verify that your data in accounts.json is correct, and if the errors still persist, open an issue here.

## References

The documentations of the trading APIs used in this project can be found here:
```
https://demo.dx.trade/developers/#/DXtrade-REST-API
https://tradelocker.com/api/#/
https://docs.match-trade.com/docs/match-trader-api-documentation/
```
## Privacy

This script is designed to run locally, and it does not transfer any user data to third-party servers or services, apart from the necessary interactions with the servers of the respective trading platforms (e.g., exchanges, brokers) that you choose to connect to.

Please note that when using this script to interact with trading platforms, certain data, such as your account information, trade orders, and transaction history, will be transmitted to and from the respective platform servers as per their standard operations. This script does not collect, store, or share any of this data with external parties beyond the trading platforms you actively connect to.


## Disclaimer

By using this code, you agree to indemnify and hold harmless the creator of this project from any and all claims, damages, losses, liabilities, costs, and expenses (including reasonable attorney fees) arising from or in connection with your use of this code.

The creator of this project shall not be responsible for any direct, indirect, incidental, special, consequential, or exemplary damages, including but not limited to, damages for loss of profits, goodwill, use, data, or other intangible losses resulting from the use or inability to use this code.

You acknowledge and agree that your use of this code is at your own risk and that you are responsible for any damages or losses that may occur as a result of such use.
