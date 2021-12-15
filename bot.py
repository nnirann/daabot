import discord
from discord import message
from discord.ext import commands
import os
from gtts import gTTS
import mysql.connector
import asyncio
from discord.ext import tasks

from dotenv import load_dotenv
load_dotenv()

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from cloudinary.uploader import upload

import requests

bot = commands.Bot(command_prefix=';',help_command=None)
bot.say_status = ['free']
bot.play_status = ['free']
bot.dl_status = ['free']
bot.num_gifs = 0
bot.phrase = ''

bot.gossip_list = []


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

"""
mydb = mysql.connector.connect(host='sql6.freemysqlhosting.net', user='sql6417723', password=os.getenv('sqlpass') , database='sql6417723')
cur = mydb.cursor()
"""

# *** HELP COMMAND ***

@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(
        title = "HELP",
        description = "Commands for daa bot. Use `;help <command>` for detailed help.",
        color = 0x00ffff,
    )
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/app-icons/850273933551075338/7114885a6d030442c21e3ae16afe84d5.png")    

    embed.add_field(
        name = "COMBOGIF COMMANDS",
        value = """
            `makecombo` : Used to **make combo gifs**. Aliases: `mc` , `combo`
            `sendcombo` : Used to **send combo gifs**. Aliases : `s`
            `listcombo` : Used to **list combo gifs**. Aliases : `lc` , `list`
            `renamecombo` : Used to **rename combo gifs**. Aliases : `rc`
            `deletecombo` : Used to **delete combo gifs**. Aliases : `dc` , `delc`
        """,
        inline = False
    )
    
    await ctx.send(embed=embed)

