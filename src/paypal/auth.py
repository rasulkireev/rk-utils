"""Authentication Utils for Paypal API"""

import requests
from settings import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_URL


def get_access_token() -> str:
    """This function authenticate with Paypal using creds in .env

    Returns:
        str: Access Token that can be used across Paypal APIs
    """
    response = requests.post(
        url=PAYPAL_URL + "/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="grant_type=client_credentials",
        timeout=100,
    ).json()

    return response["access_token"]
