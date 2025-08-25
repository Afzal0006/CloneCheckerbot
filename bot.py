from pyrogram import Client, filters
from pymongo import MongoClient
from datetime import datetime

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
    sender_tag = f"[{message.from_user.first_name}](tg://user?id={user_id})"

    # ---------------------------
    # 1) Save DEAL INFO
    # ---------------------------
    if text.startswith("DEAL INFO"):
        lines = text.splitlines()
        buyer_line = next((l for l in lines if l.startswith("BUYER")), "")
        seller_line = next((l for l in lines if l.startswith("SELLER")), "")

        buyer_username = buyer_line.split(":", 1)[1].strip() if ":" in buyer_line else None
        seller_username = seller_line.split(":", 1)[1].strip() if ":" in seller_line else None

        if buyer_username and seller_username:
            # Save Telegram IDs as well if available
            buyer_id = None
            seller_id = None

            if message.entities:
                for entity in message.entities:
                    if entity.type == "mention":
                        mention_text = message.text[entity.offset:entity.offset + entity.length]
                        if mention_text == buyer_username:
                            buyer_id = entity.user.id if hasattr(entity, 'user') else None
                        if mention_text == seller_username:
                            seller_id = entity.user.id if hasattr(entity, 'user') else None

            deal_data = {
                "chat_id": message.chat.id,
                "buyer": buyer_username,
                "seller": seller_username,
                "buyer_id": buyer_id,
                "seller_id": seller_id,
                "status": "active",
                "timestamp": datetime.utcnow()
            }
            deals_col.insert_one(deal_data)
            await client.send_message(
                message.chat.id,
                f"✅ New Deal Set!\nBuyer: {buyer_username}\nSeller: {seller_username}"
            )
        return

    # ---------------------------
    # 2) Release/Refund handling
    # ---------------------------
    if "release" in lowered or "refund" in lowered:
        # Admin skip
        member = await client.get_chat_member(message.chat.id, user_id)
        if member.status in ["administrator", "creator"]:
            return

        # Check active deals
        active_deals = list(deals_col.find({"chat_id": message.chat.id, "status": "active"}))
        if not active_deals:
            await client.send_message(
                message.chat.id,
                f"⚠ {sender_tag}, no active deal found! Please use the DEAL INFO form."
            )
            return

        allowed = False
        for deal in active_deals:
            # Allow if sender ID matches buyer_id or seller_id
            if user_id == deal.get("buyer_id") or user_id == deal.get("seller_id"):
                allowed = True
                await client.send_message(
                    message.chat.id,
                    f"✔ Allowed: {sender_tag} used `{lowered}` on deal between {deal['buyer']} & {deal['seller']}"
                )
                break

        if not allowed:
            await client.send_message(
                message.chat.id,
                f"⚠ {sender_tag}, only the buyer or seller of this deal can use release/refund!"
            )


print("🤖 Multi-user & multi-deal Escrow bot running…")
app.run()
