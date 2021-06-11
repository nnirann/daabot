from discord import message
from discord.ext import commands
import os
from gtts import gTTS
import mysql.connector
import asyncio

from dotenv import load_dotenv
load_dotenv()

help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)

bot = commands.Bot(command_prefix=';',help_command=help_command)

bot.status = ['free']
bot.num_gifs = 0
bot.phrase = ''

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

mydb = mysql.connector.connect(host='sql6.freemysqlhosting.net', user='sql6417723', password=os.getenv('sqlpass') , database='sql6417723')
cur = mydb.cursor()

# --------------- START OF COMBOGIF COMMANDS --------------- #

# initiated combogif command
@bot.command(name='makecombo',aliases=['mc','combo'],help="Used to create a combogif [Aliases : mc , combo]",rest_is_raw=True)
async def makecombo(ctx, *, arg):
    if not arg:
        await ctx.send('You need to give a name after `makecombo`')
        return

    if bot.status[0] == 'makecombo':
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

    bot.status = ['makecombo', ctx.message.author.id] 

    # checking table of that server exists in the db
    cur.execute('show tables')
    if (f't{server_id}',) not in cur.fetchall():
        cur.execute(f'create table t{server_id} (id int auto_increment primary key, user_id varchar(50), gif_name varchar(50), gif_link varchar(200))')


@bot.command(name="send",aliases=['s'],help="Used to send combogif [Aliases : s]")
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


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author == bot.user:
        return

    # if user is sending the gifs for making combo
    if 'makecombo' == bot.status[0]:
        # confirming same user initiated the sequence
        if message.author.id == bot.status[1]:

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
                bot.status = ['free']   
                bot.num_gifs = 0

@bot.command(name="listcombo",aliases=['lc','list'],help="Lists your combo gifs [Aliases : lc , list]")
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


@bot.command(name="deletecombo",aliases=['dc','delc'],help="Deletes combo gif [Aliases : dc , delc]",rest_is_raw=True)
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

# --------------- END OF COMBOGIF COMMANDS -------------- #


# --------------- START OF TTS COMMANDS -------------- #

@bot.command(name='say',help="Says the text in the voice channel you are connected to.",rest_is_raw=True)
async def tts(ctx,*,arg):
    if not arg:
        await ctx.send('Give text after `;say`')
        return

    if bot.status == ['tts']:
        await ctx.send('`say` command is being used. Please wait.')
        return
    
    if not ctx.author.voice:
        await ctx.send('You have to be in a voice channel to use this command.')
        return 
    
    channel = ctx.author.voice.channel.name
    
    speech = gTTS(text=arg)
    speech.save("text.mp3")
    
    vc = discord.utils.get(ctx.guild.voice_channels,name=channel)
    await vc.connect()
    
    await asyncio.sleep(1)

    voice = discord.utils.get(bot.voice_clients,guild=ctx.guild)
    voice.play(discord.FFmpegPCMAudio("text.mp3"))
    bot.status = ['tts']

    while voice.is_playing():
        await asyncio.sleep(0.1)
    await voice.disconnect()
   
    bot.status = ['free']



# --------------- END OF TTS COMMANDS -------------- #
bot.run(os.getenv('TOKEN'))
