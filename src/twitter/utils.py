import os
from dotenv import load_dotenv
import requests
from google import genai

load_dotenv()


def send_to_typefully(content: str, threadify: bool = True) -> dict:
    cleaned_content = content.replace("\n---\n", "\n\n\n\n")

    url = "https://api.typefully.com/v1/drafts/"
    headers = {
        "X-API-KEY": f"Bearer {os.getenv('TYPEFULLY_API_KEY')}",
        "Content-Type": "application/json",
    }
    payload = {"content": cleaned_content, "threadify": threadify}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()



def generate_tweet_thread_from_newsletter(newsletter_content: str) -> str:
    """
    Generate a tweet thread from newsletter content using Gemini.

    Args:
        newsletter_content (str): The newsletter content to convert to a tweet thread

    Returns:
        str: Generated tweet thread content
    """
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    client = genai.Client(api_key=api_key)

    prompt = f"""Please convert the following newsletter content into a Twitter thread.

Requirements for the tweet thread:
- Each tweet should be under 280 characters
- Use ultra chill tone. Starting sentences from non capital letters, for example.
- Do not add emojis.
- The goal of this thread is to hook the reader into subscribing to my newsletter.
  So don't add full details but make interesting hooks into the content.
- Start with a super hook that captures attention
- Break down the content into logical, digestible pieces
- don't use thread numbering (1/n, 2/n, etc.), just use the content as is
- Maintain the key insights and value from the original content
- Make it feel personal and authentic
- End with a call-to-action or engaging question

Format the output with each tweet on a separate line, separated by "---"

Here is an example of how I converted one newsletter issue into a tweet thread:
```
Hey, Happy Tuesday!

> ***Why are you getting this***: You signed up to receive this newsletter on [my personal website](https://rasulkireev.com). I promised to send you the most interesting sites and resources I have encountered during the week. *If you don't want to receive this newsletter, feel free to* [*unsubscribe*]({{ unsubscribe_url }}) *anytime.*

## Personal Updates

- Made big updates to [Marketing Agents](https://marketingagents.net/). Automatic blog post submission is finally done and so is usage and tracking of relevant keywords. Next up is marketing. The absolute base feature set is done and I need to see if I can find some customers. This has always been a weakness of mine, so kind of scared to get started.

- My son is an absolute joy to be around. He speaks very well now, which makes it so much more fun to interact with. Trying to enjoy this while it lasts, even though I get much less time for my side projects now.

- Finally pulled the plug on one of my addictive habits, this time for good! Feel free to keep me honest here and ask how i'm doing in the future. Withdrawal symptoms were bad. I was soooooo tired all the time, it was crazy.

- Improved [django-saas-starter](https://github.com/rasulkireev/django-saas-starter) with the latest updates in my projects.
  - IP tracking for email newsletter on buttondown
  - Improved API authentication via django-ninja
  - Sentry tracking for django-q

- Was doing some fun experiments with terminal-based data visualization using ASCII. Nothing conclusive yet.

## Quote of the week

> "A complex system that works always evolves from a simple system that works. Beginning from scratch with a complex system is a really bad idea."
>
> *— seangoedecke.com, Everything I Know About Good System Design*

I've been really enjoying content that Sean Goedecke posts. He is an inspiration when it comes to blogging and writing! Definitely want to be like him when I grow up.

This point specifically stood out to me. Cause in life, when you see something complex that works great, that is most likely because it started simple and stable. Then grew more complex very slowly, keeping that stability component.

## Cool person I encountered this week

**Geoffrey Huntley**

<img style="border-radius: 50%; width: 100px" src="https://ghuntley.com/content/images/size/w150/2025/08/A-black-and-white--low-angle-digital-illustration-in-a-symbolic-traditional-tattoo-art-style.--A-bald--light-skinned-man-with-a-bushy-beard--prominent-eyebrows--and-a-friendly-expression-wears-denim-overalls--2--1.jpg" alt="Geoffrey Huntley">

I discovered Geoffrey through his fascinating post titled "too many model context protocol servers and LLM allocations on the dance floor" - a definitive guide to context engineering that caught my attention.

🔗 [Website](https://ghuntley.com/) | 📧 ghuntley@ghuntley.com

## Favorite Tweet of the Week

https://x.com/Rainmaker1973/status/1952254423432122878

## Books I read this week

- The Mind Illuminated: A Complete Meditation Guide Integrating Buddhist Wisdom and Brain Science: 87225 words
- The Story of Civilization, Vol. 1: Our Oriental Heritage (India, China & More): 24631 words
- Alexander Pushkin Anthology: 10123 words
- How to Live by Derek Sivers: 7399 words
- The 22 Immutable Laws of Marketing: Exposed and Explained by the World's Two: 6156 words
- Full-Stack Tao: 2571 words
- Demand-Side Sales 101: Stop Selling and Help Your Customers Make Progress: 2322 words
- Dialogues by Seneca: 678 words
- The Narrow Road: 390 words

## Favorite Articles I read this week

- [Everything I know about good system design](https://www.seangoedecke.com/good-system-design) by seangoedecke.com - Super useful advice for software engineers.

- [What I learned spending $851 on Reddit Ads](https://successfulsoftware.net/2025/08/11/what-i-learned-spending-851-on-reddit-ads/) by Andy Brice - Andy is also a huge inspiration! In this post he spent $851 testing Reddit ads. Not only was this a total flop, but Reddit seemed to fake some data...

## Other cool links
- [lazy-brush - smooth drawing with mouse](https://lazybrush.dulnan.net/): Draw smooth curves and straight lines with your mouse, finger or any pointing device.

- [Shutter Declutter](https://shutterdeclutter.app)

- [visualrambling.space](https://visualrambling.space/): Just a place to ramble visually

- [Moving Objects in 3D Space](https://visualrambling.space/moving-objects-in-3d/): Trying to understand how to move objects in 3D space

- [The Useless Web](https://theuselessweb.com/): The Useless Web Button... just press it and find where it takes you. The perfect button for the bored, or those looking to find useless sites online!

- [all text in nyc](https://www.alltext.nyc/): Search engine that reveals text hidden in NYC's Street View images (2007-2024). Created by Yufeng Zhao, this tool lets you explore the city through shop signs, graffiti, and street text across all five boroughs.

## Support

You can support this project by using one of the affiliate links below. These are always going to be projects I use and love! No "Bluehost" crap here!

- [Buttondown](https://buttondown.email/refer/rasulkireev) - Email newsletter tool I use to send you this newsletter.
- [Readwise](https://readwise.io/i/rasul) - Best reading software company out there. I you want to up your e-reading game, this is definitely for you! It also so happens that I work for Readwise. Best company out there!
- [Hetzner](https://hetzner.cloud/?ref=Ju1ttKSG0Fn7) - IMHO the best place to buy a VPS or a server for your projects. I'll be doing a tutorial on how to use this in the future.
- [SaaS Pegasus](https://www.saaspegasus.com/?via=rasul) is one of the best (if not the best) ways to quickstart your Django Project. If you have a business idea but don't want to set up all the boring stuff (Auth, Payments, Workers, etc.) this is for you!

## Sponsors

This newsletter is sponsored by [Marketing Agents](https://marketingagents.net). Well, sponsor is a strong word. It is just another project of mine that I wanted to share with you 🙈.

**If you have a side project and are struggling with the marketing side, it might help! It's still in early dev, so any feedback is super useful.**

> If you want to become a real sponsor, just reply to this email 😄
```

```
just sent a weekly issue of my personal newsletter.

here is what I covered:

---

just shipped a major update to my side project and honestly... kinda terrified to start marketing it, but it's time...

---

my 2.5 year old toddler is talking non-stop now and it's honestly the best thing ever.

yes, i get less time to do side projects, but it is what it is. kids are more important, and more fun, to be honest

---

finally broke one of my worst (addictive) habits for good this time

withdrawal was brutal - couldn't stay awake to save my life. but asking for accountability here if anyone wants to check in on me later

---

been playing around with ascii data visualization in the terminal lately, but nothing crazy good yet.

if you know of any libraries that are good fro this kind of thing, please share. relatively actively maintained and can use python are the requirements.

---

@sjgoedecke is my favorite tech blogger these days! huge inspiration. Here as quote from his 'Everything I Know About Good System Design' post that spoke to me

"a complex system that works always evolves from a simple system that works"

---

everything impressive you see started simple and stable, then grew slowly while keeping that foundation solid

---

also discovered this cool developer @GeoffreyHuntley through his "too many model context protocol servers on the dance floor" post.

if you are into AI or want to learn more definitely follow Geoffrey

---

also shared the following in the newsletter (that didn't make sense to add here):
- books I read last week
- favorite articles read last week
- my favorite tweet from last week
- list of cool links/sites i found last week
```

---

Here is the newsletter content to convert this time:
```
{newsletter_content}
```
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro-preview-03-25", contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating tweet thread with Gemini: {e}"
