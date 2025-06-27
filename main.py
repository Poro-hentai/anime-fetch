from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    InlineQueryHandler,
    filters,
    ContextTypes
)
from telegram import InlineQueryResultArticle, InputTextMessageContent
from flask import Flask
import logging
import difflib
import uuid
import threading
import json
import os

logging.basicConfig(level=logging.INFO)

# --- Configuration ---
API_TOKEN = os.environ.get("API_TOKEN")
POSTS_FILE = "posts.json"
REQUESTS_FILE = "requests.json"
USERS_FILE = "users.json"
GROUP_CHAT = "@sister_leveling"  # Group username or chat ID where requests get forwarded

for file_name in [POSTS_FILE, REQUESTS_FILE, USERS_FILE]:
    if not os.path.exists(file_name):
        with open(file_name, "w") as f:
            json.dump({} if file_name != REQUESTS_FILE else [], f)  # requests.json as list

# URLs for media and captions for start/about/help
START_URL = "https://telegra.ph/file/050a20dace942a60220c0-6afbc023e43fad29c7.jpg"
ABOUT_URL = "https://telegra.ph/file/9d18345731db88fff4f8c-d2b3920631195c5747.jpg"
HELP_URL = "https://telegra.ph/file/e6ec31fc792d072da2b7e-54e7c7d4c5651823b3.jpg"

START_CAPTION = (
    "🌸 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ「 ᴀɴɪᴍᴇ ɢᴀʀᴅᴇɴ 」🌸\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "➤ ᴅᴏᴡɴʟᴏᴀᴅ ʏᴏᴜʀ ғᴀᴠᴏʀɪᴛᴇ ᴀɴɪᴍᴇ.\n"
    "➤ sᴇɴᴅ ᴀɴɪᴍᴇ ʀᴇǫᴜᴇsᴛs. \n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🔰 ɴᴀᴠɪɢᴀᴛᴇ ᴛʜᴇ ɢᴀʀᴅᴇɴ:\n"
    "⤷ ᴛᴀᴘ 『 ʜᴇʟᴘ 』ᴛᴏ ᴠɪᴇᴡ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs\n"
    "⤷ ᴛᴀᴘ 『 ᴀʙᴏᴜᴛ 』ᴛᴏ sᴇᴇ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs & ᴍɪssɪᴏɴ\n"
    "⤷ ᴛᴀᴘ 『 ᴄʟᴏsᴇ 』ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜɪs ᴍᴇssᴀɢᴇ\n"
)

ABOUT_CAPTION = (
    " ᴀʙᴏᴜᴛ sᴇᴄᴛɪᴏɴ:-\n"
    "🎥 ᴛʜɪs ʙᴏᴛ ɪs ᴍᴀᴅᴇ ғᴏʀ ʜᴇʟᴘɪɴɢ ᴜsᴇʀs ғɪɴᴅ & ʀᴇǫᴜᴇsᴛ ᴀɴɪᴍᴇ easilʏ.\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "=>📌 ᴏғғɪᴄɪᴀʟ ᴄʜᴀɴɴᴇʟs & ɢʀᴏᴜᴘs:\n"
    "• 💬 @sister_leveling  - ᴀɴɪᴍᴇ ɢʀᴏᴜᴘ\n"
    "• 🔗 @Lord_Shadow_Sama - ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ\n"
    "• 🌟 @Garden_Sama      - ɢᴀʀᴅᴇɴ\n\n"
    "❓ɪғ ʏᴏᴜ ғᴀᴄᴇ ᴀɴʏ ɪssᴜᴇs, ғᴇᴇʟ ғʀᴇᴇ ᴛᴏ ᴀsᴋ ғᴏʀ ʜᴇʟᴘ ɪɴ ᴏᴜʀ ᴀɴɪᴍᴇ ɢʀᴏᴜᴘ."
)

