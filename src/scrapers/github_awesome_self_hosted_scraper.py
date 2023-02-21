# I just want to scrape all the projects in the
# awesome-selfhosted/awesome-selfhosted repo and
# see how many stars each one has. I will save some
# relevant data to my personal typesense instance

import re
from datetime import date, datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from typesense.exceptions import ObjectAlreadyExists, ObjectNotFound

from src.auth import mongo_client, typesense_client
from src.config import GITHUB_PAT

COLLECTION_NAME = "awesome_selfhosted_repos"


def create_or_update_typesense_schema(collection_name: str) -> None:
    schema = {"name": collection_name, "fields": [{"name": ".*", "type": "auto"}]}

    try:
        typesense_client.collections.create(schema)
    except ObjectAlreadyExists:
        print("Schema already exists")
        # code below would update the fields if you wanted to.
        # schema_fields = {"fields": schema["fields"]}
        # typesense_client.collections[collection_name].update(schema_fields)


def get_all_github_repo_links_mentioned_on_web_page(url: str) -> list:
    response = requests.get(url, timeout=100)
    soup = BeautifulSoup(response.content, "html.parser")

    repo_pattern = re.compile(r"^https:\/\/github.com\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+$")
    github_repos = []

    for link in soup.find_all("a"):
        href = link.get("href")
        if href and all(
            [
                "github.com" in href,
                repo_pattern.match(href),
                "awesome" not in href,
                "topics" not in href,
            ]
        ):
            github_repos.append(href)

    return github_repos


def get_data_from_repo(repo: str) -> dict:
    path = urlparse(repo).path
    repo_path = path.strip("/")

    response = requests.get(
        f"https://api.github.com/repos/{repo_path}",
        headers={
            "User-Agent": "rasulkireev",
        },
        auth=("rasulkireev", GITHUB_PAT),
        timeout=100,
    ).json()

    try:
        data = {
            "id": str(response["id"]),
            "last_updated": str(datetime.now()),
            "name": response["name"],
            "description": response["description"],
            "repo_url": response["html_url"],
            "stars": response["stargazers_count"],
            "language": response["language"],
            "topics": response["topics"],
        }

        return data

    except KeyError as e:
        print(f"Repo: {repo_path}")
        print(f"Response: {response}")

        return e


def create_or_update_typesense_document(collection: str, document: dict) -> None:
    try:
        typesense_client.collections[collection].documents.create(document)
        print(f"Created Typesense Document: {document['name']}")
    except ObjectAlreadyExists:
        typesense_client.collections[collection].documents[document["id"]].update(document)
        print(f"Updated Typesense Document: {document['name']}")


def document_was_updated_today(collection: str, name: str) -> bool:
    try:
        search_parameters = {
            "q": name,
            "query_by": "name",
        }

        results = typesense_client.collections[collection].documents.search(search_parameters)
        hits = results["hits"]

        for hit in hits:
            if hit["document"]["name"] == name:
                last_updated = hit["document"]["last_updated"]
                date_obj = datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S.%f").date()
                today = date.today()

                if date_obj == today:
                    return True

        return False

    except ObjectNotFound:
        return False


# create db connections and create tables
mongo_db = mongo_client[COLLECTION_NAME]
mongo_collection = mongo_db[COLLECTION_NAME]
create_or_update_typesense_schema(COLLECTION_NAME)

list_of_repo_urls = get_all_github_repo_links_mentioned_on_web_page(
    "https://github.com/awesome-selfhosted/awesome-selfhosted"
)
set_of_repo_urls = set(list_of_repo_urls)
num_of_repos = len(set_of_repo_urls)

for index, repo_url in enumerate(set_of_repo_urls):
    repo_name = urlparse(repo_url).path.strip("/").split("/")[-1]

    # if document_was_updated_today(COLLECTION_NAME, repo_name):
    #   print(f"{repo_name} repo was already updated today")
    # else:

    repo_data_dict = get_data_from_repo(repo_url)
    create_or_update_typesense_document(COLLECTION_NAME, repo_data_dict)

    mongo_collection.insert_one(repo_data_dict)
    print(f"Inserted Mongo document: {repo_data_dict['name']}")

    print(f"Repo {index+1}/{num_of_repos} is done: {repo_data_dict['name']}")
