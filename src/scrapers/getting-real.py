import html2text
import httpx
from bs4 import BeautifulSoup

from src.scrapers.utils import remove_unwanted_elements


def parse_the_page(url: str) -> str:
    response = httpx.get(url)

    soup = BeautifulSoup(response.content, "html.parser")
    soup = remove_unwanted_elements(soup)

    # Add the Chapter 1 to the header.
    intro_masthead = soup.find("p", {"class": "intro__masthead"})
    intro_title = soup.find("h1", {"class": "intro__title"})
    new_h1 = soup.new_tag("h1", attrs={"class": "intro__title"})
    new_h1.string = f"{intro_masthead.string} {intro_title.string}"
    intro_masthead.replace_with("")
    intro_title.replace_with(new_h1)

    try:
        pagination = soup.find("nav", {"class": "pagination"})
        page_link = pagination.find("a")["href"]
        pagination.extract()
    except TypeError:
        page_link = ""

    html = str(soup)

    return html2text.html2text(html), page_link


book_url = "https://basecamp.com/gettingreal/01.1-what-is-getting-real"

markdown, next_page_link = parse_the_page(book_url)
while next_page_link:
    next_page_link = f"https://basecamp.com{next_page_link}"
    print(f"processing page: {next_page_link}")
    new_markdown, next_page_link = parse_the_page(next_page_link)
    markdown += new_markdown

with open("ignore/getting_real/getting_real.md", "w", encoding="utf-8") as f:
    f.write(markdown)

# Then run "pandoc -o 'getting_real.epub' getting_real.md --metadata-file 'metadata.yaml' --toc --toc-depth=2"
