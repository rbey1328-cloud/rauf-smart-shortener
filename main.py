
import os
import sqlite3
import secrets
import threading
from flask import Flask, redirect, request, render_template_string
import telebot

BOT_TOKEN = os.environ["BOT_TOKEN"]
BASE_URL = os.environ["BASE_URL"].rstrip("/")
AD_CODE = os.environ.get("ADSTERRA_AD_CODE", "")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

def setup_db():
    with sqlite3.connect("links.db") as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS links (
                code TEXT PRIMARY KEY,
                target TEXT NOT NULL
            )
        """)

def save_link(code, url):
    with sqlite3.connect("links.db") as db:
        db.execute(
            "INSERT INTO links VALUES (?, ?)", (code, url)
        )

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Welcome! Send me any website URL and I will create a short link."
    )

@bot.message_handler(func=lambda m: bool(m.text))
def shorten(message):
    url = message.text.strip()

    if not (url.startswith("https://") or url.startswith("http://")):
        bot.reply_to(message, "Please send a valid URL starting with https://")
        return

    code = secrets.token_urlsafe(5)
    save_link(code, url)
    bot.reply_to(message, f"Your short link:\n{BASE_URL}/s/{code}")

@app.route("/s/<code>")
def visit(code):
    with sqlite3.connect("links.db") as db:
        row = db.execute(
            "SELECT target FROM links WHERE code = ?", (code,)
        ).fetchone()

    if not row:
        return "Link not found", 404

    page = """
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
    <body style="font-family:Arial;text-align:center;padding:30px">
      <h2>Your link is ready</h2>
      <div>AD_PLACEHOLDER</div>
      <p><a href="TARGET_URL">Continue to your destination</a></p>
    </body>
    </html>
    """
    page = page.replace("AD_PLACEHOLDER", AD_CODE)
    page = page.replace("TARGET_URL", row[0])
    return page

@app.route("/")
def home():
    return "Rauf Smart Shortener is running!"

if __name__ == "__main__":
    setup_db()
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
  
