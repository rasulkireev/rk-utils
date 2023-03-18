"""Core module which is used to access all other Paypal Utils"""

from src.paypal.plans import create_plan, list_plans
from src.paypal.products import list_products

if __name__ == "__main__":
    new_plan = create_plan()
    print(f"New Plan: {new_plan}")

    products = list_products()["products"]
    for product in products:
        print(list_plans(product["id"]))
