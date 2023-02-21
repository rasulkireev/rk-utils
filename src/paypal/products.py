"""These are utils for Paypal Products API"""

import requests
import yaml

from src.paypal.auth import get_access_token
from src.paypal.settings import PAYPAL_URL, PAYPAL_YAML_DATA_DIR

PRODUCTS_ENDPOINT = "/v1/catalogs/products"


def list_products() -> dict:
    """Returns a list of existing products

    Returns:
        dict: Dicitonary of Products
    """
    access_token = get_access_token()
    response = requests.get(
        url=PAYPAL_URL + PRODUCTS_ENDPOINT,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
        timeout=100,
    ).json()

    return response


def create_product() -> dict:
    """Create product using the `product.yml` file in this dir.

    Returns:
        dict: Information about create product
    """
    with open(PAYPAL_YAML_DATA_DIR / "product.yml", "r", encoding="UTF-8") as product_dict:
        access_token = get_access_token()
        data = yaml.load(product_dict, Loader=yaml.BaseLoader)
        response = requests.post(
            url=PAYPAL_URL + PRODUCTS_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
            timeout=100,
        ).json()

    return response
