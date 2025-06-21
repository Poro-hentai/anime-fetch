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
    ContextTypes   # ✅ This line added
)
from telegram import InlineQueryResultArticle, InputTextMessageContent
from flask import Flask
import uuid
import threading

import json
import os

# Configuration
API_TOKEN = "8006836827:AAERFD1tDpBDJhvKm_AHy20uSAzZdoRwbZc"  # Replace with your bot's API token
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
    "✨ Welcome to Anime Garden! ✨\n\n"
    "Discover & Request your favorite Anime.\n"
    "Use the buttons below to explore more!\n\n"
    "Commands:\n"
    "/addpost - Admin only: Save an anime post with media, caption & buttons\n"
    "/animelist - List saved anime posts\n"
    "/search <name> - Search saved anime by name\n"
    "/requestanime <name> - Request an anime (will be forwarded to group)\n"
    "/viewrequests - View all anime requests\n"
    "/users - View how many users have started the bot (admin only)\n"
    "/broadcast - Broadcast a message to all users (admin only)\n"
    "/cancel - Cancel current operation\n"
)

ABOUT_CAPTION = (
    "📜 About Us\n\n"
    "Anime Garden is your one-stop destination for discovering and requesting Anime!"
)

HELP_CAPTION = (
    "⚙️ Help\n\n"
    "Commands:\n"
    "/addpost - Reply to a message containing anime media, caption & buttons to save it\n"
    "/animelist - List all saved anime posts\n"
    "/search <term> - Search anime posts by name\n"
    "/requestanime <name> - Request an anime (your request will be sent to the group)\n"
    "/viewrequests - View all user requests\n"
    "/users - View how many users have started the bot (admin only)\n"
    "/broadcast - Broadcast a message to all users (admin only)\n"
    "/cancel - Cancel any ongoing action\n\n"
    "Buttons in saved posts will be preserved and shown when displaying posts."
)

# States for ConversationHandler
WAITING_FOR_NAME = 0
WAITING_FOR_BROADCAST = 1

# Utility functions
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

#@usernameofbot to search anime anyhere
async def inlinequery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()
    results = []

    if not query:
        return

    posts = load_data(POSTS_FILE)

    for name, post in posts.items():
        if query in name.lower():
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

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_user(update)
    keyboard = [
        [
            InlineKeyboardButton("About 📜", callback_data="about"),
            InlineKeyboardButton("Help ⚙️", callback_data="help"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="close")],
    ]
    await update.message.reply_photo(
        photo=START_URL,
        caption=START_CAPTION,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# Admin-only decorator
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_ids = [5759232282]  # Put your Telegram user ID(s) here (int)
        user_id = update.effective_user.id
        if user_id not in admin_ids:
            await update.message.reply_text("You are not authorized to use this command.")
            return ConversationHandler.END
        return await func(update, context)
    return wrapper

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

# addpost command starts here
@admin_only
async def addpost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a message containing the anime details to save.")
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
        await update.message.reply_text("No supported media found (photo/document).")
        return ConversationHandler.END

    caption = reply_msg.caption or ""

    buttons = extract_buttons(reply_msg)

    context.user_data["media"] = {"file_id": media_file_id, "type": media_type}
    context.user_data["caption"] = caption
    context.user_data["buttons"] = buttons

    await update.message.reply_text("What name should I save this post as? Reply with the name.")
    return WAITING_FOR_NAME

# Save post with media, caption, buttons
async def save_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post_name = update.message.text.strip()
    if not post_name:
        await update.message.reply_text("Invalid name. Please try again.")
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

    await update.message.reply_text(f"Post saved as '{post_name}'!")
    return ConversationHandler.END

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

#show anime list
async def animelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    posts = load_data(POSTS_FILE)
    if not posts:
        await update.message.reply_text("❌ No anime posts saved yet!")
        return

    sorted_posts = sorted(posts.keys(), key=lambda x: x.lower())
    grouped = {}

    for name in sorted_posts:
        key = name[0].upper()
        grouped.setdefault(key, []).append(name)

    text = "📚 *Anime Library* - Sorted A–Z\n\n"
    for letter in sorted(grouped):
        text += f"🔠 *{letter}*\n"
        for title in grouped[letter]:
            text += f"• `{title}`\n"
        text += "\n"

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )



# Search posts by name
# Updated Search 
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).lower()
    if not query:
        await update.message.reply_text("Please provide a search term.")
        return

    posts = load_data(POSTS_FILE)
    results = [name for name in posts if query in name.lower()]

    if not results:
        await update.message.reply_text("No matches found!")
        return

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"viewpost:{name}")] for name in results
    ]
    await update.message.reply_text(
        "Search results:\nClick a button to view the post.",
        reply_markup=InlineKeyboardMarkup(keyboard)
        
    )


# Request anime command: save multiple requests as a list, forward to group
async def requestanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request_text = " ".join(context.args).strip()
    if not request_text:
        await update.message.reply_text("Please specify the anime you want to request.")
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

    await update.message.reply_text(f"Your request for '{request_text}' has been recorded!")

    try:
        await context.bot.send_message(
            chat_id=GROUP_CHAT,
            text=f"📢 New Anime Request from @{user_name}:\n{request_text}"
        )
    except Exception as e:
        print(f"Failed to send request to group: {e}")

        
