# main.py — 🎉 Полностью рабочий Metodist-CoT с кнопками!
# ✅ Абсолютные пути | Красивый UI | Полная обработка кнопок | Эмодзи | HTML

import json
import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from src import TELEGRAMTOKEN, YANDEX_CLOUD_API_KEY, FOLDER_ID

# ✅ АБСОЛЮТНЫЕ пути — работают всегда
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "configs", "Metodist-CoT.json")  # ИЗМЕНИ НА СВОЁ ИМЯ!
PRESETS_PATH = os.path.join(BASE_DIR, "configs", "presets.json")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ------------------ utils ------------------

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_mode(context: ContextTypes.DEFAULT_TYPE, cfg: dict) -> str:
    return context.user_data.get("mode") or cfg.get("default_mode", "balanced")


def get_user_overrides(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.get("overrides", {}) or {}


def build_completion_options(cfg: dict, mode: str, presets: dict, overrides: dict) -> dict:
    base_opts = dict(cfg.get("completionOptions", {}))
    if mode not in presets:
        mode = cfg.get("default_mode", "balanced")
    
    preset = presets[mode]
    base_opts["temperature"] = preset["temperature"]
    base_opts["maxTokens"] = preset["maxTokens"]
    
    if "temperature" in overrides: base_opts["temperature"] = overrides["temperature"]
    if "maxTokens" in overrides: base_opts["maxTokens"] = overrides["maxTokens"]
    
    return base_opts


def call_yandexgpt_completion(user_text: str, completion_options: dict, cfg: dict) -> str:
    endpoint, model_name, system_prompt = cfg["endpoint"], cfg["model_name"], cfg.get("system_prompt", "")
    
    payload = {
        "modelUri": f"gpt://{FOLDER_ID}/{model_name}",
        "completionOptions": completion_options,
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_text},
        ],
    }
    
    headers = {"Content-Type": "application/json", "Authorization": f"Api-Key {YANDEX_CLOUD_API_KEY}"}
    r = requests.post(endpoint, headers=headers, json=payload, timeout=180)
    r.raise_for_status()
    
    data = r.json()
    alts = data.get("result", {}).get("alternatives", [])
    return alts[0].get("message", {}).get("text", "❌ Пустой ответ") if alts else "❌ Нет ответа"


