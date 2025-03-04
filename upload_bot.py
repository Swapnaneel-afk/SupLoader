import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class ScreenshotUploader(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        # Constants
        self.MAX_FILES_PER_BATCH = 10
        self.SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.gif')
        self.PROGRESS_BAR_LENGTH = 20

    async def setup_hook(self):
        await self.add_cog(UploadCog(self))

    def create_progress_bar(self, current, total):
        percentage = current / total
        filled_length = int(self.PROGRESS_BAR_LENGTH * percentage)
        bar = '█' * filled_length + '░' * (self.PROGRESS_BAR_LENGTH - filled_length)
        return f'[{bar}] {int(percentage * 100)}%'

class UploadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.upload_tasks = {}

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"Bot is ready! Logged in as {self.bot.user}")
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for !help"
            )
        )

    @commands.command()
    async def upload_screenshots(self, ctx, folder_path: str):
        """Upload screenshots from specified folder in batches"""
        try:
            await self._handle_upload(ctx, folder_path)
        except Exception as e:
            logging.error(f"Error in upload_screenshots: {str(e)}")
            await ctx.send(f"❌ An error occurred: {str(e)}")

    async def _handle_upload(self, ctx, folder_path: str):
        # Validate folder path
        if not os.path.isdir(folder_path):
            raise ValueError(f"'{folder_path}' is not a valid directory!")

        # Get screenshot files
        screenshot_files = [
            f for f in os.listdir(folder_path)
            if f.lower().endswith(self.bot.SUPPORTED_FORMATS)
        ]

        if not screenshot_files:
            await ctx.send(f"📂 No supported image files found in '{folder_path}'!")
            return

        # Start upload process
        total_files = len(screenshot_files)
        status_message = await ctx.send(
            f"🔍 Found {total_files} files\n"
            f"📤 Starting upload in batches of {self.bot.MAX_FILES_PER_BATCH}\n"
            f"⏳ Progress: {self.bot.create_progress_bar(0, total_files)}"
        )

        start_time = datetime.now()
        files_uploaded = 0

        for i in range(0, total_files, self.bot.MAX_FILES_PER_BATCH):
            batch = screenshot_files[i:i + self.bot.MAX_FILES_PER_BATCH]
            files_to_upload = []

            for screenshot in batch:
                file_path = os.path.join(folder_path, screenshot)
                files_to_upload.append(discord.File(file_path))

            current_batch = i // self.bot.MAX_FILES_PER_BATCH + 1
            total_batches = (total_files - 1) // self.bot.MAX_FILES_PER_BATCH + 1

            await ctx.send(
                f"📦 Batch {current_batch}/{total_batches}",
                files=files_to_upload
            )

            files_uploaded += len(batch)
            await status_message.edit(content=
                f"🔍 Found {total_files} files\n"
                f"📤 Uploading batch {current_batch}/{total_batches}\n"
                f"⏳ Progress: {self.bot.create_progress_bar(files_uploaded, total_files)}"
            )

            # Small delay to prevent rate limiting
            await asyncio.sleep(1)

        # Calculate upload statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        speed = total_files / duration if duration > 0 else 0

        await status_message.edit(content=
            f"✅ Upload Complete!\n"
            f"📊 Statistics:\n"
            f"└── Files: {total_files}\n"
            f"└── Time: {duration:.2f}s\n"
            f"└── Speed: {speed:.2f} files/s\n"
            f"└── Progress: {self.bot.create_progress_bar(total_files, total_files)}"
        )

def setup():
    load_dotenv()
    bot = ScreenshotUploader()
    
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Please provide a folder path!\nUsage: !upload_screenshots <folder_path>")
        else:
            await ctx.send(f"❌ An error occurred: {str(error)}")

    return bot

if __name__ == "__main__":
    bot = setup()
    try:
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable not set!")
        bot.run(token)
    except discord.LoginFailure:
        logging.error("Failed to login: Invalid token")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
