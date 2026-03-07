import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# Discordトークンを環境変数から取得
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN is None:
    print("Error: DISCORD_TOKEN が設定されていません")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True  # 必要に応じてオン
bot = commands.Bot(command_prefix="!", intents=intents)

# データファイル
DATA_FILE = "reviews.json"
STAFF_FILE = "staff.json"

# --- データ操作関数 ---
def load_reviews():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reviews(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_staff():
    if not os.path.exists(STAFF_FILE):
        return []
    with open(STAFF_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_staff(data):
    with open(STAFF_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- Bot イベント ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} がログインしました")

# --- スラッシュコマンド ---
@bot.tree.command(name="staff_add", description="スタッフ登録")
@app_commands.describe(user="登録するスタッフ")
async def staff_add(interaction: discord.Interaction, user: discord.Member):
    staff = load_staff()
    if str(user.id) in staff:
        await interaction.response.send_message("すでに登録されています")
        return
    staff.append(str(user.id))
    save_staff(staff)
    await interaction.response.send_message(f"{user.mention} をスタッフ登録しました")

@bot.tree.command(name="review", description="スタッフを評価")
@app_commands.describe(user="スタッフ", rating="評価(1〜5)", comment="コメント")
async def review(interaction: discord.Interaction, user: discord.Member, rating: int, comment: str):
    if rating < 1 or rating > 5:
        await interaction.response.send_message("評価は1〜5です")
        return
    if interaction.user.id == user.id:
        await interaction.response.send_message("自分を評価できません")
        return
    staff = load_staff()
    if str(user.id) not in staff:
        await interaction.response.send_message("このユーザーはスタッフではありません")
        return
    data = load_reviews()
    staff_id = str(user.id)
    if staff_id not in data:
        data[staff_id] = []
    data[staff_id].append({
        "stars": rating,
        "comment": comment,
        "user": str(interaction.user.id)
    })
    save_reviews(data)
    await interaction.response.send_message("レビューを送信しました")

@bot.tree.command(name="average", description="平均評価")
@app_commands.describe(staff="スタッフ")
async def average(interaction: discord.Interaction, staff: discord.Member):
    data = load_reviews()
    staff_id = str(staff.id)
    if staff_id not in data:
        await interaction.response.send_message("評価がありません")
        return
    ratings = [r["stars"] for r in data[staff_id]]
    avg = sum(ratings) / len(ratings)
    await interaction.response.send_message(f"{staff.mention}\n平均⭐ {avg:.2f}\nレビュー数 {len(ratings)}")

@bot.tree.command(name="comments", description="レビューを見る")
@app_commands.describe(staff="スタッフ")
async def comments(interaction: discord.Interaction, staff: discord.Member):
    data = load_reviews()
    staff_id = str(staff.id)
    if staff_id not in data:
        await interaction.response.send_message("レビューがありません")
        return
    text = f"{staff.mention} のレビュー\n\n"
    for r in data[staff_id][-10:]:
        text += f"⭐{r['stars']} - {r['comment']}\n"
    await interaction.response.send_message(text)

@bot.tree.command(name="ranking", description="スタッフランキング")
async def ranking(interaction: discord.Interaction):
    data = load_reviews()
    ranking_list = []
    for staff_id, reviews in data.items():
        if len(reviews) < 5:
            continue
        ratings = [r["stars"] for r in reviews]
        avg = sum(ratings) / len(ratings)
        ranking_list.append((staff_id, avg, len(reviews)))
    if not ranking_list:
        await interaction.response.send_message("レビュー5件以上のスタッフがいません")
        return
    ranking_list.sort(key=lambda x: x[1], reverse=True)
    text = "🏆スタッフランキング（レビュー5件以上）\n\n"
    for i, (staff_id, avg, count) in enumerate(ranking_list[:10], start=1):
        text += f"{i}位 <@{staff_id}> ⭐{avg:.2f} ({count}件)\n"
    await interaction.response.send_message(text)

@bot.tree.command(name="profile", description="スタッフプロフィール")
@app_commands.describe(staff="スタッフ")
async def profile(interaction: discord.Interaction, staff: discord.Member):
    data = load_reviews()
    staff_id = str(staff.id)
    if staff_id not in data:
        await interaction.response.send_message("レビューがありません")
        return
    reviews = data[staff_id]
    ratings = [r["stars"] for r in reviews]
    avg = sum(ratings) / len(ratings)
    star_count = {i: ratings.count(i) for i in range(1, 6)}
    text = f"""
📊 スタッフプロフィール
スタッフ : {staff.mention}

平均評価 ⭐{avg:.2f}
レビュー数 {len(reviews)}

⭐5 : {star_count[5]}
⭐4 : {star_count[4]}
⭐3 : {star_count[3]}
⭐2 : {star_count[2]}
⭐1 : {star_count[1]}
"""
    await interaction.response.send_message(text)

# --- Bot 起動 ---
bot.run(TOKEN)
