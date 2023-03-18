import os

import html2text
import httpx
from bs4 import BeautifulSoup

from src.scrapers.utils import remove_unwanted_elements


def parse_the_page(url: str) -> str:
    response = httpx.get(url)

    soup = BeautifulSoup(response.content, "html.parser")
    soup = remove_unwanted_elements(soup)

    # change the location of all the img files
    for tag in soup.findAll("img"):
        if tag.has_attr("src"):
            filename = os.path.basename(tag["src"])
            tag["src"] = f"shapeup-files/{filename}"

    # Add the 'Chapter #' to the header.
    try:
        intro_masthead = soup.find("p", {"class": "intro__masthead"})
        intro_title = soup.find("h1", {"class": "intro__title"})
        new_h1 = soup.new_tag("h1", attrs={"class": "intro__title"})
        new_h1.string = f"{intro_masthead.string} {intro_title.string}"
        intro_masthead.replace_with("")
        intro_title.replace_with(new_h1)
    except AttributeError:
        print("no subheader")

    try:
        pagination = soup.find("nav", {"class": "pagination"})
        link = pagination.find("a")["href"]
        pagination.extract()
    except TypeError:
        link = ""

    html = str(soup)

    return html2text.html2text(html), link


book_url = "https://basecamp.com/shapeup/0.1-foreword"

markdown, next_page_link = parse_the_page(book_url)
while next_page_link:
    next_page_link = f"https://basecamp.com{next_page_link}"
    print(f"processing page: {next_page_link}")
    new_markdown, next_page_link = parse_the_page(next_page_link)
    markdown += new_markdown

with open("ignore/shapeup/shapeup.md", "w", encoding="utf-8") as f:
    f.write(markdown)

# Then run "pandoc -o 'getting_real.epub' getting_real.md --metadata-file 'metadata.yaml' --toc --toc-depth=2"