"""
# *** COMBOGIF COMMANDS *** 

@bot.command(name='makecombo',aliases=['mc','combo'],help="Used to make combo gifs\n Syntax: makecombo <combo name>",rest_is_raw=True)
async def makecombo(ctx, *, arg):
    if not arg:
        await ctx.send('You need to give a name after `makecombo`')
        return

    if bot.say_status[0] == 'makecombo':
        await ctx.send('`combogif` is being used now. Please wait.')
        return

    bot.phrase = arg.strip()
    server_id = ctx.guild.id

    # checking if that combogif exists
    try:
        cur.execute(f"select gif_name from t{server_id} where user_id = '{ctx.message.author.id}' and gif_name = '{bot.phrase}'")
        data = cur.fetchall()
        
        if len(data) != 0:
            await ctx.send(f"There already exists {len(data)} gif(s) associated with that name. If you want to add to that combogif, send the gifs and then send `done`. Else send `done` now")
            bot.num_gifs = len(data)
        
        else:    
            await ctx.send(f"Send gif(s) you want to combine for `{bot.phrase}` or send `done` when done")
    
    except mysql.connector.errors.ProgrammingError: # error raised when no record of that user is found
        await ctx.send(f"Send gif(s) you want to combine for `{bot.phrase}` or send `done` when done")

    bot.say_status = ['makecombo', ctx.message.author.id] 

    # checking table of that server exists in the db
    cur.execute('show tables')
    if (f't{server_id}',) not in cur.fetchall():
        cur.execute(f'create table t{server_id} (id int auto_increment primary key, user_id varchar(50), gif_name varchar(50), gif_link varchar(200))')


@bot.command(name="sendcombo",aliases=['s','send'],help="Used to send combogif \nSyntax: sendcombo <combo name>")
async def send(ctx, *, arg):
    at_pos = arg.find('@')
    if at_pos != -1:
        combo_name = arg[:at_pos-1].strip()
        tags = arg[at_pos-1:]

    else:
        combo_name = arg
        tags = ''

    server_id = ctx.guild.id
    cur.execute(f'select gif_link from t{server_id} where gif_name = "{combo_name}" and user_id = "{ctx.author.id}"')
    data = cur.fetchall()

    if len(data) == 0:
        await ctx.send(f'There is no combogif called `{combo_name}`')

    else:
        await ctx.message.delete()
        await ctx.send(f'<@{ctx.author.id}> sent -> {tags}')
        for i in data:
            await ctx.send(i[0])

@bot.command(name="listcombo",aliases=['lc','list'],help="Lists your combo gifs\nSyntax: listcombo")
async def list(ctx):
    server_id = ctx.guild.id
    cur.execute(f"select distinct gif_name from t{server_id} where user_id = '{ctx.message.author.id}'")
    data = cur.fetchall()
    msg = ''
    if len(data) == 0 :
        msg = 'You have no combogifs.'
    for i in range(len(data)):
        msg += f"**{i+1}** {data[i][0]} \n"

    await ctx.send(msg)


@bot.command(name="renamecombo",aliases=["rc"],help="Rename combo gif. \nSyntax: `;renamecombo <old_name> = <new_name>`",rest_is_raw=True)
async def rename(ctx,*,arg):
    if not arg:
        await ctx.send('Give arguments after `;renamecombo`')
        return
    
    if arg.find('=') == -1: 
        await ctx.send('Give `<old name of combo> = <new name of combo>` to rename')
        return
    
    splt = arg.split('=')
    if len(splt) != 2:
        await ctx.send('You need to give both old name and new name for the combo.')
        return

    old_name,new_name = splt[0].strip() , splt[1].strip()
        
    server_id = ctx.guild.id
 
    cur.execute(f"select exists(select * from t{server_id} where user_id = '{ctx.message.author.id}' and gif_name = '{old_name}')")
    if cur.fetchall()[0][0] == 1:
        cur.execute(f'update t{server_id} set gif_name = "{new_name}" where gif_name = "{old_name}" and user_id = "{ctx.message.author.id}"')
        mydb.commit()
        await ctx.send(f'Changed name of combogif from `{old_name}` to `{new_name}`')
    else :
        await ctx.send(f'Combogif {old_name} not found.')    


@bot.command(name="deletecombo",aliases=['dc','delc'],help="Deletes combo gif\nSyntax: deletecombo <combo gif name>",rest_is_raw=True)
async def delete(ctx,*,arg):
    name = arg.strip()
    if not name:
        await ctx.send('Give the name of combogif to delete')
        return

    server_id = ctx.guild.id
    cur.execute(f"select exists(select * from t{server_id} where user_id = '{ctx.message.author.id}' and gif_name = '{name}')")
    if cur.fetchall()[0][0] == 1: #that exists
        cur.execute(f"delete from t{server_id} where user_id = '{ctx.message.author.id}' and gif_name = '{name}'")
        mydb.commit()
        await ctx.send(f"Combogif `{name}` was deleted.")
    else:
        await ctx.send(f"There are no combogifs named `{name}`")
"""

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

# *** SONG DOWNLOAD (ONLY RYTHM PLAYING SONGS) ***

async def download_song(ctx,link):
    bot.dl_status = ["dl"]
    og_msg = await ctx.send(f"Download started <@{ctx.message.author.id}>")
    stream = os.popen(f'spotdl "{link}"')
    output = stream.read()

    mp3_file_names = [x for x in os.listdir() if x.endswith(".mp3") and x != "text.mp3"]
    if mp3_file_names == []:
        await ctx.send(f"There was an error in downloading this <@{ctx.message.author.id}>")
        bot.dl_status = ["free"]
        return

    file_name = mp3_file_names[0] 
    await og_msg.edit(content=f"Download finished. Generating URL")

    url_to_get = f"https://res.cloudinary.com/daabot/video/upload/{file_name}".replace(" ","%20")
    r = requests.get(url_to_get)
    print(r)
    if r.status_code == 404:
        res = upload(file_name,resource_type='video',public_id=file_name[:-4])
        embed=discord.Embed(title=file_name[:-4],description=f"[Download Link]({res['secure_url']})")
    else:
        embed=discord.Embed(title=file_name[:-4],description=f"[Download Link]({url_to_get})")
        
    await ctx.send(f"<@{ctx.message.author.id}>")
    await ctx.send(embed=embed)
        
    await og_msg.delete()
    os.remove(file_name)
    bot.dl_status = ["free"]

