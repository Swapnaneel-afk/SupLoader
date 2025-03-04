import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Constant for batch size
MAX_FILES_PER_MESSAGE = 10

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("------")

@bot.command()
async def upload_screenshots(ctx, folder_path: str):
    try:
        if not os.path.isdir(folder_path):
            await ctx.send(f"Error: '{folder_path}' is not a valid directory!")
            return
        
        screenshot_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not screenshot_files:
            await ctx.send(f"No image files found in '{folder_path}'!")
            return
        
        total_files = len(screenshot_files)
        await ctx.send(f"Found {total_files} files. Starting upload in batches of {MAX_FILES_PER_MESSAGE}...")
        
        for i in range(0, total_files, MAX_FILES_PER_MESSAGE):
            batch = screenshot_files[i:i + MAX_FILES_PER_MESSAGE]
            files_to_upload = []
            
            for screenshot in batch:
                file_path = os.path.join(folder_path, screenshot)
                files_to_upload.append(discord.File(file_path))
            
            current_batch = i // MAX_FILES_PER_MESSAGE + 1
            total_batches = (total_files - 1) // MAX_FILES_PER_MESSAGE + 1
            
            await ctx.send(
                f"Uploading batch {current_batch}/{total_batches}",
                files=files_to_upload
            )
        
        await ctx.send(f"✅ Finished uploading all {total_files} screenshots!")
    
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    try:
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable not set!")
        bot.run(token)
    except discord.LoginFailure:
        print("Failed to login: Invalid token")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
