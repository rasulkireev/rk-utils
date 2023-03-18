def remove_unwanted_elements(soup):
    # Remove un wanted elements
    for tag in soup.findAll(class_="warning"):
        tag.extract()
    for tag in soup.findAll("nav", {"class": "menu"}):
        tag.extract()
    for tag in soup.findAll("button", {"class": "intro__book-title"}):
        tag.extract()
    for tag in soup.findAll("p", {"class": "intro__next"}):
        tag.extract()
    for tag in soup.findAll("ul", {"class": "intro__sections"}):
        tag.extract()
    for tag in soup.findAll("footer"):
        tag.extract()

    return soup
