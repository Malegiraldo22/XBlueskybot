# Automatic X and Bluesky Post Scheduler

This project is an automated social media posting system that generates and posts tweets and Bluesky posts based on trending topics, using AI-powered content generation (Google Gemini), web search (DuckDuckGo), and Google Sheets for logging and tracking.

## Features

- **AI-generated tweets** using Google Gemini
- **Topic and voice selection** for varied and engaging posts
- **Real-time internet search** using DuckDuckGo for fresh and relevant content
- **Automatic posting to X and Bluesky**
- **Logging and tracking** of posts, errors, and rejections in Google Sheets
- **Error handling and retires** to ensure reliability
- **Automatic shceduling** of tweets at regular intervals

## Requirements
Before running the project, ensure you have the following installed:
- Python 3.8+
- Required python packages (see `requirements.txt`)

## Installation

1. Clone this repository
```sh
git clone https://github.com/Malegiraldo22/XBlueskybot.git
cd XBlueskybot
```

2. Install dependencies
```sh
pip install -r requirements.txt
```

3. Set up environment variables
Create a `.env` file and add the following credentials
```
CONSUMER_KEY=your_twitter_consumer_key  
CONSUMER_SECRET=your_twitter_consumer_secret  
XGOOGLE_JSON=your_X_google_service_account_json  
XGOOGLE_SHEET=your_X_google_sheet_url  
BGOOGLE_JSON=your_B_google_service_account_json  
BGOOGLE_SHEET=your_B_google_sheet_url  
GEN_AI_KEY=your_google_gemini_api_key  
BS_USER=your_bluesky_username  
BS_PASSWORD=your_bluesky_password 
```

4. Authenticate X
- Run the script once and follow the instructions to obtain access token

## How it works

1. Google Sheets Authentication

    The script connects to Google Sheets to log posted tweets, long tweets, errors and rejected tweets

2. OAuth Authentication for X

    Handles X API authentication using OAuth1

3. Bluesky Authentication

    Logs into Bluesky using user credentials

4. Theme and Voice selection

    A random theme (e.g., "Space Exploration") and a voice (e.g., "The Sarcastic Cynic") are chosen

5. Internet search for news

    Uses DuckDuckGo to fetch the latest news on the selected theme

6. AI-Powered Tweet Generation

    - Google Gemini generates a tweet based on the theme, voice and news.
    - A separate AI review ensures the tweet is engaging and not generic or robotic

7. Posting and Logging

    - If the tweet is under 280 characters, it gets posted on X and Bluesky
    - If it's too long, it's logged for later review
    - Errors and rejections are tracked in Google Sheets

8. Automated Shceduling

    The script runs automatically every hour to generate and post tweets

## Running the script
To start the automated posting:
```sh
python bot.py
```

## Troubleshooting
- If authentication fails, check API keys and .env variables
- If the tweet limit is exceeded, review the `LongTweets` sheet for overly long tweets
- If Bluesky login fails, verify the `BS_USER` and `BS_PASSWORD`

## License
This project is open-source and licensed under the MIT License

## Contributing
Pull requests are welcome! If you'd like to suggest improvements, feel free to open an issue.