import discord
from discord import message
from discord.ext import commands
import os
from gtts import gTTS
import asyncio
from discord.ext import tasks
from dotenv import load_dotenv
load_dotenv()
import requests
import csv

bot = commands.Bot(command_prefix=';',help_command=None)
bot.say_status = ['free']
bot.phrase = ''

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')


# *** STATS ***

@bot.command(name="dlstats",rest_is_raw=True)
async def dlstats(ctx,*,arg):
    f = open("server_data.csv",'w',newline='')
    f.truncate()
    writer = csv.writer(f)
    writer.writerow(["Channel ID","User ID","Time","Jump URL"])

    server = bot.get_guild(772345603400531988) 
    channels = server.text_channels

    n = 0

    await ctx.send("Process started. This will take some time.")

    for channel in channels:
        try:
            msgs = await channel.history(limit=None).flatten()
            for msg in msgs:
                if not msg.author.bot:
                    writer.writerow([str(channel.id), str(msg.author.id), msg.created_at,msg.jump_url])
        except Exception as e:
            print(f"Error on {channel.name}: {e}")
            await ctx.send(f"Couldn't access {channel.name}")
        
        n += 1

        await ctx.send(f"[{n}/{len(channels)}]  {channel.name} processed. <@{ctx.message.author.id}>")
    
    await ctx.send(f"Process done <@{ctx.message.author.id}>")
    f.close()

# *** TTS ***
@bot.command(name="say",rest_is_raw=True)
async def say(ctx,*,text): 
    print("SAY")
    #if ;say is being used
    if bot.say_status[0] == "say":
        await ctx.send(f"`;say` is being used by <@{bot.say_status[1]}>. Please wait.")    
        return

    # If no text is given
    if not text:
        await ctx.send("> Give **text** to say after `;say`")
        return
    
    # This checks if user is connected a voice channel
    if not ctx.author.voice:
        await ctx.send("You have to be in a **voice channel** to use `;say`")
        return
    
    vc_user_connected = ctx.author.voice.channel
    
    try:
      vclient = await vc_user_connected.connect(timeout=2.5) 
    
    # This exception is raised when bot is already connected to a voice channel
    except discord.errors.ClientException:
      if bot.voice_clients[0].channel != vc_user_connected:
        await bot.voice_clients[0].disconnect()
        
        # Again try block because the voice channel to be connected could be locked
        try:
          vclient = await vc_user_connected.connect(timeout=2.5)
        
        except asyncio.TimeoutError:
          await ctx.send("Could not connect to the **voice channel**")
          return
 
    # This exception is usually raised when the voice channel is locked
    except asyncio.TimeoutError:
      await ctx.send("Could not connect to the **voice channel**")
      return
      
    bot.say_status = ["say",ctx.author.id]
    
    # Using TTS and creating .mp3 file 
    speech = gTTS(text=text,lang="en",tld="co.uk")
    speech.save("text.mp3")

    # Plays the text.mp3 file
    vclient.play(discord.FFmpegPCMAudio("text.mp3"))
    
    # Checking when vc finishes playing and disconnecting 
    while vclient.is_playing(): await asyncio.sleep(0.1)
    await vclient.disconnect()

    bot.say_status = ["free"]

# *** CHANGING NICK LOOP ***
bot.nick_count = 0
nick_list = [". deez",". nuts"]

@tasks.loop(seconds=1)
async def nick_loop():
    server = bot.get_guild(772345603400531988)
    member = await server.fetch_member(524200058686799903)
    await member.edit(nick=nick_list[bot.nick_count])
    if bot.nick_count == len(nick_list) - 1: bot.nick_count = 0
    else: bot.nick_count += 1

@nick_loop.before_loop
async def before_nick_loop():
    print("starting ... ")
    await bot.wait_until_ready()

nick_loop.start()

# ** NICK CHANGE **
@bot.command(name="nick",rest_is_raw=True)
async def nick(ctx,nick: str): 
    await ctx.message.delete()
    server = bot.get_guild(772345603400531988)
    members = server.members
    for member in members:
        try:
            await member.edit(nick=nick)
        except Exception as e:
            print(e,member.name)
            continue


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author == bot.user:
        return

bot.run(os.getenv('TOKEN'))