HELP_CAPTION = (
    "ᴄᴏᴍᴍᴀᴅs:-\n"
    "/start - sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ ᴏʀ sᴇᴇ ᴀʙᴏᴜᴛ/ʜᴇʟᴘ\n"
    "/animelist - ʟɪsᴛ ᴀʟʟ sᴀᴠᴇᴅ ᴀɴɪᴍᴇ ᴘᴏsᴛs\n"
    "/search Naruto - sᴇᴀʀᴄʜ ᴀɴɪᴍᴇ ᴘᴏsᴛs ʙʏ ɴᴀᴍᴇ\n"
    "/requestanime Naruto - ʀᴇǫᴜᴇsᴛ ᴀɴ ᴀɴɪᴍᴇ (ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴡɪʟʟ ʙᴇ sᴇɴᴛ ᴛᴏ ᴛʜᴇ ɢʀᴏᴜᴘ)\n"
    "/viewrequests - ᴠɪᴇᴡ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛs\n"
    "/cancel - ᴄᴀɴᴄᴇʟ ᴀɴʏ ᴏɴɢᴏɪɴɢ ᴀᴄᴛɪᴏɴ\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "ғᴏʀ ᴍᴏʀᴇ ʜᴇʟᴘ ᴊᴏɪɴ:- @Sister_leveling ᴀɴᴅ ᴛᴇʟʟ ᴀᴅᴍɪɴ"
)

# States for ConversationHandler
WAITING_FOR_NAME = 0
WAITING_FOR_BROADCAST = 1

# --- Utility Functions ---
def load_data(file_name):
    with open(file_name, "r") as f:
        data = json.load(f)
        if file_name == REQUESTS_FILE and not isinstance(data, list):
            data = []
        if file_name != REQUESTS_FILE and not isinstance(data, dict):
            data = {}
    return data

def save_data(file_name, data):
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

# Helper: parse inline keyboard buttons from the message (if any)
def extract_buttons(message):
    if message.reply_markup and isinstance(message.reply_markup, InlineKeyboardMarkup):
        buttons = []
        for row in message.reply_markup.inline_keyboard:
            row_buttons = []
            for btn in row:
                btn_data = {"text": btn.text}
                if btn.callback_data:
                    btn_data["callback_data"] = btn.callback_data
                elif btn.url:
                    btn_data["url"] = btn.url
                row_buttons.append(btn_data)
            buttons.append(row_buttons)
        return buttons
    return None

# Helper to recreate InlineKeyboardMarkup from stored buttons
def build_keyboard(buttons):
    if not buttons:
        return None
    keyboard = []
    for row in buttons:
        kb_row = []
        for btn in row:
            if "callback_data" in btn:
                kb_row.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["callback_data"]))
            elif "url" in btn:
                kb_row.append(InlineKeyboardButton(text=btn["text"], url=btn["url"]))
            else:
                kb_row.append(InlineKeyboardButton(text=btn["text"], callback_data="noop"))
        keyboard.append(kb_row)
    return InlineKeyboardMarkup(keyboard)

# Admin-only decorator
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_ids = [5759232282]  # List of allowed admin IDs
        user_id = update.effective_user.id

        if user_id not in admin_ids:
            # If it's a command
            if hasattr(update, "message") and update.message:
                await update.message.reply_text("ʙᴀᴋᴀ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ sᴇɴᴘᴀɪ.")
            # If it's a button press
            elif hasattr(update, "callback_query") and update.callback_query:
                await update.callback_query.answer("ʙᴀᴋᴀ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ sᴇɴᴘᴀɪ.", show_alert=True)
            return ConversationHandler.END
        return await func(update, context)
    return wrapper

# --- Bot Command Handlers ---

