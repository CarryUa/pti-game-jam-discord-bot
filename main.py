import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from pathlib import Path

        

themes = list[str]()

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

Path("themes.txt").touch(exist_ok=True)
with open("themes.txt", "r") as file:
      for line in file:
        if line.strip():
            themes.append(line.strip())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="suggest", description="Zaproponuj temat dla nastepnego Jam'u.\nMax 100 liter.")
async def suggest(interaction:discord.Interaction, temat: str):
    if(temat in themes):
        await interaction.response.send_message(f"Nie udalo sie dodac temat: ``{temat}`` juz jest w pule. Sprawdz pule za pomoca ``/list``", delete_after=30)
        return

    if(len(temat)>100):
        await interaction.response.send_message(f"Nie udalo sie dodac temat: Temat jest zadlugi. (Max 100 znakow)", delete_after=30)
        return 
    
    themes.append(temat)
    await interaction.response.send_message(f"Dodano ``{temat}`` do puly tematow. Sprawdz pule za pomoca ``/list``", delete_after=30)

@bot.tree.command(name="list", description="Wyswietla wszystkie tematy w pule.")
async def list(interaction: discord.Interaction):
    if len(themes) <= 0:
        await interaction.response.send_message("Jeszcze niema zadnych temator. Badz pierwszym, zaproponuj temat za pomoca ``/suggest``")
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
@app_commands.default_permissions(administrator=True)
async def remove(interaction: discord.Interaction, nr_tematu: int):
    if nr_tematu not in range(1, len(themes)+1):
        await interaction.response.send_message(f"Tematu z numerem {nr_tematu} nie istnieje. Sprawdz pisownie lub zobac liste tematow za pomoca ``/list``", delete_after=30)
        return

    themes.remove(themes[nr_tematu-1])
    await interaction.response.send_message(f"Temat usuniento z puli.", delete_after=30)

try:
    bot.run(TOKEN)
finally:
    print("Saving data...")
    with open("themes.txt", "w") as file:
        file.truncate()
        for theme in themes:
            file.write(theme.strip() + '\n')