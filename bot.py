from pyrogram import Client, filters

# ==== CONFIG ====
API_ID = 24597778
API_HASH = "0b34ead62566cc7b072c0cf6b86b716e"
BOT_TOKEN = "6470654669:AAGdIa0b0As_XmgnT0OD2yZa1Otpos2f3YM"

# Global deal info (latest form ka data yahan store hoga)
current_buyer = None
current_seller = None

app = Client("escrow_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.group)
def handle_group_messages(client, message):
    global current_buyer, current_seller

    if not message.text:
        return

    text = message.text.strip()

    # 1) Agar new DEAL INFO form hai → extract buyer & seller
    if text.startswith("DEAL INFO"):
        lines = text.splitlines()
        buyer_line = next((l for l in lines if l.startswith("BUYER")), "")
        seller_line = next((l for l in lines if l.startswith("SELLER")), "")

        if ":" in buyer_line:
            current_buyer = buyer_line.split(":")[1].strip()
        if ":" in seller_line:
            current_seller = seller_line.split(":")[1].strip()

        client.send_message(
            message.chat.id,
            f"✅ New Deal Set!\nBuyer: {current_buyer}\nSeller: {current_seller}"
        )
        return

    # 2) Agar koi 'release' ya 'refund' bole
    lowered = text.lower()
    if "release" in lowered or "refund" in lowered:
        sender_username = f"@{message.from_user.username}" if message.from_user.username else ""

        # Check: agar wo current buyer ya seller hai → allowed
        if sender_username in [current_buyer, current_seller]:
            print(f"✔ Allowed: {sender_username} used {lowered}")
            return

        # Agar admin hai to skip
        member = client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in ["administrator", "creator"]:
            print(f"⚠ Admin {sender_username} used keyword, skipping ban.")
            return

        # Otherwise ban user
        try:
            client.ban_chat_member(message.chat.id, message.from_user.id)
            client.send_message(
                message.chat.id,
                f"🚫 {sender_username} tried to interfere with the deal and was banned!"
            )
            print(f"❌ Banned: {sender_username}")
        except Exception as e:
            print(f"Error banning {sender_username}: {e}")


print("🤖 Escrow bot is running…")
app.run()
