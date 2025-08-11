# TODO: Create a tweet thread from the generated newsletter and send it to typefully
# TODO: Send the newsletter to buttondown
# TODO(MAYBE): add some interesting article links from ask hn digests. or a section on interesting hacker news disucssions
# TODO(MAYBE): add some cool repos from my github favorites
# Update sponsore block to be more like in bwd
# Make the wording better on the sponsors block
# add sent-in-newsletter tag to other links raindrops
# create a function that will create a subject line
# TODO: add books i've been reading that week (from bookwise email)

import os
import anthropic
import requests
from dotenv import load_dotenv
from src.obsidian.weekly_journal_summary import get_last_week_notes
from src.raindrop.main import add_tag_to_raindrop, get_last_7_raindrops_from_other, get_random_person_from_collection
from src.readwise.highlights import filter_highlights_by_date_range, get_highlights_last_7_days

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
client = anthropic.Client(api_key=api_key)


def create_personal_updates_block():
    journal_content = get_last_week_notes()

    prompt = f"""use these journal entries from my journal to create a list of bullet points.

    - keep them short and potentially relevant to my subscribers
    - only use non work related things

    Format your response as a complete newsletter section and make sure it is valid markdown.
    Start with `## Personal Updates`
    For bullet points use `-` and for sub-bullets use `-` again.

    Here are the journal entries to choose from:
    {journal_content}
    """

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error generating quote with Claude: {e}"


def create_quote_of_the_week_block():
    recent_highlights_by_updated_at = get_highlights_last_7_days()
    recent_highlights_by_highlighted_at = filter_highlights_by_date_range(recent_highlights_by_updated_at, days=7)

    recent_highlights_by_highlighted_at = [
        highlight for highlight in recent_highlights_by_highlighted_at
        if highlight.get("note") not in {".h1", ".h2", ".h3", ".h4"}
    ]

    # put all the highlights into a nicely formatted string, which will have the following things: highlight text, note, author name, book title, book author
    highlights_formatted = ""
    for i, highlight in enumerate(recent_highlights_by_highlighted_at):
        highlights_formatted += f"""
        Highlight {i+1}
        Text: {highlight.get("text")}
        Note: {highlight.get("note")}
        Author: {highlight.get("book_author")}
        Book Title: {highlight.get("book_title")}
        --------------------------
        """

    prompt = f"""From these recent reading highlights, choose the ONE that would work best as a "Quote of the week" for a personal newsletter.

    Select the highlight that is:
    - Most thought-provoking or inspiring
    - Broadly relatable to a general audience
    - Not too technical or niche

    Format your response as a complete newsletter section with:
    1. The quote itself (properly formatted) (with attribution to the author and the book title)
    2. One or two sentences expanding on the quote from a personal experience perspective (write as if you're the newsletter author sharing your own thoughts)
    3. Keep it simple and relatable

    Here are the highlights to choose from:
    {highlights_formatted}

    Return only the formatted newsletter section, starting with "## Quote of the week" and including any formatting you think would work well."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error generating quote with Claude: {e}"


def create_cool_person_block():
    person = get_random_person_from_collection()

    url = person.get("link")
    name = person.get("title")
    note = person.get("note")

    jina_url = f"https://r.jina.ai/{url}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {os.getenv('JINA_READER_API_KEY')}",
    }

    response = requests.get(jina_url, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json().get("data", {})

    title = data.get("title", "")
    description = data.get("description", "")
    content = data.get("content", "")

    prompt = f"""
    Below are data about a person.
    I would like you to create a newsletter section about this person.

    URL: {url}
    Name: {name}
    Note (how I found this person): {note}
    Page Title: {title}
    Page Description: {description}
    Page Content: {content}

    Response should:
    - be valid markdown
    - if there is a headshot in the context provided, add it
    - if there is a note about how i found the person, add it
    - summarize information found in the context i shared to let my subs know more about this person
    - add a link to their personal website as well as social links if any
    - needs to start with "## Cool person I encountered this week"
    - needs to be very consice info.
      - bold name of the person
      - one image (if available, formatted to be a circle, likes so: <img style="border-radius: 50%; width: 100px" src="link to image" alt="name">)
      - one paragraph about how i know him (if available)
      - one paragraph about his work (from the context provided)

    Example:
    ```
    ## 😄 Cool person I encountered this week

    **Brajeshwar Oinam**

    <img style="border-radius: 50%; width: 100px" src="link to image" alt="Brajeshwar Oinam">

    I found [Brajeshwar](link) through his "[Notes Site](link)", more specifically his list of [Awesome Articles](link).

    He has a very interesting set of products, and a pretty interesting story, which you can checkout [here](link), if you are curious.
    ```
    """

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )
        content = response.content[0].text.strip()
    except Exception as e:
        return f"Error generating cool person block with Claude: {e}"

    add_tag_to_raindrop(person["_id"], "featured in newsletter")

    return content


def create_other_cool_links_block():
    raindrops = get_last_7_raindrops_from_other()

    block = "## Other cool links\n"
    for raindrop in raindrops:
        url = raindrop.get("link")
        title = raindrop.get("title")
        excerpt = raindrop.get("excerpt")

        block += f"- [{title}]({url}): {excerpt}\n"

    return block


def create_support_block():
    return """##Support

You can support this project by using one of the affiliate links below. These are always going to be projects I use and love! No "Bluehost" crap here!

- [Buttondown](https://buttondown.email/refer/rasulkireev) - Email newsletter tool I use to send you this newsletter.
- [Readwise](https://readwise.io/i/rasul) - Best reading software company out there. I you want to up your e-reading game, this is definitely for you! It also so happens that I work for Readwise. Best company out there!
- [Hetzner](https://hetzner.cloud/?ref=Ju1ttKSG0Fn7) - IMHO the best place to buy a VPS or a server for your projects. I'll be doing a tutorial on how to use this in the future.
"""


def create_sponsors_block():
    return """## 🤑 Sponsors

This newsletter is sponsored by [TJ Alerts](https://gettjalerts.com). Well, sponsor is a strong word. It is just another project of mine that I wanted to share with you 🙈. Fully free!

**If you are looking for a job, I think this will be extremely useful to you.**

I search the whole web for current job openings and categorize them on many aspects (location, tech used, salary, etc.). You can search those jobs and subscribe to receive recurring updates on latest jobs that match your filters.

> If you want to become a real sponsor, just reply to this email 😄
"""


if __name__ == "__main__":
    newsletter_content = """Hey, Happy Tuesday!

> ***Why are you getting this***: You signed up to receive this newsletter on [my personal website](https://rasulkireev.com). I promised to send you the most interesting sites and resources I have encountered during the week. *If you don't want to receive this newsletter, feel free to* [*unsubscribe*]({{ unsubscribe_url }}) *anytime.*"""

    personal_updates_block = create_personal_updates_block()
    newsletter_content += personal_updates_block

    newsletter_content += "\n\n"

    quote_block = create_quote_of_the_week_block()
    newsletter_content += quote_block

    newsletter_content += "\n\n"

    cool_person_block = create_cool_person_block()
    newsletter_content += cool_person_block

    # newsletter_content += "\n\n"

    # tweet_block = create_tweet_of_the_week_block()
    # newsletter_content += tweet_block

    newsletter_content += "\n\n"

    other_cool_links_block = create_other_cool_links_block()
    newsletter_content += other_cool_links_block

    newsletter_content += "\n\n"

    support_block = create_support_block()
    newsletter_content += support_block

    newsletter_content += "\n\n"

    sponsors_block = create_sponsors_block()
    newsletter_content += sponsors_block

    print(newsletter_content)