# Save user info who starts the bot
async def save_user(update: Update):
    user = update.effective_user
    users = load_data(USERS_FILE)
    # Save username, first name, last name, keyed by user id
    users[str(user.id)] = {
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
    }
    save_data(USERS_FILE, users)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_user(update)
    keyboard = [
        [
            InlineKeyboardButton("ᴀʙᴏᴜᴛ 📜", callback_data="about"),
            InlineKeyboardButton("ʜᴇʟᴘ ⚙️", callback_data="help"),
        ],
        [InlineKeyboardButton("𝙲ʟᴏsᴇ", callback_data="close")],
    ]
    await update.message.reply_photo(
        photo=START_URL,
        caption=START_CAPTION,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# addpost command starts here
@admin_only
async def addpost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴄᴏɴᴛᴀɪɴɪɴɢ ᴛʜᴇ ᴀɴɪᴍᴇ ᴅᴇᴛᴀɪʟs ᴛᴏ savᴇ.")
        return ConversationHandler.END

    reply_msg = update.message.reply_to_message

    media_file_id = None
    media_type = None
    if reply_msg.photo:
        media_file_id = reply_msg.photo[-1].file_id
        media_type = "photo"
    elif reply_msg.document:
        media_file_id = reply_msg.document.file_id
        media_type = "document"
    else:
        await update.message.reply_text("ɴᴏ sᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ ғᴏᴜɴᴅ (ᴘʜᴏᴛᴏ/ᴅᴏᴄᴜᴍᴇɴᴛ).")
        return ConversationHandler.END

    caption = reply_msg.caption or ""
    buttons = extract_buttons(reply_msg)

    context.user_data["media"] = {"file_id": media_file_id, "type": media_type}
    context.user_data["caption"] = caption
    context.user_data["buttons"] = buttons

    await update.message.reply_text("ᴡʜᴀᴛ ɴᴀᴍᴇ sʜᴏᴜʟᴅ ɪ sᴀᴠᴇ ᴛʜɪs ᴘᴏsᴛ ᴀs? ʀᴇᴘʟʏ ᴡɪᴛʜ ᴛʜᴇ namᴇ.")
    return WAITING_FOR_NAME

# Save post with media, caption, buttons
async def save_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post_name = update.message.text.strip()
    if not post_name:
        await update.message.reply_text("Invaliᴅ ɴᴀᴍᴇ. ᴘʟᴇᴀsᴇ ᴛʀʏ agaiɴ.")
        return WAITING_FOR_NAME

    media = context.user_data.get("media")
    caption = context.user_data.get("caption")
    buttons = context.user_data.get("buttons")

    posts = load_data(POSTS_FILE)
    posts[post_name] = {
        "media": media,
        "caption": caption,
        "buttons": buttons,
    }
    save_data(POSTS_FILE, posts)

    await update.message.reply_text(f"Posᴛ sᴀᴠᴇᴅ ᴀs '{post_name}'!")
    return ConversationHandler.END

# Show Anime List
async def animelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    posts = load_data(POSTS_FILE)
    if not posts:
        await update.message.reply_text("❌ ɴᴏ ᴀɴɪᴍᴇ ᴘᴏsᴛs sᴀᴠᴇᴅ ʏᴇᴛ!")
        return

    sorted_posts = sorted(posts.keys(), key=lambda x: x.lower())
    grouped = {}

    for name in sorted_posts:
        key = name[0].upper()
        grouped.setdefault(key, []).append(name)

    text = "*📚 ᴀɴɪᴍᴇ ʟɪʙʀᴀʀʏ - sᴏʀᴛᴇᴅ ᴀ–ᴢ*\n\n"

    for letter in sorted(grouped):
        text += f"🔠 *{letter}*\n"
        for title in grouped[letter]:
            text += f"• {title}\n"
        text += "\n"

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# Updated Search: Fuzzy matching and partial
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip().lower()
    if not query:
        await update.message.reply_text("❗ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ sᴇᴀʀᴄʜ ᴛᴇʀᴍ. ʟɪᴋᴇ ᴛʜɪs :- /search ɴᴀʀᴜᴛᴏ")
        return

    posts = load_data(POSTS_FILE)
    post_names = list(posts.keys())

    # Get close matches using difflib
    close_matches = difflib.get_close_matches(query, post_names, n=10, cutoff=0.4)

    # Also include substring matches
    substring_matches = [name for name in post_names if query in name.lower()]

    # Combine and remove duplicates
    all_matches = list(dict.fromkeys(close_matches + substring_matches))

    if not all_matches:
        await update.message.reply_text("❌ ɴᴏ ᴍᴀᴛᴄʜɪɴɢ ᴀɴɪᴍᴇ ғᴏᴜɴᴅ!")
        return

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"viewpost:{name}")] for name in all_matches
    ]
    await update.message.reply_text(
        f"🔎 Search results for: {query}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Request anime command: save multiple requests as a list, forward to group
async def requestanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request_text = " ".join(context.args).strip()
    if not request_text:
        await update.message.reply_text("ᴘʟᴇᴀsᴇ sᴘᴇᴄɪғʏ ᴛʜᴇ ᴀɴɪᴍᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ requesᴛ.\n ʙʏ ᴡʀɪᴛɪɴɢ ʟɪᴋᴇ ᴛʜɪs - \n /requestanime ɴᴀᴛᴜᴛᴏ")
        return

    requests = load_data(REQUESTS_FILE)  # now a list

    user = update.effective_user
    user_name = user.username or user.first_name or "Unknown"

    # Append new request entry as a dict
    requests.append({
        "user_id": user.id,
        "username": user_name,
        "anime": request_text,
    })
    save_data(REQUESTS_FILE, requests)

    await update.message.reply_text(f"✅ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ғᴏʀ '{request_text}' ʜᴀᴅ ʙᴇᴇɴ ʀᴇᴄᴏʀᴅᴇᴅ!")

    try:
        await context.bot.send_message(
            chat_id=GROUP_CHAT,
            text=f"📢 ɴᴇᴡ ᴀɴɪᴍᴇ ʀᴇǫᴜᴇsᴛ ғʀᴏᴍ - \n@{user_name}:-{request_text}"
        )
    except Exception as e:
        print(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʀᴇǫᴜᴇsᴛ ᴛᴏ ɢʀᴏᴜᴘ: {e}")

# send msg to user
@admin_only
async def msguser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("ᴜsᴇ ʟɪᴋᴇ ᴛʜɪs:- /msguser <user_id ᴏʀ ᴡʀɪᴛᴇ @username> <ʏᴏᴜʀ ᴍᴇssᴀɢᴇ>")
        return

    user_ref = args[0]
    msg_text = " ".join(args[1:])

    users = load_data(USERS_FILE)
    
    # Try to get user_id from username if needed
    if user_ref.startswith("@"):
        username = user_ref[1:].lower()
        found_id = None
        for uid, data in users.items():
            if data.get("username", "").lower() == username:
                found_id = uid
                break
        if not found_id:
            await update.message.reply_text(f"❌ ᴜsᴇʀɴᴀᴍᴇ '{user_ref}' ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴜsᴇʀ ᴅᴀᴛᴀʙᴀsᴇ.")
            return
        user_id = int(found_id)
    else:
        try:
            user_id = int(user_ref)
        except ValueError:
            await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ID ᴏʀ usernamᴇ.")
            return

    try:
        await context.bot.send_message(chat_id=user_id, text=msg_text)
        await update.message.reply_text(f"✅ ᴍᴇssᴀɢᴇ sᴇɴᴛ ᴛᴏ {user_id}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇ: {e}")

# deletepost
@admin_only
async def deletepost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ᴜsᴇ ʟɪᴋᴇ ᴛʜɪs: /deletepost <ᴘᴏsᴛ ɴᴀᴍᴇ>")
        return

    post_name = " ".join(context.args).strip()
    posts = load_data(POSTS_FILE)

    if post_name not in posts:
        await update.message.reply_text(f"ɴᴏ ᴘᴏsᴛ ғᴏᴜɴᴅ ᴡɪᴛʜ ɴᴀᴍᴇ '{post_name}'.")
        return

    del posts[post_name]
    save_data(POSTS_FILE, posts)
    await update.message.reply_text(f"✅ ᴘᴏsᴛ '{post_name}' ʜᴀs ʙᴇᴇɴ ᴅᴇʟᴇᴛᴇᴅ.")

# Admin-only command to remove a request (exact match, case-insensitive)
@admin_only
async def removereq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("ᴜsᴇ ʟɪᴋᴇ ᴛʜɪs: /removereq <ᴀɴɪᴍᴇ ɴᴀᴍᴇ>")
        return

    anime_name = " ".join(args).strip().lower()
    requests = load_data(REQUESTS_FILE)

    original_count = len(requests)

    updated_requests = [r for r in requests if r["anime"].strip().lower() != anime_name]

    save_data(REQUESTS_FILE, updated_requests)

    removed_count = original_count - len(updated_requests)
    if removed_count > 0:
        await update.message.reply_text(f"✅ ʀᴇᴍᴏᴠᴇᴅ {removed_count} ʀᴇǫᴜᴇsᴛ(s) ғᴏʀ '{anime_name}'.")
    else:
        await update.message.reply_text(f"❌ ɴᴏ ᴇxᴀᴄᴛ ᴍᴀᴛᴄʜ ғᴏᴜɴᴅ ғᴏʀ '{anime_name}'.")

# View all anime requests
@admin_only
async def viewrequests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    requests = load_data(REQUESTS_FILE)
    if not requests:
        await update.message.reply_text("ɴᴏ ʀᴇǫᴜᴇsᴛs ғᴏᴜɴᴅ!")
        return

    response = "ᴀɴɪᴍᴇ ʀᴇǫᴜᴇsᴛs:\n\n"
    for req in requests:
        user_display = f"@{req['username']}" if req['username'] else "Unknown"
        response += f"{user_display}: {req['anime']}\n"
    await update.message.reply_text(response)

# Admin-only command: show how many users have started the bot
@admin_only
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_data(USERS_FILE)
    count = len(users)
    await update.message.reply_text(f"ᴛᴏᴛᴀʟ ᴜɴɪǫᴜᴇ ᴜsᴇʀs ᴡʜᴏ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ: {count}")
    
# Download json files
@admin_only
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [POSTS_FILE, USERS_FILE, REQUESTS_FILE]
    for file in files:
        if os.path.exists(file):
            await update.message.reply_document(document=open(file, "rb"), filename=file)
        else:
            await update.message.reply_text(f"❌ ғɪʟᴇ {file} ɴᴏᴛ ғᴏᴜɴᴅ.", parse_mode="Markdown")

# Admin-only command: broadcast message to all users
@admin_only
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴍᴇ ᴛʜᴇ ᴍᴇssᴀɢʀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs.")
    return WAITING_FOR_BROADCAST

async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_data(USERS_FILE)

    message = update.message.reply_to_message or update.message
    reply_markup = message.reply_markup if message.reply_markup else None

    caption = message.caption or ""
    sent, failed = 0, 0

    for user_id in users:
        try:
            user_id = int(user_id)

            if message.photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=message.document.file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            elif message.video:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=message.video.file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            elif message.text:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message.text,
                    reply_markup=reply_markup
                )
            else:
                # Unhandled media type
                print(f"⚠️ᴜɴsᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ ᴛʏᴘᴇ ғᴏʀ ᴜsᴇʀ {user_id}")
                failed += 1
                continue

            sent += 1

        except Exception as e:
            print(f"❌ ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ᴛᴏ {user_id}: {e}")
            failed += 1

    await update.message.reply_text(f"✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ.\nsᴇɴᴛ: {sent}\nғᴀɪʟᴇᴅ: {failed}")
    return ConversationHandler.END

# Cancel the conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ᴏᴘᴇʀᴀᴛɪᴏɴ canceleᴅ.")
    return ConversationHandler.END

# unknown command replyer
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ʙᴀᴋᴀ! ᴜɴᴋɴᴏᴡɴ ᴄᴏᴍᴍᴀɴᴅ: ᴜsᴇ /start ᴛᴏ sᴇᴇ ᴀᴠᴀɪʟᴀʙʟᴇ commanᴅs.")
    
# --- Callback Query Handlers ---

# Handle inline button queries for about/help/back/close
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    close_button = [InlineKeyboardButton("❌ ᴄʟᴏsᴇ", callback_data="close")]

    if query.data == "about":
        keyboard = [
            [InlineKeyboardButton("ʙᴀᴄᴋ 🔙", callback_data="back"),
             InlineKeyboardButton("ʜᴇʟᴘ ⚙️", callback_data="help")],
            close_button
        ]
        await query.edit_message_media(
            media=InputMediaPhoto(ABOUT_URL, caption=ABOUT_CAPTION),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "help":
        keyboard = [
            [InlineKeyboardButton("ʙᴀᴄᴋ 🔙", callback_data="back"),
             InlineKeyboardButton("ᴀʙᴏᴜᴛ 📜", callback_data="about")],
            close_button
        ]
        await query.edit_message_media(
            media=InputMediaPhoto(HELP_URL, caption=HELP_CAPTION),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("ᴀʙᴏᴜᴛ 📜", callback_data="about"),
             InlineKeyboardButton("ʜᴇʟᴘ ⚙️", callback_data="help")],
            close_button
        ]
        await query.edit_message_media(
            media=InputMediaPhoto(START_URL, caption=START_CAPTION),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "close":
        await query.delete_message()
    elif query.data.startswith("viewpost:"):
        post_name = query.data.split(":", 1)[1]
        posts = load_data(POSTS_FILE)
        post = posts.get(post_name)
        if not post:
            await query.edit_message_text("❌ ᴘᴏsᴛ ɴᴏᴛ ғᴏᴜɴᴅ!")
            return
        media = post["media"]
        caption = post.get("caption", "")
        buttons = build_keyboard(post.get("buttons"))
        try:
            await query.message.delete()
        except Exception as e:
            print(f"❗ ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ: {e}")
        if media["type"] == "photo":
            await query.message.chat.send_photo(media["file_id"], caption=caption, reply_markup=buttons)
        elif media["type"] == "document":
            await query.message.chat.send_document(media["file_id"], caption=caption, reply_markup=buttons)

# @usernameofbot to search anime anyhere
async def inlinequery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()
    results = []

    if not query:
        return

    posts = load_data(POSTS_FILE)
    post_names = list(posts.keys())

    matches = difflib.get_close_matches(query, post_names, n=10, cutoff=0.4)
    matches += [name for name in post_names if query in name.lower()]
    matches = list(dict.fromkeys(matches))  # Remove duplicates

    for name in matches:
        post = posts[name]
        caption = post.get("caption", "No caption")
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=name,
                description=caption[:50] + "...",
                input_message_content=InputTextMessageContent(f"*{name}*\n\n{caption}", parse_mode="Markdown")
            )
        )

    await update.inline_query.answer(results[:20])  # Limit to 20 results