#send msg to user
@admin_only
async def msguser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /msguser <user_id or @username> <your message>")
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
            await update.message.reply_text(f"❌ Username '{user_ref}' not found in user database.")
            return
        user_id = int(found_id)
    else:
        try:
            user_id = int(user_ref)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or username.")
            return

    try:
        await context.bot.send_message(chat_id=user_id, text=msg_text)
        await update.message.reply_text(f"✅ Message sent to `{user_id}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send message: {e}")

#deletepost
@admin_only
async def deletepost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /deletepost <post name>")
        return

    post_name = " ".join(context.args).strip()
    posts = load_data(POSTS_FILE)

    if post_name not in posts:
        await update.message.reply_text(f"No post found with name '{post_name}'.")
        return

    del posts[post_name]
    save_data(POSTS_FILE, posts)
    await update.message.reply_text(f"✅ Post '{post_name}' has been deleted.")


# View all anime requests
@admin_only
async def viewrequests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    requests = load_data(REQUESTS_FILE)
    if not requests:
        await update.message.reply_text("No requests found!")
        return

    response = "Anime Requests:\n\n"
    for req in requests:
        user_display = f"@{req['username']}" if req['username'] else "Unknown"
        response += f"{user_display}: {req['anime']}\n"
    await update.message.reply_text(response)

# Handle inline button queries for about/help/back/close
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    close_button = [InlineKeyboardButton("❌ Close", callback_data="close")]

    if query.data == "about":
        keyboard = [
            [InlineKeyboardButton("Back 🔙", callback_data="back"),
             InlineKeyboardButton("Help ⚙️", callback_data="help")],
            close_button
        ]
        await query.edit_message_media(
            media=InputMediaPhoto(ABOUT_URL, caption=ABOUT_CAPTION),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "help":
        keyboard = [
            [InlineKeyboardButton("Back 🔙", callback_data="back"),
             InlineKeyboardButton("About 📜", callback_data="about")],
            close_button
        ]
        await query.edit_message_media(
            media=InputMediaPhoto(HELP_URL, caption=HELP_CAPTION),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("About 📜", callback_data="about"),
             InlineKeyboardButton("Help ⚙️", callback_data="help")],
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
            await query.edit_message_text("Post not found!")
            return

        media = post["media"]
        caption = post.get("caption", "")
        buttons = build_keyboard(post.get("buttons"))

        # Delete the message with button (search result)
        try:
            await query.message.delete()
        except:
            pass  # Ignore if delete fails

        # Send the post as new message
        if media["type"] == "photo":
            await query.message.chat.send_photo(media["file_id"], caption=caption, reply_markup=buttons)
        elif media["type"] == "document":
            await query.message.chat.send_document(media["file_id"], caption=caption, reply_markup=buttons)



# Cancel the conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

# Admin-only command: show how many users have started the bot
@admin_only
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_data(USERS_FILE)
    count = len(users)
    await update.message.reply_text(f"Total unique users who started the bot: {count}")
    #Download json
@admin_only
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = [POSTS_FILE, USERS_FILE, REQUESTS_FILE]
    for file in files:
        if os.path.exists(file):
            await update.message.reply_document(document=open(file, "rb"), filename=file)
        else:
            await update.message.reply_text(f"❌ File `{file}` not found.", parse_mode="Markdown")


# Admin-only command: broadcast message to all users
@admin_only
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send me the message you want to broadcast to all users.")
    return WAITING_FOR_BROADCAST

async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_data(USERS_FILE)

    message = update.message.reply_to_message or update.message
    reply_markup = message.reply_markup if message.reply_markup else None


    sent, failed = 0, 0

    for user_id in users:
        try:
            if message.photo:
                await context.bot.send_photo(
                    chat_id=int(user_id),
                    photo=message.photo[-1].file_id,
                    caption=message.caption or "",
                    reply_markup=reply_markup
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=int(user_id),
                    document=message.document.file_id,
                    caption=message.caption or "",
                   reply_markup=reply_markup
                )
            else:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=message.text or "",
                    reply_markup=reply_markup
                )
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"✅ Broadcast complete.\nSent: {sent}\nFailed: {failed}")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(API_TOKEN).build()

    addpost_handler = ConversationHandler(
        entry_points=[CommandHandler("addpost", addpost)],
        states={
            WAITING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_post)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            WAITING_FOR_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(addpost_handler)
    application.add_handler(broadcast_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("animelist", animelist))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("requestanime", requestanime))
    application.add_handler(CommandHandler("viewrequests", viewrequests))
    application.add_handler(CommandHandler("deletepost", deletepost))
    application.add_handler(CommandHandler("users", users))
    application.add_handler(CommandHandler("msguser", msguser))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(InlineQueryHandler(inlinequery))

# === Flask App for Render Uptime ===
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# === Main Entry Point ===
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main()
