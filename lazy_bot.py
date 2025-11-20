import os
import feedparser
import smtplib
import google.generativeai as genai
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import schedule

# ================= CONFIGURATION (Read from GitHub Secrets) =================
# These variables are read from the secrets you set in GitHub.
GEMINI_KEY = os.environ.get("GEMINI_KEY")
YOUR_GMAIL = os.environ.get("YOUR_GMAIL")
YOUR_APP_PASSWORD = os.environ.get("YOUR_APP_PASSWORD")
BLOGGER_EMAIL = os.environ.get("BLOGGER_EMAIL")

# ============================================================================

# Setup Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

def job():
    print(f"[{datetime.now()}] Starting daily trend post...")
    
    # 1. FIND TREND
    # Change 'geo=IN' to a different country code if needed (e.g., 'US', 'GB', etc.)
    rss_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN"
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("No trends found.")
        return

    top_trend = feed.entries[0]
    topic = top_trend.title
    news_link = top_trend.ht_news_item_url
    print(f"🔥 Trending Topic: {topic}")

    # 2. WRITE BLOG (Using Gemini)
    prompt = f"""
    Write an engaging, viral news blog post about the following trending topic: "{topic}". 
    
    **Instructions for the AI:**
    1. Tone: Exciting, Urgent, and News-style.
    2. Structure: Use HTML tags for formatting.
    <h1>Catchy Clickbait Title on the Topic</h1>
    <p><b>Introduction:</b> Hook the reader immediately.</p>
    <h2>What is Happening Now?</h2>
    <p>Explain the news clearly with a few paragraphs.</p>
    <h2>Why This Matters</h2>
    <p>Explain the impact on the local audience.</p>
    <p><i>Source: <a href="{news_link}">Read the full story here</a></i></p>
    
    OUTPUT ONLY THE HTML CODE. DO NOT include any surrounding markdown like ```html or ```.
    """
    
    try:
        response = model.generate_content(prompt)
        blog_html = response.text
        
        # 3. EMAIL TO BLOGGER
        msg = MIMEMultipart()
        msg['From'] = YOUR_GMAIL
        msg['To'] = BLOGGER_EMAIL
        # This subject line becomes the post title
        msg['Subject'] = f"TREND ALERT: {topic}"
        
        msg.attach(MIMEText(blog_html, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(YOUR_GMAIL, YOUR_APP_PASSWORD)
        server.sendmail(YOUR_GMAIL, BLOGGER_EMAIL, msg.as_string())
        server.quit()
        
        print("✅ Blog posted successfully via Email!")
        
    except Exception as e:
        print(f"Error encountered: {e}")

# The schedule run loop is not needed in GitHub Actions (it uses cron)
# We only call job() once for the workflow run.
job()
