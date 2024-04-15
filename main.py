"""
Please read the latest README file for TradeKillSwitch on GitHub:
https://github.com/SheikAlgo/TradeKillSwitch/blob/master/README.md

It contains essential information and instructions for how to use this script.
"""

try:
    import requests
    import pandas as pd
    import datetime as dt
    import time
    import json
    import sys
except Exception as e:
    print("Error encountered while importing modules: ", e)
    print("Try running 'pip install' for that particular module.")
    input("Press Enter to exit...")
    quit()


def get_request(url, headers=None, timeout=None):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code in [200, 201]:
            data = response.json()
            return data
        else:
            print(f"Request failed with status code: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def post_request(url, payload, headers=None):
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            resp = response.json()
            return resp
        else:
            print(f"Request failed with status code: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def delete_request(url, payload=None, headers=None):
    try:
        response = requests.delete(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            resp = response.json()
            return resp
        else:
            print(f"Request failed with status code: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def parse_json():
    # read accounts.json
    try:
        print("Loading 'accounts.json'...")
        with open('accounts.json') as accounts:
            parsed_json = json.load(accounts)
            if "accounts" not in parsed_json:
                raise Exception("Missing 'accounts' key in json")
            for account in parsed_json["accounts"]:
                if "id" not in account:
                    raise Exception("Missing 'id' key in json")
                if not account["base_url"].endswith("/"):
                    raise Exception(f"'base_url' of id {account['id']} must end with '/'")
                missing = {"platform", "base_url", "account", "password", "past_delta", "future_delta",
                           "event_impact", "country_symbols"} - set(account.keys())
                if len(missing) > 0:
                    raise Exception(f"Missing keys in id: {account['id']}: {missing}")
                if account["platform"] in ["matchtrader", "tradelocker"]:
                    if "email" not in account:
                        raise Exception(f"Missing 'email' key in id: {account['id']}")
                if account["platform"] == "tradelocker":
                    if "server" not in account:
                        raise Exception(f"Missing 'server' key in id: {account['id']}")
                if not isinstance(account["event_impact"], list):
                    raise Exception(f"'event_impact' of id {account['id']} should be a list '[]'")
                if len(account["event_impact"]) == 0:
                    raise Exception(f"'event_impact' list of id {account['id']} is empty")
                for imp in account["event_impact"]:
                    if str(imp).lower() not in ["high", "medium", "low"]:
                        raise Exception(f"'event_impact' of id {account['id']} "
                                        f"should be one of 'high', 'medium', or 'low'")

                print(f"Details for id {account['id']}:")
                print("     Selected past time delta: ", pd.Timedelta(account["past_delta"]))
                print("     Selected future time delta: ", pd.Timedelta(account["future_delta"]))
                print("     Selected event impact: ", account["event_impact"])
                print("     Selected countries & symbols: ", account["country_symbols"])

            print("\naccounts.json loaded successfully \n")
            return parsed_json

    except Exception as e:
        print("\nError in loading accounts.json: ", e)
        input("Press Enter to exit.")
        sys.exit()


def ff_news():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = get_request(url, timeout=30)
        if response is not None:
            df: pd.DataFrame = pd.json_normalize(response)
            df['date'] = pd.to_datetime(df['date'])
            df["impact"] = df.impact.str.lower()
            df['date'] = df['date'].dt.tz_convert(None)
            df['date'] = df['date'].dt.tz_localize('UTC')
            df = df[["country", "impact", "date"]]
            return df
        return None

    except Exception as er:
        print(f"Couldn't fetch FF calendar events! Error info: {er}")
        return None


def filter_news(news_df, past_delta="15 minutes", future_delta="24 hours", impact=("high",), ):
    now = pd.Timestamp.now("UTC")
    df = news_df[
        (news_df.date >= now - pd.Timedelta(past_delta)) &
        (news_df.date <= now + pd.Timedelta(future_delta)) &
        (news_df.impact.isin(impact))]
    df = df[["country", "date", "impact"]]

    past_news_df = df[df["date"] < now]
    future_news_df = df[df["date"] >= now]

    return past_news_df, future_news_df


def find_symbols(news_df, country_symbols: dict):
    found_countries = set(news_df.country.unique())
    common_countries = found_countries.intersection(set(country_symbols.keys()))
    impacted_symbols = [country_symbols[country] for country in common_countries]
    impacted_symbols = set().union(*impacted_symbols)
    return impacted_symbols


class MatchTrader:
    def __init__(self, base_url, email, account_id, password):
        self.base_url = base_url
        self.email = email
        self.account_id = account_id
        self.password = password
        self.auth_header = {}
        self.uuid = ""

    def login(self):
        login_url = self.base_url + "mtr-backend/login"
        payload = {
            "email": self.email,
            "password": self.password,
            "brokerId": "0"
        }

        response = post_request(login_url, payload)

        if response is not None:
            print(f"MatchTrader login successful: {self.email}, {self.base_url}")
            token = trading_token = ""
            accounts = response["tradingAccounts"]
            for account in accounts:
                if account["tradingAccountId"] == self.account_id:
                    self.uuid = account["offer"]["system"]["uuid"]
                    token = response["token"]
                    trading_token = account["tradingApiToken"]

            self.auth_header = {
                "Content-Type": "application/json",
                "Authorization": f"{token}",
                "Auth-Trading-Api": f"{trading_token}",
            }
        else:
            print(f"MatchTrader login failed: {self.email}, {self.base_url}")

    def get_open_positions(self):
        open_positions_url = self.base_url + f"mtr-api/{self.uuid}/open-positions"
        return get_request(open_positions_url, self.auth_header)

    def close_position(self, order):
        close_url = self.base_url + f"mtr-api/{self.uuid}/position/close"

        print(f"Closing position: {order['positionId']}, volume: {order['volume']},"
              f" instrument: {order['instrument']}")

        resp = post_request(close_url, order, self.auth_header)
        if resp["status"] == "OK" and resp["errorMessage"] is None:
            print(f"Position {order['positionId']} closed succesfuly")
        else:
            print(f"Error encountered in closing position {order['positionId']}")

    def close_all_positions(self, symbols_list=()):
        resp = self.get_open_positions()
        if resp is not None and len(resp["positions"]) > 0:
            close_all = True if "ALL" in symbols_list or len(symbols_list) == 0 else False
            for position in resp["positions"]:
                if not close_all and position["symbol"] not in symbols_list:
                    continue

                order = {
                    "orderSide": position['side'],
                    "positionId": position['id'],
                    "volume": position['volume'],
                    "instrument": position['symbol'],
                    "isMobile": False
                }

                self.close_position(order)


class DXtrade:
    def __init__(self, base_url, account, password, domain="default"):
        self.base_url = base_url
        self.account = account
        self.password = password
        self.domain = domain
        self.send_order_url = base_url + f"accounts/default:{account}/orders"
        self.get_positions_url = base_url + f"accounts/default:{account}/positions"
        self.auth_header = {}

    def login(self):
        login_url = self.base_url + "login"
        payload = {"username": self.account, "domain": self.domain, "password": self.password}

        response = post_request(login_url, payload)
        if response is not None:
            print(f"DXtrade login successful: {self.account}, {self.base_url}")
            self.auth_header = {
                "Content-Type": "application/json",
                "Authorization": f"DXAPI {response['sessionToken']}"
            }
        else:
            print(f"DXtrade login failed: {self.account}, {self.base_url}")

    def send_order(self, order):
        return post_request(self.send_order_url, order, self.auth_header)

    def get_open_positions(self):
        return get_request(self.get_positions_url, self.auth_header)

    def close_position(self, order):
        print(f"Closing position: {order['positionCode']}, quantity: {order['quantity']},"
              f" instrument: {order['instrument']}")

        resp = self.send_order(order)
        if resp is not None and "orderId" in resp:
            print(f"Position {order['positionCode']} closed succesfuly")
        else:
            print(f"Error encountered in closing position {order['positionCode']}")

    def close_all_positions(self, symbols_list=()):
        resp = self.get_open_positions()
        if resp is not None and len(resp["positions"]) > 0:
            close_all = True if "ALL" in symbols_list or len(symbols_list) == 0 else False
            for position in resp["positions"]:
                if not close_all and position["symbol"] not in symbols_list:
                    continue

                order = {
                    "account": f"default:{self.account}",
                    "orderCode": position["positionCode"],  # unique number
                    "type": "MARKET",
                    "instrument": position["symbol"],
                    "quantity": position["quantity"],
                    "positionCode": position["positionCode"],
                    "positionEffect": "CLOSE",
                    "side": "BUY" if position["side"] == "SELL" else "SELL",
                    "tif": "GTC",
                }

                self.close_position(order)


class TradeLocker:
    def __init__(self, base_url, email, account_id, password, server):
        self.base_url = base_url
        self.email = email
        self.account_id = account_id
        self.password = password
        self.server = server
        self.auth_header = {}
        self.accNum = ""
        self.instruments_id_dict = {}

    def login(self):
        login_url = self.base_url + "auth/jwt/token"
        payload = {
            "email": self.email,
            "password": self.password,
            "server": self.server,
        }

        response = post_request(login_url, payload)

        if response is not None:
            print(f"TradeLocker login successful: {self.email}, {self.base_url}, {self.server}")
            access_token = response['accessToken']
            self.auth_header = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }

            all_accounts_url = self.base_url + "auth/jwt/all-accounts"
            resp = get_request(all_accounts_url, self.auth_header)

            if resp is not None and "accounts" in resp:
                for account in resp["accounts"]:
                    if account['id'] == self.account_id:
                        self.accNum = account['accNum']
                        self.auth_header["accNum"] = account['accNum']
                if self.accNum == "":
                    print(f"Account ID {self.account_id} not found.")

            if self.instruments_id_dict == {}:
                self.map_instruments_id()

        else:
            print(f"TradeLocker login failed: {self.email}, {self.base_url}, {self.server}")

    def map_instruments_id(self):
        instruments_url = self.base_url + f"trade/accounts/{self.account_id}/instruments"
        res = get_request(instruments_url, self.auth_header)
        if res is not None:
            instruments = res['d']['instruments']
            for ins in instruments:
                self.instruments_id_dict[ins['name']] = ins['tradableInstrumentId']

    def get_open_positions(self):
        positions_url = self.base_url + f"trade/accounts/{self.account_id}/positions"
        return get_request(positions_url, self.auth_header)

    def close_all_positions(self, symbols_list=()):
        close_all_positions_url = self.base_url + f"trade/accounts/{self.account_id}/positions"
        if len(symbols_list) == 0:
            res = delete_request(close_all_positions_url, headers=self.auth_header)
        else:
            for symbol in symbols_list:
                instrument_id = self.instruments_id_dict[symbol]
                close_url = close_all_positions_url + f"?tradableInstrumentId={instrument_id}"
                res = delete_request(close_url, headers=self.auth_header)
                print(res)


if __name__ == '__main__':

    # parse accounts.json
    accounts_dict = parse_json()

    # create instances of each account for each trading platform
    instances_list = []
    if accounts_dict != {}:
        for account in accounts_dict["accounts"]:
            instance = None
            if account["platform"] == "matchtrader":
                instance = MatchTrader(account["base_url"], account["email"],
                                       account["account"], account["password"])
            elif account["platform"] == "dxtrade":
                instance = DXtrade(account["base_url"], account["account"], account["password"])
            elif account["platform"] == "tradelocker":
                instance = TradeLocker(account["base_url"], account["email"], account["account"],
                                       account["password"], account["server"])

            if instance is not None:
                instance.id = account["id"]
                instance.country_symbols = account["country_symbols"]
                instance.past_delta = account["past_delta"]
                instance.future_delta = account["future_delta"]
                instance.event_impact = account["event_impact"]
                instances_list.append(instance)

    # test logins to validate credentials
    try:
        if instances_list:
            print("Testing logins...")
            for instance in instances_list:
                print(f"\nTesting id: {instance.id}")
                instance.login()
        else:
            input("No accounts found...")
            sys.exit()
    except Exception as e:
        print("Error encountered while testing logins: ", e)

    print("\nGetting news events from ForexFactory...")
    unfiltered_news_df = ff_news()
    if unfiltered_news_df is None:
        input("\nNo news data found. Is your internet connection or ForexFactory working?")
        sys.exit()

    delay = 50

    while True:
        utc_now = dt.datetime.now(tz=dt.timezone.utc)
        if utc_now.minute == 0:  # update news every hour
            print("Updating news...")
            temp_df = ff_news()
            unfiltered_news_df = temp_df if temp_df is not None else unfiltered_news_df

        print("\nIterating through instances...")
        for i, instance in enumerate(instances_list):
            print("\nChecking instance id:", instance.id)
            past_news_df, future_news_df = filter_news(unfiltered_news_df, instance.past_delta,
                                                       instance.future_delta, instance.event_impact,
                                                       )

            # find impacted symbols
            past_impacted_symbols = find_symbols(past_news_df, instance.country_symbols)
            future_impacted_symbols = find_symbols(future_news_df, instance.country_symbols)

            if len(past_impacted_symbols) > 0:
                print(f"[Past] Impacted symbols from the past {instance.past_delta}:",
                      past_impacted_symbols)
            else:
                print(f"[Past] No symbols impacted from the past {instance.past_delta}")

            if len(future_impacted_symbols) > 0:
                try:
                    print(f"[Future] Impacted symbols within the next {instance.future_delta}: ",
                          future_impacted_symbols)
                    instances_list[i].login()
                    instances_list[i].close_all_positions(future_impacted_symbols)
                except Exception as e:
                    print(f"Error encountered in instance id {instance.id}: {e}")
            else:
                print(f"[Future] No symbols impacted within the next {instance.future_delta}")

        print(f"\nNext run at: {dt.datetime.now() + dt.timedelta(seconds=delay)} \n")
        print("############################################")

        time.sleep(delay)
