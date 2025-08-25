from pyrogram import Client, filters
from pymongo import MongoClient

# ==== CONFIG ====
API_ID = 24597778
API_HASH = "0b34ead62566cc7b072c0cf6b86b716e"
BOT_TOKEN = "6470654669:AAGdIa0b0As_XmgnT0OD2yZa1Otpos2f3YM"

# ==== MongoDB Atlas ====
MONGO_URI = "mongodb+srv://afzal99550:afzal99550@cluster0.aqmbh9q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["escrow_db"]
deals_col = db["deals"]

app = Client("escrow_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.group)
async def handle_group_messages(client, message):
    if not message.text:
        return

    text = message.text.strip()
    lowered = text.lower()
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else None
    sender_tag = f"[{message.from_user.first_name}](tg://user?id={user_id})"

    # 1) New DEAL INFO form
    if text.startswith("DEAL INFO"):
        lines = text.splitlines()
        buyer_line = next((l for l in lines if l.startswith("BUYER")), "")
        seller_line = next((l for l in lines if l.startswith("SELLER")), "")
        amount_line = next((l for l in lines if l.startswith("DEAL AMOUNT")), "")
        time_line = next((l for l in lines if l.startswith("TIME TO COMPLETE DEAL")), "")

        buyer = buyer_line.split(":", 1)[1].strip() if ":" in buyer_line else None
        seller = seller_line.split(":", 1)[1].strip() if ":" in seller_line else None
        amount = amount_line.split(":", 1)[1].strip() if ":" in amount_line else None
        deadline = time_line.split(":", 1)[1].strip() if ":" in time_line else None

        if buyer and seller:
            deal_data = {
                "chat_id": message.chat.id,
                "buyer": buyer,
                "seller": seller,
                "amount": amount,
                "deadline": deadline,
                "created_by": user_id,
                "status": "active"
            }
            deals_col.insert_one(deal_data)
            await client.send_message(
                message.chat.id,
                f"✅ New Deal Set!\nBuyer: {buyer}\nSeller: {seller}"
            )
        return

    # 2) Someone types 'release' or 'refund'
    if "release" in lowered or "refund" in lowered:
        current_deal = deals_col.find_one({"chat_id": message.chat.id}, sort=[("_id", -1)])
        if not current_deal:
            await client.send_message(
                message.chat.id,
                f"⚠ {sender_tag}, please tag on the DEAL INFO form before using `{lowered}`"
            )
            return

        buyer = current_deal["buyer"]
        seller = current_deal["seller"]

        # Admin exemption
        member = await client.get_chat_member(message.chat.id, user_id)
        if member.status in ["administrator", "creator"]:
            return

        # Check if message **mentions/tagged username** from the form
        tagged_users = []
        if message.entities:
            for e in message.entities:
                if hasattr(e, "user") and e.user:
                    tagged_users.append(f"@{e.user.username}" if e.user.username else None)

        # Allowed only if tagged username matches buyer/seller
        is_allowed = False
        if username in [buyer, seller]:
            # Buyer/seller khud type kar raha ho → check if tag present
            if (buyer in text) or (seller in text):
                is_allowed = True
        else:
            # Other users → check if tag matches buyer/seller
            if any(u in [buyer, seller] for u in tagged_users):
                is_allowed = True

        if is_allowed:
            await client.send_message(
                message.chat.id,
                f"✔ Allowed: {sender_tag} used `{lowered}` on deal between {buyer} & {seller}"
            )
        else:
            # Warn user first if they typed without tagging
            if username in [buyer, seller]:
                await client.send_message(
                    message.chat.id,
                    f"⚠ {sender_tag}, please tag yourself on the DEAL INFO form before using `{lowered}`"
                )
            else:
                # Ban unknown/interfering user
                try:
                    await client.ban_chat_member(message.chat.id, user_id)
                    await client.send_message(
                        message.chat.id,
                        f"🚫 {sender_tag} tried to interfere with the deal and was banned!"
                    )
                except Exception as e:
                    await client.send_message(message.chat.id, f"⚠ Error banning user: {e}")


print("🤖 Escrow bot with strict form tag verification is running…")
app.run()