async def send_restart_notice(application):
    try:
        await application.bot.send_message(chat_id="@sister_leveling", text="♻️ ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ ʙʏ @LORD_SHADOW_SAMA")
    except Exception as e:
        print(f"❌ ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʀᴇsᴛᴀʀᴛ ᴍᴇssᴀɢᴇ: {e}")

# --- Flask for Render Uptime ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running!"

# --- Main Bot Function ---
def main():
    application = ApplicationBuilder().token(API_TOKEN).build()

    addpost_handler = ConversationHandler(
        entry_points=[CommandHandler("addpost", addpost)],
        states={WAITING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_post)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
        WAITING_FOR_BROADCAST: [
            MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_send)
        ]
    },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(addpost_handler)
    application.add_handler(broadcast_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("animelist", animelist))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("requestanime", requestanime))
    application.add_handler(CommandHandler("removereq", removereq))
    application.add_handler(CommandHandler("viewrequests", viewrequests))
    application.add_handler(CommandHandler("deletepost", deletepost))
    application.add_handler(CommandHandler("users", users))
    application.add_handler(CommandHandler("msguser", msguser))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(InlineQueryHandler(inlinequery))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.post_init = send_restart_notice
    application.run_polling(drop_pending_updates=True)

# --- Run Flask & Bot Together ---
if __name__ == "__main__":
    import threading
    # It's good practice to get the port from environment variables in Render
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port), daemon=True).start()
    main()
