from requests_oauthlib import OAuth1Session
import os
from google import genai
from google.genai import types
import random
from datetime import datetime
from dotenv import load_dotenv
import time
import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
import gspread
from google.oauth2 import service_account
import json
from textwrap import dedent
from duckduckgo_search import DDGS
from atproto import Client, client_utils

load_dotenv()

#X Google sheets authentication
try:
    google_json = os.getenv('XGOOGLE_JSON')
    service_account_info = json.loads(google_json, strict=False)
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_with_scope = credentials.with_scopes(scope)
    client_gsheets = gspread.authorize(creds_with_scope)
    x_spreadsheet = client_gsheets.open_by_url(os.getenv('XGOOGLE_SHEET'))
    print("Connected to X Google sheets")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

try:
    x_posted_sheet = x_spreadsheet.worksheet("PostedTweets")
    x_long_tweets_sheet = x_spreadsheet.worksheet("LongTweets")
    x_error_sheet = x_spreadsheet.worksheet("Errors")
    x_rejected = x_spreadsheet.worksheet("TweetsRejected")
    print("X Spreadsheets opened")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())


#Bluesky Google Sheets
try:
    google_json = os.getenv('BGOOGLE_JSON')
    service_account_info = json.loads(google_json, strict=False)
    credentials = service_account.Credentials.from_service_account_info(service_account_info)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_with_scope = credentials.with_scopes(scope)
    client_gsheets = gspread.authorize(creds_with_scope)
    spreadsheet = client_gsheets.open_by_url(os.getenv('BGOOGLE_SHEET'))
    print("Connected to Bluesky Google sheets")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

try:
    b_posted_sheet = spreadsheet.worksheet("Posted")
    b_long_tweets_sheet = spreadsheet.worksheet("Long")
    b_error_sheet = spreadsheet.worksheet("Errors")
    b_rejected = spreadsheet.worksheet("Rejected")
    print("Bluesky Spreadsheets opened")
except Exception as e:
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

#X Authentication
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")

# Get request token
request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

try:
    fetch_response = oauth.fetch_request_token(request_token_url)
except ValueError:
    print(
        "There may have been an issue with the consumer_key or consumer_secret you entered."
    )

resource_owner_key = fetch_response.get("oauth_token")
resource_owner_secret = fetch_response.get("oauth_token_secret")

# Get authorization
base_authorization_url = "https://api.twitter.com/oauth/authorize"
authorization_url = oauth.authorization_url(base_authorization_url)
print("Please go here and authorize: %s" % authorization_url)
verifier = input("Paste the PIN here: ")

# Get the access token
access_token_url = "https://api.twitter.com/oauth/access_token"
oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=resource_owner_key,
    resource_owner_secret=resource_owner_secret,
    verifier=verifier,
)
oauth_tokens = oauth.fetch_access_token(access_token_url)

access_token = oauth_tokens["oauth_token"]
access_token_secret = oauth_tokens["oauth_token_secret"]

#Bluesky login
b_client = Client()
profile = b_client.login(os.getenv('BS_USER'), os.getenv('BS_PASSWORD'))

#Gemini Auth
client = genai.Client(api_key=os.getenv('GEN_AI_KEY'))


# Theme selection function
def theme_selection():
    """
    Function that randomly selects a theme and a voice to be used to generate a tweet

    Returns:
        - Theme (str): A theme selected as the main topic of a tweet
        - Voice (str): The voice used to set the tone of the tweet
    """
    topics = [
        "Space Exploration",
        "Cybersecurity & Privacy",
        "Web3 & Decentralization",
        "Climate Change Action & Sustainability",
        "Pop Culture & Entertainment",
        "Memes & Internet Culture",
        "Global News & Geopolitics",
        "Elon Musk",
        "Donald Trump",
        "Vladimir Putin"
    ]

    voices = [
    "The Sarcastic Cynic", "The Optimistic Enthusiast", "The Curious Observer", "The Skeptical Researcher",
    "The Passionate Advocate", "The Relatable Friend", "The Techie Guru", "The Creative Innovator",
    "The World Traveler", "The Foodie Expert", "The Empathetic Listener", "The Nostalgic Storyteller",
    "The Ambitious Hustler", "The Laid-back Observer", "A Software Developer", "A Marketing Strategist",
    "A Financial Advisor", "A Personal Trainer", "A Teacher/Educator", "A Journalist/Reporter",
    "A Data Scientist", "A Designer", "The Conspiracy Theorist (lighthearted)", "The Internet Meme Expert",
    'The "Karen" (Satirically)', "The Confused Millennial/Gen Z"
    ]

    theme = random.choice(topics)
    voice = random.choice(voices)
    return theme, voice

