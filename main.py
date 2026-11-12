import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
import json


class AcceptSuggestView(discord.ui.View):
    candidate: str

    def __init__(self, candidate: str):
        super().__init__(timeout=60)
        self.candidate = candidate

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        candidates.remove(self.candidate)
        themes.append(self.candidate)
        await interaction.response.defer()
        await interaction.followup.delete_message(interaction.message.id)
        save_stuff()

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        candidates.remove(self.candidate)
        blacklist.append(self.candidate)
        await interaction.response.defer()
        await interaction.followup.delete_message(interaction.message.id)
        save_stuff()
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.gray)
    async def skip_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.followup.delete_message(interaction.message.id)


    


themes = list[str]()
candidates = list[str]()
blacklist = list[str]()
target_channel = int()
channel_name = "<unset_channel>"

Path("cache.json").touch(exist_ok=True)


def save_stuff():
    global themes, candidates, blacklist, target_channel
    tmp = "cache.json.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"themes": themes, "candidates": candidates, "target_channel": target_channel,
                   "blacklist": blacklist}, f, ensure_ascii=False)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, "cache.json")

try:
    with open("cache.json", "r") as file:
        data = json.loads(file.read())
        themes = data["themes"]
        candidates = data["candidates"]
        blacklist = data["blacklist"]
        target_channel = data["target_channel"]
except (json.JSONDecodeError, KeyError):
    themes = []
    candidates = []
    blacklist = []
    target_channel = 0



load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)


async def load_channel_messages():
    global channel_name

    if target_channel == 0:
        channel_name = "<unset_channel>"
        return []

    channel = bot.get_channel(target_channel)
    if channel is None:
        channel_name = str(target_channel)
        return []

    channel_name = channel.name
    
    async for msg in channel.history(limit=500):
        theme = msg.content
        if(theme == ""): continue
        if(len(theme) > 100): continue
        if(theme in candidates or
           theme in themes or
           theme in blacklist): continue
        candidates.append(theme)
        print(theme)

    save_stuff()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    await load_channel_messages()

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command):
    save_stuff()

@bot.event
async def on_message(message: discord.Message):
    # Ignore the bot's own messages
    if message.author == bot.user:
        return

    # Only react in the target channel
    if message.channel.id != target_channel:
        return

    theme = message.content
    if not theme or len(theme) > 100:
        return
    if theme in candidates or theme in themes or theme in blacklist:
        return

    candidates.append(theme)
    save_stuff()
    await bot.process_commands(message)
    
# @bot.tree.command(name="suggest", description="Zaproponuj temat dla nastepnego Jam'u.\nMax 100 liter.")
# async def suggest(interaction:discord.Interaction, temat: str):
#     if(temat in themes or temat in candidates):
#         await interaction.response.send_message(f"Nie udalo sie dodac temat: ``{temat}`` juz zaproponowany, lub czeka na walidacje. Sprawdz pule za pomoca ``/list``", delete_after=30, ephemeral=True)
#         return

#     if(temat in blacklist):
#         await interaction.response.send_message(f"Nie udalo sie dodac temat: Temat ``{temat}`` zostal zablokowany prez administratora. Skontaktuj sie z administracja jezeli uwazasz ze temat zostal zablokowany niesprawiedliwie", delete_after=30, ephemeral=True)
#         return

#     if(len(temat)>100):
#         await interaction.response.send_message(f"Nie udalo sie dodac temat: Temat jest zadlugi. (Max 100 znakow)", delete_after=30, ephemeral=True)
#         return 

#     candidates.append(temat)
#     await interaction.response.send_message(f"Twoj temat oczekuje na validacje. Puzniej zobaczysz go za pomoca ``/list``", delete_after=30, ephemeral=True)

@bot.tree.command(name="help", description="Wyswietla pomoc i kanal do wysylania tematow.")
async def help_command(interaction: discord.Interaction):
    global channel_name
    resolved_channel = bot.get_channel(target_channel)
    if target_channel == 0:
        channel_name = "<unset_channel>"
    elif resolved_channel is not None:
        channel_name = resolved_channel.name

    channel_mention = f"<#{target_channel}>" if target_channel != 0 else "`<unset_channel>`"
    await interaction.response.send_message(
        f"""
## Pomoc
- `/list` - Wyswietla wszystkie zatwierdzone tematy w puli.
- `/help` - Wyswietla te wiadomosc pomocy.

**Jak zaproponowac temat:**
Wyslij swoj temat jako zwykla wiadomosc na kanal {channel_mention} (`#{channel_name}`).
Tematy moga miec maksymalnie 100 znakow.
""",
        ephemeral=True,
        delete_after=120,
    )