# ------------------ Commands ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cfg, presets = load_json(CONFIG_PATH), load_json(PRESETS_PATH)
    except FileNotFoundError as e:
        await update.message.reply_text(f"❌ <b>Конфиг:</b> {e}", parse_mode="HTML")
        return

    mode = get_mode(context, cfg)
    keyboard = [
        [InlineKeyboardButton("🔧 Режим", callback_data="mode")],
        [InlineKeyboardButton("📊 Параметры", callback_data="params")],
        [InlineKeyboardButton("⚙️ Настроить", callback_data="set")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    await update.message.reply_text(
        "🤖 <b>Metodist-CoT онлайн!</b>\n\n"
        f"🎯 <b>Режим:</b> <code>{mode}</code>\n"
        f"📈 <b>Режимы:</b> {', '.join(presets.keys())}\n\n"
        "💬 <i>Задавай вопросы!</i>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔙 Главное", callback_data="start")]]
    await update.message.reply_text(
        "🆘 <b>📖 Помощь</b>\n\n"
        "• <code>/mode balanced</code>\n"
        "• <code>/params</code>\n"
        "• <code>/set temperature 0.7</code>\n"
        "• <code>/set reset</code>\n\n"
        "<b>Режимы:</b>\n"
        "⚪ <i>strict</i> — точность\n"
        "🟢 <i>balanced</i> — баланс\n"
        "🔴 <i>creative</i> — креатив",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cfg, presets = load_json(CONFIG_PATH), load_json(PRESETS_PATH)
    except FileNotFoundError:
        await update.message.reply_text("❌ Конфиг не найден")
        return

    if not context.args:
        current = get_mode(context, cfg)
        keyboard = [[InlineKeyboardButton(p, callback_data=f"mode_{p}")] for p in presets] + [[InlineKeyboardButton("🔙 Главное", callback_data="start")]]
        await update.message.reply_text(
            f"🎯 <b>Режим:</b> <code>{current}</code>\n\nВыбери:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    new_mode = context.args[0].strip().lower()
    if new_mode in presets:
        context.user_data["mode"] = new_mode
        await update.message.reply_text(f"✅ <b>{new_mode}</b> активирован!", parse_mode="HTML")
    else:
        await update.message.reply_text(f"❌ Нет <code>{new_mode}</code>", parse_mode="HTML")


async def params_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cfg, presets = load_json(CONFIG_PATH), load_json(PRESETS_PATH)
    except FileNotFoundError:
        await update.message.reply_text("❌ Конфиг не найден")
        return

    mode, overrides = get_mode(context, cfg), get_user_overrides(context)
    opts = build_completion_options(cfg, mode, presets, overrides)
    
    keyboard = [[InlineKeyboardButton("🔙 Главное", callback_data="start")]]
    await update.message.reply_text(
        f"📊 <b>Параметры:</b>\n\n"
        f"🎯 Режим: <code>{mode}</code>\n"
        f"🌡️ Temp: <code>{opts['temperature']:.2f}</code>\n"
        f"📜 Tokens: <code>{opts['maxTokens']}</code>\n"
        f"🔧 Overrides: <code>{overrides or 'нет'}</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚙️ <b>/set temperature 0.7</b>\n"
            "<b>/set maxTokens 2500</b>\n"
            "<b>/set reset</b>",
            parse_mode="HTML"
        )
        return

    sub, overrides = context.args[0].strip().lower(), get_user_overrides(context)
    
    if sub == "reset":
        context.user_data["overrides"] = {}
        await update.message.reply_text("✅ Overrides сброшены")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ /set temperature 0.7")
        return

    key, raw_value = sub, context.args[1].strip()
    
    if key == "temperature":
        try:
            value = float(raw_value)
            if 0 <= value <= 2:
                overrides["temperature"] = value
                context.user_data["overrides"] = overrides
                await update.message.reply_text(f"✅ Temp: <code>{value:.2f}</code>", parse_mode="HTML")
            else:
                await update.message.reply_text("❌ Temp: 0..2")
        except:
            await update.message.reply_text("❌ Число!")
        return

    if key in ("maxtokens", "max_tokens", "maxTokens"):
        try:
            value = int(raw_value)
            if value > 0:
                overrides["maxTokens"] = value
                context.user_data["overrides"] = overrides
                await update.message.reply_text(f"✅ Tokens: <code>{value}</code>", parse_mode="HTML")
            else:
                await update.message.reply_text("❌ Tokens > 0")
        except:
            await update.message.reply_text("❌ Целое число!")
        return

    await update.message.reply_text("❌ temperature | maxTokens | reset")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cfg, presets = load_json(CONFIG_PATH), load_json(PRESETS_PATH)
    except FileNotFoundError:
        await update.message.reply_text("❌ Конфиг не найден")
        return

    mode, overrides = get_mode(context, cfg), get_user_overrides(context)
    opts = build_completion_options(cfg, mode, presets, overrides)
    
    status = await update.message.reply_text("🤔 <i>Думаю с YandexGPT...</i>", parse_mode="HTML")
    
    try:
        answer = call_yandexgpt_completion(update.message.text, opts, cfg)
        await status.edit_text(answer)
    except Exception as e:
        logger.exception(e)
        await status.edit_text("❌ YandexGPT недоступен")


# ------------------ КНОПКИ ------------------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "start": await start(query, context)
    elif data == "help": await help_cmd(query, context)
    elif data == "params": await params_cmd(query, context)
    elif data == "set": await set_cmd(query, context)
    elif data == "mode": await mode_cmd(query, context)
    elif data.startswith("mode_"):
        new_mode = data.replace("mode_", "")
        try:
            cfg, presets = load_json(CONFIG_PATH), load_json(PRESETS_PATH)
            context.user_data["mode"] = new_mode
            await query.edit_message_text(f"✅ <b>Режим:</b> <code>{new_mode}</code>\n\n💬 Пиши!", parse_mode="HTML")
        except:
            await query.edit_message_text("❌ Конфиг не найден")


# ------------------ main ------------------
def main():
    app = ApplicationBuilder().token(TELEGRAMTOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("mode", mode_cmd))
    app.add_handler(CommandHandler("params", params_cmd))
    app.add_handler(CommandHandler("set", set_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🚀 Metodist-CoT запущен! 🎉")
    app.run_polling()

if __name__ == "__main__":
    main()
