import json
import logging
import os
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("aiw-bot")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]  # e.g. "@aiw_channel" or "-1001234567890"
COURSE_URL = os.environ.get("COURSE_URL", "https://l1troe0.github.io/freelance-sales-ai-course/")
TIMEZONE = ZoneInfo(os.environ.get("BOT_TIMEZONE", "Europe/Moscow"))
POST_HOUR = int(os.environ.get("AUTOPOST_HOUR", "12"))

DATA_DIR = Path(__file__).parent
POSTS_FILE = DATA_DIR / "posts.json"
STATE_FILE = DATA_DIR / "state.json"


def load_posts() -> list[str]:
    with POSTS_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        with STATE_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    return {"next_index": 0}


def save_state(state: dict) -> None:
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Открыть курс →", url=COURSE_URL)]]
    )
    await update.message.reply_text(
        "Привет! Это AIW — заработок на ИИ ⚡\n\n"
        "Здесь бесплатный курс: как находить B2B-клиентов, продавать сайты "
        "и делать их в 2 раза быстрее с помощью ИИ.\n\n"
        "Жми на кнопку ниже, чтобы открыть курс.",
        reply_markup=keyboard,
    )


async def autopost(context: ContextTypes.DEFAULT_TYPE) -> None:
    posts = load_posts()
    if not posts:
        log.warning("posts.json пуст — постить нечего")
        return
    state = load_state()
    idx = state["next_index"] % len(posts)
    text = posts[idx]
    await context.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    state["next_index"] = idx + 1
    save_state(state)
    log.info("Опубликован пост #%s", idx)


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    app.job_queue.run_daily(
        autopost,
        time=time(hour=POST_HOUR, tzinfo=TIMEZONE),
        name="daily_autopost",
    )

    log.info("Бот запущен. Автопостинг в %s:00 (%s)", POST_HOUR, TIMEZONE)
    app.run_polling()


if __name__ == "__main__":
    main()
