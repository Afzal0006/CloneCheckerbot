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

    # 1) Agar new DEAL INFO form hai → extract buyer & seller
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
                "created_by": message.from_user.id,
                "status": "active"
            }
            deals_col.insert_one(deal_data)

            sent_msg = await client.send_message(
                message.chat.id,
                f"✅ New Deal Set!\nBuyer: {buyer}\nSeller: {seller}"
            )
            await sent_msg.delete()

        return

    # 2) Agar koi 'release' ya 'refund' bole
    lowered = text.lower()
    if "release" in lowered or "refund" in lowered:
        user_id = message.from_user.id
        sender_tag = f"[{message.from_user.first_name}](tg://user?id={user_id})"
        current_deal = deals_col.find_one({"chat_id": message.chat.id}, sort=[("_id", -1)])

        # Agar koi active deal hi nahi hai
        if not current_deal:
            await client.send_message(
                message.chat.id,
                "⚠ Please tag on form and write `release` or `refund`"
            )
            return

        buyer = current_deal["buyer"]
        seller = current_deal["seller"]

        # Agar buyer/seller hai
        if f"@{message.from_user.username}" in [buyer, seller]:
            await client.send_message(
                message.chat.id,
                f"✔ Allowed: {sender_tag} used `{lowered}` on deal between {buyer} & {seller}"
            )
            return

        # Agar admin hai to skip
        member = await client.get_chat_member(message.chat.id, user_id)
        if member.status in ["administrator", "creator"]:
            return

        # Warna 3rd person → ban
        try:
            await client.ban_chat_member(message.chat.id, user_id)
            await client.send_message(
                message.chat.id,
                f"🚫 {sender_tag} tried to interfere with the deal and was banned!"
            )
        except Exception as e:
            await client.send_message(message.chat.id, f"⚠ Error banning user: {e}")


print("🤖 Escrow bot with tagging + ban is running…")
app.run()
