from pyrogram import Client, filters

# ===== CONFIG =====
BOT_TOKEN = "8350094964:AAE-ebwWQBx_YWnW_stEqcxiKKVVx8SZaAw"  # Replace with your bot token

# Buyer & Seller usernames (with @)
BUYER = "@buyer_username"
SELLER = "@seller_username"

app = Client("escrow_bot", bot_token=BOT_TOKEN)

@app.on_message(filters.group)
def monitor_messages(client, message):
    if not message.text:
        return

    text = message.text.lower()

    # Check for restricted words
    if "release" in text or "refund" in text:
        sender_username = f"@{message.from_user.username}" if message.from_user.username else ""
        
        # Kick if sender is not buyer or seller
        if sender_username not in [BUYER, SELLER]:
            try:
                client.kick_chat_member(message.chat.id, message.from_user.id)
                # Optional: send warning message to group
                client.send_message(
                    message.chat.id,
                    f"{sender_username} tried to interfere with the deal and was removed!"
                )
                print(f"Kicked user: {sender_username}")
            except Exception as e:
                print(f"Error kicking {sender_username}: {e}")

print("🤖 Escrow bot is running…")
app.run()
