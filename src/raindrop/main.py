import requests
import os
from dotenv import load_dotenv

load_dotenv()

RAINDROP_ACCESS_TOKEN = os.getenv("RAINDROP_ACCESS_TOKEN")
BASE_URL = "https://api.raindrop.io/rest/v1"

def make_request(
    path: str,
    method: str = "GET",
    data: dict = None,
    params: dict = None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {RAINDROP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    response = requests.request(method, f"{BASE_URL}/{path}", headers=headers, json=data, params=params)
    return response.json()


def get_collections() -> list[dict]:
    return make_request("collections")


def get_collection_id_by_name(name: str) -> int:
    collections = get_collections()
    for collection in collections["items"]:
        if collection["title"] == name:
            return collection["_id"]
    return None


def get_collection_raindrops(collection_id: int) -> dict:
    return make_request(f"raindrops/{collection_id}")


def add_tag_to_raindrop(raindrop_id: int, tag: str):
    raindrop = make_request(f"raindrop/{raindrop_id}")
    tags = raindrop['item']["tags"] + [tag]
    print(f"Adding tag {tag} to raindrop {raindrop_id}")
    return make_request(f"raindrop/{raindrop_id}", "PUT", data={"tags": tags})


def get_random_person_from_collection() -> dict:
    collection_id = get_collection_id_by_name("People")
    raindrops = get_collection_raindrops(collection_id)

    for raindrop in raindrops["items"]:
        if "featured in newsletter" in raindrop["tags"]:
            continue

        return raindrop

    return None


def get_last_7_raindrops_from_other() -> list[dict]:
    """Get the last 7 raindrops from the 'Other' collection."""
    collection_id = get_collection_id_by_name("Other")
    if collection_id is None:
        return []

    raindrops = get_collection_raindrops(collection_id)
    return raindrops["items"][:7]
