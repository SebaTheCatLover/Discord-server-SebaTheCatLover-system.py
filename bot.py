import json
import discord
from discord.ext import commands
from discord import app_commands

import os
import json

def load_profiles():
    if not os.path.exists("profiles.json"):
        with open("profiles.json", "w") as f:
            json.dump({}, f)

    with open("profiles.json", "r") as f:
        return json.load(f)

def save_profiles(profiles):
    with open("profiles.json", "w") as f:
        json.dump(profiles, f, indent=4)

def required_xp(level):
    return 5 * (level + 1)

# Important stuff

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Variables and other

THREAD_ID = 1477630169937346590  # PUT YOUR REPORTS THREAD ID HERE
COUNT_CHANNEL_ID = 1479575731184074913  # your counting channel id
last_number = 0
last_user_id = None
LEVEL_ROLES = {
    1: "Newbie",
    3: "Rookie",
    5: "Regular",
    10: "Prominent",
    20: "Standout",
    35: "Distinguished",
    50: "Renowned",
    70: "Veteran",
    100: "Icon",
    145: "Legend",
    200: "Legacy"
}

# Classes

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot ready.")

class ConfirmAcceptView(discord.ui.View):
    def __init__(self, message, reporter, reported):
        super().__init__(timeout=60)
        self.message = message
        self.reporter = reporter
        self.reported = reported

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        # DM the reporter that the report was accepted
        try:
            await self.reporter.send(
                f"Your report of {self.reported.mention} has been accepted!"
            )
        except:
            pass

        # Change buttons on the original report message
        new_view = AfterAcceptView(self.reporter, self.reported)
        await self.message.edit(view=new_view)

        # remove the confirmation message buttons
        await interaction.response.edit_message(view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)

class ConfirmRejectView(discord.ui.View):
    def __init__(self, report_message, reporter, reported):
        super().__init__(timeout=30)
        self.report_message = report_message
        self.reporter = reporter
        self.reported = reported

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        # DM reporter that the report was rejected
        try:
            await self.reporter.send(
                f"Your report of {self.reported.mention} has been rejected."
            )
        except:
            pass

        # Delete the report message
        await self.report_message.delete()

        # Remove confirmation buttons
        await interaction.response.edit_message(view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)

class AfterAcceptView(discord.ui.View):
    def __init__(self, reporter, reported):
        super().__init__(timeout=None)
        self.reporter = reporter
        self.reported = reported

    @discord.ui.button(label="Done", style=discord.ButtonStyle.green)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):

        thread = interaction.channel

        await thread.send(f"The report of {self.reported.mention} is done!")
        await self.reporter.send(
            f"Your report of {self.reported.mention} was successful!"
        )

        try:
            await thread.remove_user(self.reported)
        except:
            pass

        await interaction.message.delete()

    @discord.ui.button(label="Wrong", style=discord.ButtonStyle.red)
    async def wrong(self, interaction: discord.Interaction, button: discord.ui.Button):

        await self.reporter.send(
            f"Your report of {self.reported.mention} was a failure."
        )

        await interaction.message.delete()


