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
image_model = os.getenv("OPENAI_IMAGE_MODEL")
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

app = FastAPI()
scheduler = AsyncIOScheduler()

system_prompt = "Ти допомагаєш людині вивчати англійські слова в стилі контекстного запамʼятовування, правила та інші корисні штуки з англійскої мови."
words_prompt = "Згенеруй сьогоднішнє завдання (3 нових слова і вправи в стилі контекстного запамʼятовування) на англійській із перекладом на українську, щоб було зрозуміло, як використовуються слова. Також додай emoji і все це повинно бути коротко і зрозуміло описано."
rule_prompt = "Згенеруй сьогоднішнє коротке, зрозуміле граматичне правило з прикладами. англійською мовою з перекладом на українську і прикладами. Додай emoji."
idioms_prompt = "Згенеруй сьогоднішню ідіому англійською мовою з перекладом на українську і прикладами. Додай emoji."

def generate_task(task_type, system_prompt, user_prompt):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        logging.info(f"{task_type} response got ok!")
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"{task_type} response error {e}")

def generate_image(prompt):
    try:
        response = client.images.generate(
            model=image_model,
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        logging.info(f"Image was generated!")
        return response.data[0].url
    except Exception as e:
        logging.error(f"Image generation error: {e}")
        return None

async def send_message(task_type, system_prompt, user_promot):
    task = generate_task(task_type, system_prompt, user_promot)
    if task:
        image_prompt = f"An educational visual illustration for the topic: {task_type}, minimal, emoji style"
        image_url = generate_image(image_prompt)
        try:
            if image_url:
                response = await bot.send_photo(
                    chat_id=channel_id,
                    photo=image_url,
                    caption=f"{task}"
                )
            else:
                response = await bot.send_message(
                    chat_id=channel_id,
                    text=task
                )
            logging.info(f"{task_type} message was successfully sent! {response}")
        except Exception as e:
            logging.error(f"{task_type} message wasn't sent: {e}")

def schedule_async_task(coro):
    async def runner():
        await coro
    return runner

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(schedule_async_task(send_message("words", system_prompt, words_prompt)), "cron", hour=9, minute=0)
    scheduler.add_job(schedule_async_task(send_message("rules", system_prompt, rule_prompt)), "cron", hour=9, minute=30)
    scheduler.add_job(schedule_async_task(send_message("idioms", system_prompt, idioms_prompt)), "cron", hour=10, minute=0)
    scheduler.add_job(schedule_async_task(send_message("words", system_prompt, words_prompt)), "cron", hour=12, minute=0)
    scheduler.add_job(schedule_async_task(send_message("rules", system_prompt, rule_prompt)), "cron", hour=12, minute=30)
    scheduler.add_job(schedule_async_task(send_message("idioms", system_prompt, idioms_prompt)), "cron", hour=13, minute=0)
    scheduler.add_job(schedule_async_task(send_message("words", system_prompt, words_prompt)), "cron", hour=14, minute=0)
    scheduler.add_job(schedule_async_task(send_message("rules", system_prompt, rule_prompt)), "cron", hour=14, minute=30)
    scheduler.add_job(schedule_async_task(send_message("idioms", system_prompt, idioms_prompt)), "cron", hour=15, minute=0)
    scheduler.add_job(schedule_async_task(send_message("words", system_prompt, words_prompt)), "cron", hour=16, minute=0)
    scheduler.add_job(schedule_async_task(send_message("rules", system_prompt, rule_prompt)), "cron", hour=16, minute=11)
    scheduler.add_job(schedule_async_task(send_message("idioms", system_prompt, idioms_prompt)), "cron", hour=17, minute=0)
    scheduler.start()


@app.get("/")
async def root():
    return {"message": "Daily English bot is running"}

@app.post("/word")
async def trigger_manual_word():
    await send_message("words", system_prompt, words_prompt)
    return {"status": "Words sent manually"}

@app.post("/rule")
async def trigger_manual_rule():
    await send_message("rules", system_prompt, rule_prompt)
    return {"status": "Rule sent manually"}

@app.post("/idioms")
async def trigger_manual_idioms():
    await send_message("idioms", system_prompt, idioms_prompt)
    return {"status": "Idioms sent manually"}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "word":
            asyncio.run(send_message("words", system_prompt, words_prompt))
        elif sys.argv[1] == "rule":
            asyncio.run(send_message("rules", system_prompt, rule_prompt))
        elif sys.argv[1] == "idioms":
            asyncio.run(send_message("idioms", system_prompt, idioms_prompt))
    else:
        import uvicorn
        uvicorn.run("daily_task:app", host="0.0.0.0", port=8000, reload=True)