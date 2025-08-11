import os
from dotenv import load_dotenv
import openai
from pathlib import Path

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_highlights_content(filename: str) -> str:
    # Ensure filename has .md extension
    if not filename.endswith('.md'):
        filename += '.md'

    # Build path to the highlights file relative to the current working directory
    highlights_path = Path.cwd() / "ignore" / "highlights" / filename

    try:
        with open(highlights_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        raise FileNotFoundError(f"Highlights file not found: {highlights_path}")
    except Exception as e:
        raise Exception(f"Error reading highlights file: {e}")

def generate_frontmatter(highligths: str) -> str:
    message=f"""
      Below is an example of Markdown front matter for another book that I posted on my website.
      Can you please update it with the details for the book (with highlights) I'll share at the end?
      ```
      ---
      title: Getting Real
      subtitle: The Smarter, Faster, Easier Way to Build a Successful Web Application
      author: 37 Signals
      rating: 9
      slug: getting-real
      description: Building software doesn’t need a large team, huge budget, or a perfect plan up front. Products should do less and work smarter by focusing on solving real problems and evolving with user feedback. The key is to create sustainable software by making smart, incremental improvements that truly meet users’ needs.
      cover: "./images/getting-real.png"
      dateRead: 2024-07-11
      dateCreated: 2025-02-22
      dateUpdated: 2025-02-22
      category: "Business"
      type: book
      hasSummaries: false
      notAffiliateLink: https://basecamp.com/gettingreal
      affiliateLink: https://amzn.to/3XazhEk
      hnLink: https://news.ycombinator.com/item?id=43148814
      twitterLink: https://x.com/rasulkireev/status/1893994417402294418
      tags:
        - Software Development
        - Entrepreneurship
        - Product Management
        - Startup
        - Web Applications
        - Minimalism
        - Business Strategy
        - User Experience
        - Agile
        - Project Management
        - Marketing
        - Customer Support
        - Software Design
        - Lean Startup
        - Bootstrapping
      ---
      ```

      Book with highlights:
      {highligths}

      IMPORTANT:
      - Response should be in Markdown format.
      - Only return the frontmatter, no other text.
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content

def generate_summary_learnings(highligths: str) -> str:
    message=f"""
      I'm writing a book review. Below are the highlights and notes I took.

      {highligths}

      Can you help me summarize this books and write a condedsed learnings from this book. Structure should be:
      ```
      ## Summary
      {{summary}}

      ## Learnings
      {{learnings}}
      ```

      - summary should be more condesned (2 paragraphs at most)
      - learnings shuold also be condensed (ideally bullet points should be one level deep, unless really abstract)
      - Response should be in Markdown format.
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content

def generate_key_sentences(highligths: str) -> str:
    message=f"""
        You are an expert reader trained in analytical reading.
        Your task is to identify the most important sentences in the text and discover their propositions.

        Find 3-5 of the most important sentences in the text. Focus on sentences that:
        - Contain the author's key arguments or conclusions
        - Introduce important concepts or principles
        - Make significant claims or assertions
        - Connect major ideas together

        For each identified sentence:
        1. Quote the sentence
        2. Explain in 2-3 lines why this sentence is crucial to understanding the author's message and what proposition it contains

        Here is the text to analyze:
        ```
        {highligths}
        ```

        Please list the key sentences and their significance, being concise but precise in your explanations.
        Response should be in Markdown format.

        It should be in the following format:
        ```
        1. {{key_sentence}}
          - **Why it’s crucial**: {{explanation}}
          - **Proposition**: {{proposition}}
        ```
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content


def generate_unity_of_the_book(highligths: str) -> str:
    message=f"""
        Your task is to analyze the following text and express its fundamental unity - the single main point or theme that the entire work revolves around - in one sentence, or at most a short paragraph.

        Here is the text to analyze:
        ```
        {highligths}
        ```

        INSTRUCTIONS:
        1. Consider what single, central point the author is trying to communicate
        2. Identify how all major arguments or sections of the book support this central point
        3. Express this unity in ONE sentence, or if absolutely necessary, a very short paragraph
        4. Focus on WHAT the book is about as a whole, not its method or structure
        5. Avoid merely describing what the book talks about; instead, capture its essential message or argument

        IMPORTANT:
        - Be concise but complete
        - Capture the essence, not just the topic
        - Express the unity in a way that shows how all parts of the book relate to this central point
        - Avoid listing multiple main points; find the ONE unifying idea
        - Response should be in Markdown format.
        - Only return the unity statement, no other text.
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content


def generate_author_problems(highligths: str) -> str:
    message=f"""
        Your task is to analyze the text and identify the key problems or questions that the author is trying to address.
        Consider that:
        - Authors start with questions, even if they don't explicitly state them
        - The book contains the answers to these questions
        - The problems should be formulated as precisely as possible
        - Questions should be ordered by importance (primary vs secondary)

        Here is the text to analyze:
        ```
        {highligths}
        ```

        Please identify and list:

        1. The main problem or question the author is trying to solve
        2. The subordinate problems or questions that support the main one
        3. The order of these problems (which must be solved first to answer others)

        Format your response as:
        #### Main Problem
        [State the primary question/problem in one clear sentence]

        #### Supporting Problems
        1. [First supporting problem]
        2. [Second supporting problem]
        3. [Third supporting problem]
        (etc.)

        #### Problem Hierarchy
        [Brief explanation of how these problems relate to each other and why they are ordered this way]

        IMPORTANT:
        - Focus on identifying actual problems the author is trying to solve, not just topics they discuss.
        - The problems should be specific enough to guide understanding but broad enough to encompass the book's major themes.
        - Response should be in Markdown format.
        - Only return the problems, no other text.
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content


def generate_book_structure(highligths: str) -> str:
    message=f"""
        You are an expert at analyzing the structure and organization of books.
        Help me understand how the major parts of this book work together to form a coherent whole.

        Please analyze the following text and:

        1. Identify the major parts/sections and their main points
        2. Explain how these parts relate to and build upon each other
        3. Show how they connect to and support the book's central theme/argument
        4. Create a visual outline showing the hierarchical relationship between parts

        Consider:
        - How earlier parts lay groundwork for later ones
        - Key transitions and connections between sections
        - How each part contributes to the book's unity
        - The logical flow and progression of ideas

        Here is the text to analyze:
        ```
        {highligths}
        ```

        Please provide:
        1. A brief overview of the major parts/sections
        2. An explanation of how they work together
        3. A hierarchical outline showing their relationships
        4. Commentary on how this structure serves the book's main purpose

        IMPORTANT:
        - Focus on understanding and explaining the book's structural unity rather than just summarizing content.
        - Response should be in Markdown format.
        - Only return the structure, no other text.
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content

def generate_prompt_ideas(highligths: str) -> str:
    message=f"""
        Based on book highlights provided below can you help me come up with prompt ideas that
        would be useful for readers of this book to use for automations with ai agents.

        Here is the text to analyze:
        ```
        {highligths}
        ```

        IMPORTANT:
        - Response should be in Markdown format.
        - Only return the prompt ideas, no other text.
        - Come up with 10 good ideas.
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    filename = input("Enter the filename: ")

    highlights = get_highlights_content(filename)

    article = ""

    frontmatter = generate_frontmatter(highlights)
    article += frontmatter
    article += "\n"

    summary_and_learnings = generate_summary_learnings(highlights)
    article += summary_and_learnings
    article += "\n"

    article += "## [How to Read a Book](/how-to-read-a-book) Analysis"
    article += "\n"

    article += "### Key Sentences"
    key_sentences = generate_key_sentences(highlights)
    article += key_sentences
    article += "\n"

    article += "### Unity of the Book"
    unity_of_the_book = generate_unity_of_the_book(highlights)
    article += unity_of_the_book
    article += "\n"

    article += "### Author's Problems"
    author_problems = generate_author_problems(highlights)
    article += author_problems
    article += "\n"

    article += "### Book's Structure"
    book_structure = generate_book_structure(highlights)
    article += book_structure
    article += "\n"

    article += "## Prompt Ideas"
    prompt_ideas = generate_prompt_ideas(highlights)
    article += prompt_ideas

    print(article)
