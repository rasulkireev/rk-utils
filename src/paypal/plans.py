"""These are utils for Paypal Plans API"""

import requests
import yaml
from auth import get_access_token
from settings import PAYPAL_URL, PAYPAL_YAML_DATA_DIR

PLANS_ENDPOINT = "/v1/billing/plans"


def list_plans(product_id: str) -> dict:
    """Returns a list of existing plans

    Args:
        product_id (str): Existing Product ID

    Returns:
        dict: Existing Plans
    """
    access_token = get_access_token()
    response = requests.get(
        url=PAYPAL_URL + PLANS_ENDPOINT,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
        params={"product_id": product_id},
    ).json()

    return response


def create_plan() -> dict:
    """Create a Plan for an existing product using the `plan.yml`.

    Returns:
        dict: Information about created plan.
    """
    with open(PAYPAL_YAML_DATA_DIR / "plan.yml", "r", encoding="UTF-8") as product_dict:
        access_token = get_access_token()
        data = yaml.load(product_dict, Loader=yaml.BaseLoader)
        response = requests.post(
            url=PAYPAL_URL + PLANS_ENDPOINT,
            json=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
        ).json()

    return response
