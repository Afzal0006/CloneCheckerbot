from pyrogram import Client, filters

# ===== CONFIG =====
API_ID = 24597778
API_HASH = "0b34ead62566cc7b072c0cf6b86b716e"
BOT_TOKEN = "6470654669:AAGdIa0b0As_XmgnT0OD2yZa1Otpos2f3YM"

# ===== DEAL INFO =====
BUYER = "@buyer_username"   # <-- Replace with real username
SELLER = "@seller_username" # <-- Replace with real username
DEAL_AMOUNT = "10 Rs"
TIME_LIMIT = "24 hours"     # <-- Example time

# Bot client
app = Client(
    "escrow_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Send deal info when bot starts (optional, can also trigger with /deal command)
@app.on_message(filters.command("deal") & filters.group)
def deal_info(client, message):
    client.send_message(
        message.chat.id,
        f"📜 DEAL INFO:\n\n"
        f"🤝 BUYER: {BUYER}\n"
        f"🤝 SELLER: {SELLER}\n"
        f"💰 DEAL AMOUNT: {DEAL_AMOUNT}\n"
        f"⏳ TIME TO COMPLETE DEAL: {TIME_LIMIT}\n\n"
        f"⚠️ Only {BUYER} and {SELLER} can type 'release' or 'refund'."
    )

# Monitor messages in group
@app.on_message(filters.group & filters.text)
def monitor_messages(client, message):
    text = message.text.lower()
    sender_username = f"@{message.from_user.username}" if message.from_user.username else ""

    if "release" in text or "refund" in text:
        if sender_username not in [BUYER, SELLER]:
            try:
                # Delete the message
                client.delete_messages(message.chat.id, message.id)

                # Kick the interfering user
                client.kick_chat_member(message.chat.id, message.from_user.id)

                # Warn the group
                client.send_message(
                    message.chat.id,
                    f"🚫 {sender_username} tried to interfere with the deal and was removed!"
                )
                print(f"❌ Kicked user: {sender_username}")
            except Exception as e:
                print(f"⚠️ Error kicking {sender_username}: {e}")
        else:
            print(f"✅ Allowed user {sender_username} used: {text}")

print("🤖 Escrow bot is running…")
app.run()