@bot.tree.command(name="list", description="Wyswietla wszystkie tematy w pule.")
async def list(interaction: discord.Interaction):
    global channel_name
    resolved_channel = bot.get_channel(target_channel)
    if target_channel == 0:
        channel_name = "<unset_channel>"
    elif resolved_channel is not None:
        channel_name = resolved_channel.name

    if len(themes) <= 0:
        await interaction.response.send_message(f"Jeszcze niema zadnych temator. Badz pierwszym, zaproponuj temat piszac do kanalu #{channel_name}", ephemeral=True)
        return
    themes_msg = ""
    i=0
    for theme in themes:
       i+=1
       themes_msg += f"{i}) {theme}\n"
    await interaction.response.send_message(f"""
## Pula tematow: 
```
{themes_msg}
```

Zaproponuj swoj temat piszac do kanalu #{channel_name}
""", delete_after=120, ephemeral=True)
    
@bot.tree.command(name="admin-help", description="Wyswietla pomoc dla administratorow.")
@discord.app_commands.default_permissions(ban_members=True)
async def admin_help(interaction: discord.Interaction):
    if (not interaction.user.guild_permissions.ban_members):
        await interaction.response.send_message("Nie masz uprawnien by korzystac z tej komendy.", delete_after=30, ephemeral=True)
        return
    await interaction.response.send_message(
        f"""
## Pomoc dla administratorow
- `/remove <nr_tematu>` - Usuwa temat z puli.
- `/validate` - Przegladaj propozycje tematow i zatwierdzaj lub odrzucaj.
- `/set_target_channel <kanal>` - Ustawia kanal docelowy dla tematow.
- `/force_load_channel` - Wczytuje wiadomosci z kanalu docelowego. (Odbywa sie automatycznie)
- `/admin-help` - Wyswietla te wiadomosc pomocy.

Te komendy dostepne sa tylko dla administratorow.
""",
        ephemeral=True,
        delete_after=120,
    )


@bot.tree.command(name="remove", description="Usun temat z puli")
@discord.app_commands.default_permissions(ban_members=True)
async def remove(interaction: discord.Interaction, nr_tematu: int):
    if (not interaction.user.guild_permissions.ban_members):
        await interaction.response.send_message("Nie masz uprawnien by usuwac tematy z puli.", delete_after=30, ephemeral=True)
        return

    if nr_tematu not in range(1, len(themes)+1):
        await interaction.response.send_message(f"Tematu z numerem {nr_tematu} nie istnieje. Sprawdz pisownie lub zobac liste tematow za pomoca ``/list``", delete_after=30, ephemeral=True)
        return

    themes.remove(themes[nr_tematu-1])
    await interaction.response.send_message(f"Temat usuniento z puli.", delete_after=30, ephemeral=True)


@bot.tree.command(name="validate", description="Cycle tru list of candidates and hand pick valid ones.")
@discord.app_commands.default_permissions(ban_members=True)
async def validate(interaction: discord.Interaction):
    if (not interaction.user.guild_permissions.ban_members):
        await interaction.response.send_message("Nie masz uprawnien by usuwac tematy z puli.", delete_after=30, ephemeral=True)
        return

    await interaction.response.send_message("List of current candidates:", ephemeral=True)
    for candidate in candidates:
        if candidate in themes:
            candidates.remove(candidate)
            continue
        await interaction.followup.send(f"``{candidate}``", ephemeral=True, view=AcceptSuggestView(candidate=candidate))

@bot.tree.command(name="set_target_channel", description="blablablahhhh bibibuu")
@discord.app_commands.default_permissions(ban_members=True)
async def set_target_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if (not interaction.user.guild_permissions.ban_members):
        await interaction.response.send_message("Nie masz uprawnien by ustawiac kanal docelowy.", delete_after=30, ephemeral=True)
        return

    global target_channel, channel_name
    target_channel = channel.id
    resolved_channel = bot.get_channel(target_channel)
    if target_channel == 0:
        channel_name = "<unset_channel>"
    elif resolved_channel is not None:
        channel_name = resolved_channel.name
    else:
        channel_name = getattr(channel, "name", str(target_channel))
    await interaction.response.send_message(f"Set target channel to ``{target_channel}``. Run force_load_channel or restart the bot to load its content", ephemeral=True, delete_after=30)

@bot.tree.command(name="force_load_channel", description="I am gay af")
@discord.app_commands.default_permissions(ban_members=True)
async def force_load_channel(interaction: discord.Interaction):
    if (not interaction.user.guild_permissions.ban_members):
        await interaction.response.send_message("Nie masz uprawnien by wczytywac kanal.", delete_after=30, ephemeral=True)
        return

    await load_channel_messages()
    await interaction.response.send_message("Loaded. See console for logs.", ephemeral=True, delete_after=30)

try:
    bot.run(TOKEN)
finally:
    save_stuff()