class ReportView(discord.ui.View):
    def __init__(self, reporter, reported):
        super().__init__(timeout=None)
        self.reporter = reporter
        self.reported = reported

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConfirmAcceptView(interaction.message, self.reporter, self.reported)

        await interaction.response.send_message(
            "Are you sure you want to accept the report?",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ConfirmRejectView(interaction.message, self.reporter, self.reported)

        await interaction.response.send_message(
            "Are you sure you want to reject the report?",
            view=view,
            ephemeral=True
        )

class BioModal(discord.ui.Modal, title="Change Bio"):

    bio = discord.ui.TextInput(
        label="Bio",
        placeholder="Bio (up to 500 characters)",
        max_length=500,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):

        profiles = load_profiles()
        user_id = str(interaction.user.id)

        if user_id not in profiles:
            profiles[user_id] = {"xp": 0, "level": 0, "bio": ""}

        profiles[user_id]["bio"] = self.bio.value

        save_profiles(profiles)

        await interaction.response.send_message(
            "Your bio has been updated!",
            ephemeral=True
        )

class ProfileView(discord.ui.View):

    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Change Bio", style=discord.ButtonStyle.primary)
    async def change_bio(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "You can't edit someone else's bio.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(BioModal())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

# Events

@bot.tree.command(name="report", description="Report a user")
async def report(interaction: discord.Interaction, user: discord.Member, reason: str):

    if user.id == interaction.user.id:
        await interaction.response.send_message(
            "You cannot report yourself.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
    "Thank you for your report!\nModerators will review your report and take care of it!",
    ephemeral=True
    )

    thread = bot.get_channel(THREAD_ID)

    view = ReportView(interaction.user, user)

    report_message = await thread.send(
        f"User {interaction.user.mention} reported {user.mention} with a reason: {reason}",
        view=view
    )

    # store message reference properly
    view.report_message = report_message

    try:
        await thread.remove_user(user)
    except:
        pass

@bot.tree.command(name="checkprofile", description="Check a user's profile")
async def checkprofile(interaction: discord.Interaction, user: discord.Member):

    profiles = load_profiles()
    user_id = str(user.id)

    if user_id not in profiles:
        profiles[user_id] = {"xp": 0, "level": 0, "bio": "No bio yet."}
        save_profiles(profiles)

    bio = profiles[user_id]["bio"]
    level = profiles[user_id]["level"]
    xp = profiles[user_id]["xp"]

    needed = required_xp(level)

    if level == 200:
        level_text = f"Level: MAX - {level}"
    else:
        level_text = f"Level: {level}"

    embed = discord.Embed()

    if interaction.user.id == user.id:
        embed.title = f"You - {user.name}"
        embed.description = (
            f"{bio}\n\n"
            f"{level_text}\n"
            f"{xp}/{needed} XP"
        )
        view = ProfileView(user.id)
    else:
        embed.title = user.name
        embed.description = bio
        view = None

    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True
    )

# allowed digits
ALLOWED_DIGITS = set("0123456789")

@bot.event
async def on_message(message):
    global last_number, last_user_id

    if message.author.bot:
        return

    if message.channel.id != COUNT_CHANNEL_ID:
        await bot.process_commands(message)
        return

    content = message.content.strip()

    # Only numbers allowed
    if not content.isdigit():
        reached = last_number
        last_number = 0
        last_user_id = None

        await message.channel.send(
            f"{message.author.mention} has ruined the counting of {reached}\n"
            "You can't say anything else than numbers"
        )
        return

    number = int(content)

    # Same user twice
    if message.author.id == last_user_id:
        reached = last_number
        last_number = 0
        last_user_id = None

        await message.channel.send(
            f"{message.author.mention} has ruined the counting of {reached}\n"
            "You can't say twice in a row"
        )
        return

    # Wrong number
    if number != last_number + 1:
        reached = last_number
        last_number = 0
        last_user_id = None

        await message.channel.send(
            f"{message.author.mention} has ruined the counting of {reached}"
        )
        return

    last_number = number
    last_user_id = message.author.id

    await bot.process_commands(message)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    profiles = load_profiles()
    user_id = str(message.author.id)

    if user_id not in profiles:
        profiles[user_id] = {
            "xp": 0,
            "level": 0,
            "bio": "No bio yet."
        }

    new_level = profiles[user_id]["level"]

    if new_level in LEVEL_ROLES:
        role_name = LEVEL_ROLES[new_level]
        role = discord.utils.get(message.guild.roles, name=role_name)

        if role:
            await message.author.add_roles(role)

    profiles[user_id]["xp"] += 1

    leveled_up = False

    while profiles[user_id]["xp"] >= required_xp(profiles[user_id]["level"]):
        profiles[user_id]["xp"] -= required_xp(profiles[user_id]["level"])
        profiles[user_id]["level"] += 1
        leveled_up = True

    save_profiles(profiles)

    if leveled_up:
        channel = discord.utils.get(message.guild.text_channels, name="💬◆general")
        if channel:
            await channel.send(f"{message.author.mention} has leveled up to {profiles[user_id]['level']}!")

    await bot.process_commands(message)