@bot.command(name="download",aliases=["dl"],rest_is_raw=True)
async def download(ctx,*,link): 
    if not link:
        await ctx.send("Right now you need to give spotify link to the song to download. Feature to download currently playing song is in development.")
        return
    
    if "/album/" in link or "/playlist/" in link: 
        await ctx.send("Only downloading songs is supported now")
    else: 
        if bot.dl_status[0] == "free":
            await download_song(ctx,link)
        else:
            await ctx.send(";dl is being used now. Please wait.")

@bot.command(name="play",aliases=["p"],rest_is_raw=True)
async def play(ctx,*,term):
    if bot.play_status[0] == "search":
        await ctx.send(f"This command is being used by <@{bot.play_status[1]}>. Please wait.")
        return

    if not term:
        await ctx.send("Please give a search term.")
        return
    

    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    results = spotify.search(q=term)
    value = ""
    for x,item in enumerate(results["tracks"]["items"]):
        value += f'{x+1}.\t`{item["name"]}` by `{", ".join([artist["name"] for artist in item["artists"]])}` \n'

    embed = discord.Embed()

    embed.add_field(
        name = f"`{term.strip()}` - Search Results",
        value = value + "\nGive number of search result you want to play. Or send `cancel`"
    )
    
    embed_sent = await ctx.send(embed=embed)

    bot.play_status = ["search",ctx.author.id,[item["external_urls"]["spotify"] for item in results["tracks"]["items"]],embed_sent]

@bot.command(name="nick")
async def nick(ctx):
    if ctx.message.author.id == 524200058686799903:
        await ctx.message.author.edit(nick="nir")
        await ctx.send("changed?")

@tasks.loop(seconds=1.0)
async def nick_loop():
    server = bot.get_guild(772345603400531988)
    member = server.get_member(524200058686799903)
    if member.nick == "absolutely":
        await member.edit(nick="amazing")
    elif member.nick == "amazing":
        await member.edit(nick="absolutely")

@nick_loop.before_loop
    async def before_nick_loop(self):
        await bot.wait_until_ready()

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.content == "test":
        msgs = await message.channel.history(limit=5).flatten()
        await message.channel.send(f"{msgs}")
    
    if bot.play_status[0] == "search":
        if bot.play_status[1] == message.author.id:
            if message.content.isnumeric():
                index = int(message.content)-1
                if index in range(len(bot.play_status[2])):
                    await message.channel.send(f"`.play {bot.play_status[2][index]}`\n<@{bot.play_status[1]}>")
                    await bot.play_status[3].delete()
                    await message.delete()
                    bot.play_status = ["free"]
                else:
                    await message.channel.send("Please give a number in the search results")
            elif message.content == "cancel":
                await message.channel.send("Cancelled")
                bot.play_status = ["free"]


    if message.author == bot.user:
        return


    """
    # if user is sending the gifs for making combo
    if bot.say_status[0] == "makecombo":
        # confirming same user initiated the sequence
        if message.author.id == bot.say_status[1]:

            # if it's a gif link
            if message.content.startswith('https://giphy.com/gifs/') or message.content.startswith('https://tenor.com/view/'):
                if bot.num_gifs == 5:
                    await message.channel.send('You can only have maximum 5 gifs in one combo.')
                    return
                else:
                    bot.num_gifs += 1
                    server_id = message.guild.id
                    # adding the link to the table
                    cur.execute(f"insert into t{server_id} (user_id,gif_name,gif_link) values ('{message.author.id}','{bot.phrase}','{message.content}')")
                    mydb.commit()

            # if its the end
            elif message.content == 'done':
                await message.channel.send(f'Combined {bot.num_gifs} gif(s). Use `;send {bot.phrase}` for me to send this combo.')
                bot.say_status = ['free']   
                bot.num_gifs = 0

"""

bot.run(os.getenv('TOKEN'))
