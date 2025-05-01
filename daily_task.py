from fastapi import FastAPI
from openai import OpenAI
from dotenv import load_dotenv
import os
from telegram import Bot
from datetime import datetime
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sys

load_dotenv()

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = os.getenv("OPENAI_MODEL")
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

app = FastAPI()
scheduler = AsyncIOScheduler()

def generate_words_task():
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Ти допомагаєш людині вивчати англійські слова. Дай 3 нових слова і вправи в стилі контекстного запамʼятовування."
                },
                {
                    "role": "user",
                    "content": "Згенеруй сьогоднішнє задання на англійській із перекладом на українську, щоб було зрозуміло, як використовуються слова. Також додай emoji і все це повинно бути коротко і зрозуміло описано."
                }
            ]
        )
        logging.info(f"Words response got ok!")
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Words response error {e}")
        return None

def generate_rule_task():
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Ти допомагаєш людині вивчати граматику англійської мови. Дай коротке, зрозуміле граматичне правило з прикладами."
                },
                {
                    "role": "user",
                    "content": "Згенеруй сьогоднішнє граматичне правило англійською мовою з перекладом на українську і прикладами. Додай emoji."
                }
            ]
        )
        logging.info(f"Rule response got ok!")
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Rule response error {e}")
        return None

async def send_words():
    task = generate_words_task()
    if task:
        try:
            response = await bot.send_message(
                chat_id=channel_id,
                text=f"📚 Завдання на сьогодні\n\n{task}"
            )
            logging.info(f"Words message was successfully sent! {response}")
        except Exception as e:
            logging.error(f"Words message wasn't sent: {e}")

async def send_rule():
    task = generate_rule_task()
    if task:
        try:
            response = await bot.send_message(
                chat_id=channel_id,
                text=f"📘 Граматичне правило дня\n\n{task}"
            )
            logging.info(f"Rule message was successfully sent! {response}")
        except Exception as e:
            logging.error(f"Rule message wasn't sent: {e}")

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(send_words, "cron", hour=9, minute=0)
    scheduler.add_job(send_rule, "cron", hour=9, minute=15)
    scheduler.start()

@app.get("/")
async def root():
    return {"message": "Daily English bot is running"}

@app.post("/word")
async def trigger_manual_word():
    await send_words()
    return {"status": "Words sent manually"}

@app.post("/rule")
async def trigger_manual_rule():
    await send_rule()
    return {"status": "Rule sent manually"}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "word":
            asyncio.run(send_words())
        elif sys.argv[1] == "rule":
            asyncio.run(send_rule())
    else:
        import uvicorn
        uvicorn.run("daily_sender:app", host="0.0.0.0", port=8000, reload=True)
