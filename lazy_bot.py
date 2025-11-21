import os
import feedparser
import smtplib
import google.generativeai as genai
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
# The 'import schedule' line has been removed here.

# ================= CONFIGURATION (Read from GitHub Secrets) =================
# CRITICAL FIX: The names below now match your GitHub Secret names:
GEMINI_KEY = os.environ.get("GEMINI_KEY")
EMAIL_ADDRESS = os.environ.get("YOUR_GMAIL")         # Changed from EMAIL_ADDRESS
EMAIL_PASSWORD = os.environ.get("YOUR_APP_PASSWORD") # Changed from EMAIL_PASSWORD
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
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = BLOGGER_EMAIL
        # This subject line becomes the post title
        msg['Subject'] = f"TREND ALERT: {topic}"
        
        msg.attach(MIMEText(blog_html, 'html'))

        # Use the corrected environment variables for login
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, BLOGGER_EMAIL, msg.as_string())
        server.quit()
        
        print("✅ Blog posted successfully via Email!")
        
    except Exception as e:
        # If the failure happens here, it will likely be an API or authentication error.
        print(f"Error encountered: {e}")

# Call the job function once. The GitHub Actions cron handles the daily schedule.
job()
