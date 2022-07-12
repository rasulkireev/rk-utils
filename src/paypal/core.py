"""This module has many neat functions I might need to interact with Paypal API"""

import os

import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

PAYPAL_URL = "https://api-m.sandbox.paypal.com"
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")


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
    ).json()

    return response["access_token"]


def list_products() -> dict:
    """Returns a list of existing products

    Returns:
        dict: Dicitonary of Products
    """
    access_token = get_access_token()
    response = requests.get(
        url=PAYPAL_URL + "/v1/catalogs/products",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
    ).json()

    return response


def create_product() -> dict:
    """Create product using the `product.yml` file in this dir.

    Returns:
        dict: Information about create product
    """
    with open("./src/paypal/product.yml", "r", encoding="UTF-8") as product_dict:
        access_token = get_access_token()
        data = yaml.load(product_dict, Loader=yaml.BaseLoader)
        response = requests.post(
            url=PAYPAL_URL + "/v1/catalogs/products",
            json=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
        ).json()

    return response


if __name__ == "__main__":
    products = list_products()
    # product = create_product()
    print(products)
