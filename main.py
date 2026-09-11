import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path
import json


themes = list[str]()
candidates = list[str]()
qualified_user_ids = list[int]()

try:
    Path("cache.json").touch(exist_ok=True)
    with open("cache.json", "r") as file:
        data = json.loads(file.read())
        themes = data["themes"]
        candidates = data["candidates"]
        qualified_user_ids = data["qualified_user_ids"]
except (json.JSONDecodeError, KeyError):
    themes = []
    candidates = []
    qualified_user_ids = []



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

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        candidates.remove(self.candidate)
        await interaction.response.defer()
        await interaction.followup.delete_message(interaction.message.id)
    @discord.ui.button(label="Skip", style=discord.ButtonStyle.gray)

    async def skip_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.followup.delete_message(interaction.message.id)




load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)



@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="suggest", description="Zaproponuj temat dla nastepnego Jam'u.\nMax 100 liter.")
async def suggest(interaction:discord.Interaction, temat: str):
    if(temat in themes or temat in candidates):
        await interaction.response.send_message(f"Nie udalo sie dodac temat: ``{temat}`` juz zaproponowany, lub czeka na walidacje. Sprawdz pule za pomoca ``/list``", delete_after=30, ephemeral=True)
        return

    if(len(temat)>100):
        await interaction.response.send_message(f"Nie udalo sie dodac temat: Temat jest zadlugi. (Max 100 znakow)", delete_after=30, ephemeral=True)
        return 
    
    candidates.append(temat)
    await interaction.response.send_message(f"Twoj temat oczekuje na validacje. Puzniej zobaczysz go za pomoca ``/list``", delete_after=30, ephemeral=True)

@bot.tree.command(name="list", description="Wyswietla wszystkie tematy w pule.")
async def list(interaction: discord.Interaction):
    if len(themes) <= 0:
        await interaction.response.send_message("Jeszcze niema zadnych temator. Badz pierwszym, zaproponuj temat za pomoca ``/suggest``", ephemeral=True)
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

Zaproponuj swoj temat uzywajac ``/suggest``
""", delete_after=120)
    
@bot.tree.command(name="remove", description="Usun temat z puli")
async def remove(interaction: discord.Interaction, nr_tematu: int):

    if (not interaction.user.guild_permissions.administrator 
        and interaction.user.id not in qualified_user_ids):
        await interaction.response.send_message("Nie masz uprawnien by usuwac tematy z puli.", delete_after=30, ephemeral=True)
        return


    if nr_tematu not in range(1, len(themes)+1):
        await interaction.response.send_message(f"Tematu z numerem {nr_tematu} nie istnieje. Sprawdz pisownie lub zobac liste tematow za pomoca ``/list``", delete_after=30, ephemeral=True)
        return

    themes.remove(themes[nr_tematu-1])
    await interaction.response.send_message(f"Temat usuniento z puli.", delete_after=30, ephemeral=True)


@bot.tree.command(name="validate", description="Cycle tru list of candidates and hand pick valid ones.")
async def validate(interaction: discord.Interaction):
    if (not interaction.user.guild_permissions.administrator 
        and interaction.user.id not in qualified_user_ids):
        await interaction.response.send_message("Nie masz uprawnien by usuwac tematy z puli.", delete_after=30, ephemeral=True)
        return

    await interaction.response.send_message("List of current candidates:", ephemeral=True)
    for candidate in candidates:
        if candidate in themes:
            candidates.remove(candidate)
            continue
        await interaction.followup.send(f"``{candidate}``", ephemeral=True, view=AcceptSuggestView(candidate=candidate))

@bot.tree.command(name="add_qualified_user", description="Nadaje uzytkowniku prawo usuwac i validowac tematy")
@discord.app_commands.default_permissions(administrator=True)
async def add_qualified_user(interaction: discord.Interaction, user: discord.User):
    if(user.id in qualified_user_ids):
        await interaction.response.send_message(f"{user.mention} juz jest w listie kwalifikowanyh userow.", delete_after=30, ephemeral=True)
        return

    qualified_user_ids.append(user.id)
    await interaction.response.send_message(f"Dodano {user.mention} do listy kwalifikowanyh userow.", delete_after=30, ephemeral=True)
    return

@bot.tree.command(name="remove_qualified_user", description="Nadaje uzytkowniku prawo usuwac i validowac tematy")
@discord.app_commands.default_permissions(administrator=True)
async def remove_qualified_user(interaction: discord.Interaction, user: discord.User):
    if(user.id not in qualified_user_ids):
        await interaction.response.send_message(f"{user.mention} nie jest kwalifikowanym userem.", delete_after=30, ephemeral=True)
        return

    qualified_user_ids.remove(user.id)
    await interaction.response.send_message(f"Usuniento {user.mention} z listy kwalifikowanyh userow.", delete_after=30, ephemeral=True)
    return

@bot.tree.command(name="list_qualified_users", description="Nadaje uzytkowniku prawo usuwac i validowac tematy")
@discord.app_commands.default_permissions(administrator=True)
async def list_qualified_users(interaction: discord.Interaction):
    if(len(qualified_user_ids) <=0):
        await interaction.response.send_message(f"Narazie niema zadnego kwalifikowanego usera. Uzyj ``/add_qualified_user`` by je dodac.", delete_after=30, ephemeral=True)
        return

    users = ""
    for id in qualified_user_ids:
        try:
            user = await bot.fetch_user(id)
            users += f"{user.mention}\n"
        except:
            ""

    if users == "":
        await interaction.response.send_message(f"Narazie niema zadnego kwalifikowanego usera. Uzyj ``/add_qualified_user`` by je dodac.", delete_after=30, ephemeral=True)
        return

        
    await interaction.response.send_message(f"Kwalifikowane usery:\n{users}", delete_after=30, ephemeral=True)
    return

try:
    bot.run(TOKEN)
finally:
    with open("cache.json", "w") as file:
        file.truncate()
        file.write(json.dumps({"themes": themes, "candidates": candidates, "qualified_user_ids": qualified_user_ids}))
