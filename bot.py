from pyrogram import Client, filters
from pymongo import MongoClient
from datetime import datetime, timedelta

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

    # ---------------------------
    # 1) Save DEAL INFO
    # ---------------------------
    if text.startswith("DEAL INFO"):
        lines = text.splitlines()
        buyer_line = next((l for l in lines if l.startswith("BUYER")), "")
        seller_line = next((l for l in lines if l.startswith("SELLER")), "")

        buyer = buyer_line.split(":", 1)[1].strip() if ":" in buyer_line else None
        seller = seller_line.split(":", 1)[1].strip() if ":" in seller_line else None

        if buyer and seller:
            deal_data = {
                "chat_id": message.chat.id,
                "buyer": buyer,
                "seller": seller,
                "buyer_id": None,  # optional
                "seller_id": None,
                "status": "active",
                "timestamp": datetime.utcnow()
            }
            deals_col.insert_one(deal_data)
            await client.send_message(
                message.chat.id,
                f"✅ New Deal Set!\nBuyer: {buyer}\nSeller: {seller}"
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

        # Find all active deals in this chat
        active_deals = list(deals_col.find({"chat_id": message.chat.id, "status": "active"}))
        if not active_deals:
            await client.send_message(
                message.chat.id,
                f"⚠ {sender_tag}, no active deal found! Please use the DEAL INFO form."
            )
            return

        # Check if user is buyer/seller in any deal
        allowed = False
        for deal in active_deals:
            if username in [deal["buyer"], deal["seller"]]:
                allowed = True
                await client.send_message(
                    message.chat.id,
                    f"✔ Allowed: {sender_tag} used `{lowered}` on deal between {deal['buyer']} & {deal['seller']}"
                )
                break

        if not allowed:
            # Mute interfering user for 1 hour
            try:
                until_time = datetime.utcnow() + timedelta(hours=1)
                await client.restrict_chat_member(
                    message.chat.id,
                    user_id,
                    permissions={"can_send_messages": False},
                    until_date=until_time
                )
                await client.send_message(
                    message.chat.id,
                    f"🚫 {sender_tag} tried to interfere with the deal and has been muted for 1 hour!"
                )
            except Exception as e:
                await client.send_message(message.chat.id, f"⚠ Error muting user: {e}")


print("🤖 Multi-deal Escrow bot running…")
app.run()