def internet_search(theme):
    """Function that uses DuckDuckGo to search for the most recent news about a topic

    Args:
        theme (str): theme selected by the theme_selection function

    Returns:
        list: List that contains the most recent news
    """
    
    results = DDGS().news(
        keywords=theme,
        region="wt-wt",
        safesearch="off",
        timelimit="d",
        max_results=1
    )

    return results

#Function to log info into sheets
def log_to_sheet(sheet, message):
    """
    Appends a row of data into the google sheet passed with a timestamp

    Args:
        sheet: sheet to store the data
        message: message to store
    """
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
    sheet.append_row([formatted_time, message])

def create_and_publish_tweet(theme, voice, news, max_retries=5):
    """
    Generates a tweet with a theme, voice and a news related with the theme, using Gemini Pro. Checks if the tweet generated is over 280 characters lenght, if it is stores that tweet into a Google sheet as a way of control and retries.
    If the tweet is created correctly, it gets published on twitter and stored in a google sheet as a control log.
    If there's an error, stores the error in a google sheet as a control log, then tries again for at least 5 times. If after 5 tries it's impossible to publish a tweet, waits 10 minutes to try again

    Args:
        theme (str): Theme selected by theme_selection function
        emotion (str): Emotion selected by theme_selection function
        news (list): List that contains the news found by the search tool
        max_retries (int, optional): Max number of retries. Defaults to 5.

    Returns:
        tweet(str): Tweet generated
    """
    attempts = 0
    while attempts < max_retries:
        try:
            tw_gen = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[dedent(f"""\
            **Objective:** To write a single, authentic-sounding tweet (maximum 280 characters) that aligns with a given theme and voice, potentially inspired by a recent news item.

            **Persona:** You are a seasoned social media expert known for crafting engaging and human-like tweets for diverse individuals and brands.

            **Instructions:**

            1.  **Understand the Core Elements:** Carefully review the provided **Theme** and **Voice** description. If a **News Article** is included, read it thoroughly.
            2.  **Embody the Voice:** Adopt the specified **Voice** completely. Consider their typical language, tone, humor (or lack thereof), and overall online persona.
            3.  **Incorporate the Theme:** Ensure the tweet directly relates to the given **Theme**.
            4.  **Utilize the News (If Provided):** If a **News Article** is provided, use it as a genuine point of inspiration. Your tweet should feel like a natural reaction or comment someone with the specified voice might have after reading that news. You can:
                * React directly to the news.
                * Offer a related opinion or insight.
                * Share a personal anecdote triggered by the news.
                * Use the news as a jumping-off point for a broader observation related to the theme.
                * **Maintain a reasonable connection to the news; avoid completely unrelated tangents.**
            5.  **Write Like a Real Person:**
                * Use conversational language.
                * Incorporate contractions and informal phrasing where appropriate for the voice.
                * Consider using rhetorical questions or interjections.
                * Feel free to add a touch of personality or emotion consistent with the voice.
                * **Avoid overly formal or robotic language.**
            6.  **Be Concise and Engaging:** Craft a tweet that is interesting and likely to resonate with an audience.
            7.  **Include Relevant Hashtags:** Add 2-4 relevant hashtags. Think about:
                * Hashtags directly related to the **Theme**.
                * Hashtags related to key individuals or entities mentioned (if applicable).
                * Potentially trending or commonly used hashtags within the topic area.
                * **Prioritize relevance over popularity.**
            8.  **Strict Character Limit:** Ensure your tweet is **no more than 280 characters**, including spaces and hashtags. Be strategic with your word choice and use abbreviations or emojis (sparingly and appropriately for the voice) if needed.
            9. **DO NOT ADD ANYTHING BEFORE THE TWEET, NO MESSAGES LIKE "Okay, here's my attempt:" OR ANYTHING LIKE THAT, JUST THE TWEET**

            **Input Format:**

            Theme: {theme}
            Voice: {voice} (e.g., "The Sarcastic Cynic - Imagine a sarcastic cynic tweeting about this. They might use dry humor, rhetorical questions, or ironic observations.")
            News Article: {news}""")])
            tweet = tw_gen.text
            tw_review = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[dedent(f"""\
            You are a tweet reviewer. Your job is to evaluate tweets and determine if they are suitable for posting. Consider the following criteria:

            1.  **Engagement and Structure:** Is the tweet well-structured, interesting, and likely to engage a real audience? Does it sound like a tweet a real person would post? Does it use natural and conversational language, not overly formal or robotic?
            2.  **Authenticity:** Does the tweet sound authentic and human-like, or does it sound generated? Does the voice seem consistent with the assigned persona?
            3. **Content:** Does the tweet effectively address the provided theme?
            4.  **No Placeholders:** Does the tweet contain any placeholders such as [], [enterprise], [company], etc.?
            After your review, answer ONLY with 'Approved' or 'Rejected'.
            5. No messages before the tweet

            Examples:
            Tweet: Laughter is the best medicine, and memes are the sugar that makes it go down! 😂 Keep sharing the humor, folks!  #SpreadTheJoy #MemesForLife #FunnyContent #LaughterIsTheBestMedicine
            Evaluation: Approved

            Tweet: The [insert industry] industry is at it again! 😅 Just when I thought I'd seen it all, they pull something like this. What's next?!  #NeverADullMoment #IndustryWatch #OnlyInThe[Industry] #GottaLoveIt
            Evaluation: Rejected

            Tweet: Just finished reading a fantastic book about the future of AI! 🤔 It's mind-blowing stuff! Who else is fascinated by this topic? #AI #FutureTech #BookRecommendations
            Evaluation: Approved

            Tweet:  As a techie guru, I gotta say, those new headphones are a game changer! 🎧 I was so focused listening to music, I barely noticed I was at work, ahahah! #TechGuru #MusicLover #NewHeadphones #ProductReview
            Evaluation: Approved

            Tweet: Just another day, another [product name] doing [function] 🙄 #Boring #DailyLife #Meh
            Evaluation: Rejected

            Tweet: OMG, this new [insert tech] is insane! 🤯 It's like we're living in the future. #Tech #Future #Innovation #Whoa
            Evaluation: Rejected
                                 
            Tweet: Okay, here's my attempt:
            Regenerative Flea Market in LA? Sounds lovely, but how do we make *every* market regenerative? Small steps, I guess. Building community is key. Let's lift each other up while lifting up the planet. ❤️ #ClimateAction #Sustainability #CommunityWellness #LAClimateWeek
            Evaluation: Rejected                     

            The tweet to evaluate is: {tweet}""")])
            review = tw_review.text
            print('Review: ', review)
            if review.strip().lower() == "rejected":
                print('Tweet rejected, generating a new one')
                log_to_sheet(x_rejected, tweet)
                log_to_sheet(b_rejected, tweet)
                attempts += 1
                time.sleep(30)
                continue            

            if len(tweet) > 300:
                log_to_sheet(x_long_tweets_sheet, tweet)
                log_to_sheet(b_long_tweets_sheet, tweet)
                print(tweet, ", Tweet to long, generating a new one")
                time.sleep(30)
                continue  # Retry if the tweet is too long
            else:
                b_client.send_post(text=tweet)
                log_to_sheet(b_posted_sheet, tweet)

                oauth = OAuth1Session(
                    consumer_key,
                    client_secret=consumer_secret,
                    resource_owner_key=access_token,
                    resource_owner_secret=access_token_secret
                )
                response = oauth.post(
                    "https://api.twitter.com/2/tweets",
                    json={"text":tweet},
                )
                if response.status_code == 201:
                    log_to_sheet(x_posted_sheet, tweet)
                    print("Response code: {}".format(response.status_code))
                    print("Tweet posted: ", tweet)
                    break
                else:
                    log_to_sheet(x_error_sheet, response.status_code)
                    attempts += 1
                print("Tweet posted: ", tweet)
                break
        except Exception as e:
            attempts += 1
            error_message = f"{type(e).__name__} - {e}"
            log_to_sheet(x_error_sheet, error_message)
            log_to_sheet(b_error_sheet, error_message)
            current_time = datetime.now()
            formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
            print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())

            if attempts < max_retries:
                time.sleep(600)
            else:
                error_message = "Maximum retry attempts reached. Could not publish the tweet."
                log_to_sheet(x_error_sheet, error_message)
                log_to_sheet(b_error_sheet, error_message)
                current_time = datetime.now()
                formatted_time = current_time.strftime("%d-%m-%Y %H:%M:%S")
                print("Error: ", formatted_time, ": An error occurred, ", type(e).__name__, "-", e, traceback.format_exc())
                print("Could not publish the tweet")
                return None
            
# Function to run periodically
def run_periodically():
    """
    Creates and post a tweet
    """
    theme, emotion = theme_selection()
    news = internet_search(theme)
    create_and_publish_tweet(theme, emotion, news)
    print("Schedule complete: Tweet posted")

def tweet_schedule():
    # Start a thread to run the periodic function
    scheduler = BlockingScheduler(timezone='America/Bogota', daemon=True)
    scheduler.add_job(run_periodically, 'interval', hours=1)
    scheduler.start()

    for job in scheduler.get_jobs():
        msg = str(job.next_run_time)
        print(f"Next tweet will be sent at: {msg}")

tweet_schedule()