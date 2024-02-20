import discord
import discord.utils
import asyncio
import random
import traceback
import os
import requests
import json
import aiohttp
import io
import wikipedia
import typing
import fortune
import time
import yt_dlp
import typing
import markov
import json
import sys
import config as global_config
import retr
import time

from datetime import datetime, timedelta
from difflib import get_close_matches
from os.path import isfile
from discord.ext import commands
from discord.ext.commands import BadArgument, Context
from os import getenv
from dotenv import load_dotenv
from categories import buildHelpEmbed, buildCategoryEmbeds, helpCategory

genaiDataPath = 'data/genai_info.json'
GUILD_SEEK_FILENAME = 'data/guild_seek.json'
KGB_RETR = 'data/retr.txt'
RETR_PUBLISHERS = {
    'soviet': retr.Publisher(1067091686725001306, 'data/retr.txt'),
    'griss': retr.Publisher(1131911759968612434, 'data/retrgris.txt'),
}

last_command_time={}

ERR_CHANNEL_ID = 1123467774098935828

def loadFile(path: str):
    if not isfile(path): return {}

    with open(path) as f:
        return json.load(f)

channels = loadFile('data/channels.json')
genAiArray: dict[str, markov.MarkovGen] = {k: markov.MarkovGen(states=v['state'], config=v['config']) for k,v in loadFile(genaiDataPath).items()}
msgCounter = 0

print('AdventurerUp Corporation')
kgb = commands.Bot(command_prefix = global_config.prefix, strip_after_prefix = True, sync_commands=True, intents = discord.Intents.all())
kgb.remove_command('help')
load_dotenv()

HELP_EMB: typing.Union[discord.Embed, None] = None
HELP_CAT_EMB: typing.Union[list[discord.Embed], None] = None
HELP_CAT_HIDDEN: typing.Union[dict[str, discord.Embed], None] = None

if not os.path.isfile('data/guild_seek.json'):
    with open('data/guild_seek.json', 'w', encoding='utf-8') as f:
        f.write('{}')

async def change_status():
    statuses = 'kgb!help', 'версия 3.0', 'на {} серверах!'
    index = 0
    while not kgb.is_closed():
        servers_count = len(kgb.guilds)
        status = statuses[index].format(servers_count)
        try: await kgb.change_presence(activity=discord.Game(name=status))
        except: pass
        index = (index+1) % len(statuses)
        await asyncio.sleep(10)

async def read_stderr():
    channel = kgb.get_channel(ERR_CHANNEL_ID)
    if not isinstance(channel, discord.TextChannel):
        print(f'{ERR_CHANNEL_ID} is not a valid channel id!')
        return
    f = open('temp.log')

    print('Logger started')
    while not kgb.is_closed():
        val = f.read()

        if len(val) == 0:
            await asyncio.sleep(1)
            continue

        print(val, end='')
        i = 0
        while i < len(val):
            await channel.send(f'```{val[i:i+1994]}```')
            await asyncio.sleep(1)
            i += 1994

async def sync_retr():
    while True:
        await asyncio.sleep(10)
        for pub in RETR_PUBLISHERS.values():
            pub.sync_retr()

async def update_guild_seek():
    guild_seek = {}
    for guild in kgb.guilds:
        guild_info = {
            'name': guild.name,
            'users': [{
                'name': member.name, 
                'discriminator': member.discriminator
            } for member in guild.members]
        }

        guild_seek[str(guild.id)] = guild_info

    with open(GUILD_SEEK_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(guild_seek, f, ensure_ascii=False, indent=4)
      
async def update_guild_names():
    guild_names = sorted([guild.name for guild in kgb.guilds])
    with open('data/guild_names.json', 'w', encoding='utf-8') as f:
        json.dump(guild_names, f, ensure_ascii=False, indent=4)

async def send_error_embed(ctx, err_msg: str):
    await ctx.reply(embed = discord.Embed(
        title = 'Ошибка!',
        description = err_msg,
        color = discord.Colour(0xFF0000)
    ))

def get_crypto_price(symbol, api_key):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=rub"
    headers = {
        "Content-Type": "application/json",
        "X-CoinAPI-Key": api_key
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    return data.get(symbol, {}).get("rub")

def get_embed_color(argument):
    colors = {
        "monero": discord.Color(0xff8917),
        "zephyr": discord.Color(0x76ede9),
        "bitcoin": discord.Color(0xffc227),
        "ethereum": discord.Color(0x6b7ce5),
        "dogecoin": discord.Color(0xfbbe91),
        "usdt": discord.Color(0x96ecb30)
    }
    return colors.get(argument, discord.Color(0x000000))

def no_format(user):
    if isinstance(user, discord.Member) and user.discriminator != '0':
        return f'{user.name}#{user.discriminator}'
    return user.name

def execute_code(code):
    forbidden_keywords = [
        'def', 
        'eval', 
        'while', 
        '*', 
        'import', 
        'print', 
        'return', 
        'sudo', 
        'subprocess',
        'eval',
        'exec',
        'system'
    ]
    
    for keyword in forbidden_keywords:
        if keyword in code:
            return 'Код содержит запрещенное ключевое слово: {}'.format(keyword)

    try:
        exec('from hellya import *\n' + code)
        return 'Код успешно выполнен.'
    except Exception as e:
        return f'{str(e)}'

@kgb.event
async def on_ready():
    kgb.loop.create_task(change_status())
    kgb.loop.create_task(read_stderr())
    kgb.loop.create_task(sync_retr())
    await update_guild_names()
    while True:
        try:
            await asyncio.wait_for(update_guild_names(), timeout=30.0)
        except asyncio.TimeoutError:
            print('update_guild_names() timed out')
        await update_guild_seek()
        await asyncio.sleep(3600)
      
@kgb.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    if guild_id in channels:
        channel_id = channels[guild_id]
        channel = kgb.get_channel(int(channel_id))

        if not isinstance(channel, discord.TextChannel): return
        await channel.send(f'Приветствую вас на этом сервере, {member.mention}!')

def saveGenAiState():
    global msgCounter
    msgCounter = msgCounter + 1

    if msgCounter % 10 != 0: return

    with open(genaiDataPath, 'w') as f:
        json.dump({k: {
            'state': v.dumpState(),
            'config': v.config,
        } for k,v in genAiArray.items()}, f)

async def manageGenAiMsgs(message) -> bool:
    replied = False

    channelId = str(message.channel.id)

    if message.author == kgb.user: return replied
    if channelId not in genAiArray or not genAiArray[channelId].config['read']: return replied

    genAi = genAiArray[channelId]
    genAi.addMessage(message.content)

    if not genAi.config['reply_on_mention']: return replied

    if not kgb.user: return replied
    for user in message.mentions:
        if user.id != kgb.user.id: continue

        await message.reply(genAi.generate()[:2000])
        replied = True
        break

    return replied

@kgb.event
async def on_message(message):
    for retr in RETR_PUBLISHERS.values(): await retr.publish(kgb, message)

    replied = await manageGenAiMsgs(message)
    saveGenAiState()

    if message.content == '<@1061907927880974406>' and not replied:
        return await message.channel.send('Мой префикс - `kgb!`')

    await kgb.process_commands(message)

@kgb.event
async def on_member_remove(member):
    guild_id = str(member.guild.id)
    if guild_id not in channels: return

    channel_id = channels[guild_id]
    channel = kgb.get_channel(int(channel_id))
    if not isinstance(channel, discord.TextChannel): return
    
    await channel.send(f'Прощай, {member.mention}!')

@kgb.event
async def on_command_error(ctx, exc):
    if isinstance(exc, BadArgument):
        await send_error_embed(ctx, 'Найдены некорректные аргументы')
    elif isinstance(exc, commands.CommandNotFound):
        cmd = ctx.invoked_with
        cmds = [cmd.name for cmd in kgb.commands]
        matches = get_close_matches(cmd, cmds)

        if len(matches) > 0:
            await send_error_embed(ctx, f'Команда `kgb!{cmd}` не найдена, может вы имели ввиду `kgb!{matches[0]}`?')
            return

        await send_error_embed(ctx, 'Команда не найдена. \nПожалуйста, напишите `kgb!help` чтобы посмотреть полный список команд!')
    elif isinstance(exc, commands.CommandOnCooldown):
        await send_error_embed(ctx, 'Эта команда перезагружается!\n'
                                   f'Повторите попытку через {round(exc.retry_after, 2)} секунд.')
    elif isinstance(exc, commands.MissingPermissions):
        await send_error_embed(ctx, 'Вы не имеете прав администратора!')
    elif isinstance(exc, commands.MissingRequiredArgument):
        await send_error_embed(ctx, f'Пропущен аргумент: `{exc.param.name}`!')
    else:
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
        await send_error_embed(ctx, exc)
    
@kgb.event
async def on_guild_join(guild: discord.Guild):
    url = global_config.on_guild_join_pic
    embed = discord.Embed(title = 'Hello, comrades!', color = 0xff0000)
    embed.set_image(url = url)

    validChannel = None
    for channel in guild.text_channels:
        if not channel.permissions_for(guild.me).send_messages: continue
        validChannel = channel
        await channel.send(embed = embed)
        break

    if not validChannel: return

    embed = discord.Embed(
        title = 'Я KGB Modern', 
        description = 
            'Modern KGB - универсальный помощник на вашем сервере!\n' 
            'Он имеет:\n'
            '1.Встроенный генератор маркова, создающий оригинальные сообщения на основе старых.\n'
            '2.Множество прикольных апи.\n'
            '3.Возможность воспроизведения музыки в голосовых каналах.\n'
            '4.Большое множество команд\n', 
        color = 0x000000
    )

    await validChannel.send(embed=embed)
  
@kgb.command(description='Выведет список команд или информацию о команде')
async def help(ctx, *, query=None):
    if isinstance(ctx.channel, discord.DMChannel):
        return

    if query is None:
        if HELP_EMB is None:
            embed = discord.Embed(title='Системная ошибка:', description='Эмбед помощи не собран!', color=discord.Colour(0xFF0000))
            await ctx.reply(embed=embed)
            return
        
        await ctx.reply(embed=HELP_EMB)
        return

    if query.isdigit():
        if HELP_CAT_EMB is None:
            embed = discord.Embed(title='Системная ошибка:', description='Эмбед помощи категорий не собран!', color=discord.Colour(0xFF0000))
            await ctx.reply(embed=embed)
            return

        try:
            if int(query) < 1: raise IndexError

            await ctx.reply(embed=HELP_CAT_EMB[int(query) - 1])
            return
        except IndexError:
            await send_error_embed(ctx, 'Неверный номер категории.')
            return

    try:
        if not HELP_CAT_HIDDEN is None:
            await ctx.reply(embed=HELP_CAT_HIDDEN[query])
            return
    except KeyError:
        pass

    command = kgb.get_command(query)
    if command is None:
        await send_error_embed(ctx, f'Команда `{query}` не найдена.')
        return

    embed = discord.Embed(title='Описание команды:', description=command.description, color=discord.Colour(0x000000))
    if command.aliases:
        aliases = ', '.join(command.aliases)
        embed.add_field(name='Альтернативные названия:', value=aliases, inline=False)

    usage = f'kgb!{command.name} {command.signature}'
    embed.add_field(name=f'Использование:', value=f'`{usage}`', inline=False)

    await ctx.reply(embed=embed)
  
async def getApiImage(ctx, url: str) -> None:
    if isinstance(ctx.channel, discord.DMChannel): return

    data = requests.get(url).json()

    embed = discord.Embed(color=0x000000)
    embed.set_footer(text=data['fact'])
    embed.set_image(url=data['image'])

    await ctx.reply(embed=embed)

@kgb.command(description = 'Кот')
@helpCategory('api')
async def cat(ctx): await getApiImage(ctx, 'https://some-random-api.com/animal/cat')
  
@kgb.command(description = 'Собака')
@helpCategory('api')
async def dog(ctx): await getApiImage(ctx, 'https://some-random-api.com/animal/dog')
  
@kgb.command(description = 'Лис')
@helpCategory('api')
async def fox(ctx): await getApiImage(ctx, 'https://some-random-api.com/animal/fox')
  
@kgb.command(description = 'Выключает бота (только для разработчика)')
@helpCategory('secret')
async def killbot(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    if ctx.author.id != 745674921774153799:
        await send_error_embed(ctx, 'Эта команда только для разработчиков!')
        return

    await ctx.reply(embed = discord.Embed(
        title = 'Пожалуйста подождите:',
        description = 'Бот выключиться через 3 секунды!',
        color = discord.Colour(0x000000)
    ))
    await asyncio.sleep(3)
    await kgb.close()

@kgb.command(description = 'Выводит шуточное сообщение о: \nУспешном/неуспешном взломе пользователя')
@helpCategory('fun')
async def hack(ctx, *, member):
    if isinstance(ctx.channel, discord.DMChannel): return
    
    await ctx.reply(embed = discord.Embed(
        title = 'Результат взлома:',
        description = f'{member} был успешно взломан!' if random.randint(1, 2) == 1 else 
                      f'{member} не был взломан!',
        color = discord.Color(0x000000)
    ))

@kgb.command(description = 'Гадальный шар')
@helpCategory('fun')
async def ball(ctx, *, question):
    if isinstance(ctx.channel, discord.DMChannel): return

    answers = ['Да', 'Может быть', 'Конечно', 'Я не знаю', 'Определённо **Нет**', 'Нет', 'Невозможно'] 
    await ctx.reply(embed = discord.Embed(
        title = f'Вопрос: {question}',
        description = f'Ответ: {random.choice(answers)}',
        color = discord.Color(0x000000)
    ))

@kgb.command(description = 'Бан пользователя')
@commands.has_permissions(ban_members=True)
@helpCategory('moderation')
async def ban(ctx, member: discord.Member, *, reason: typing.Union[str, None] = None):
    if isinstance(ctx.channel, discord.DMChannel): return

    if member == '1061907927880974406':
        await send_error_embed(ctx, 'Нет, сэр')
        return
      
    if member is None:
        await send_error_embed(ctx, 'Вы не указали кого нужно забанить!')
        return

    if not kgb.user or member.id == kgb.user.id:
        await send_error_embed(ctx, 'No, sir')
        return

    if member.top_role >= ctx.author.top_role:
        await send_error_embed(ctx, 'Вы не можете забанить пользователя т.к. он выше вас по роли')
        return

    await member.ban(reason=reason)
    await ctx.reply(embed=discord.Embed(
      title='Успешно:',
      description=f'Пользователь {member.name} был забанен',
      color=discord.Color(0x000000)
    ))

@kgb.command(description = 'Покажет всех забаненных пользователей этого сервера')
@commands.has_permissions(ban_members = True)
@helpCategory('moderation')
async def banlist(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    banned_users = ctx.guild.bans()
    banlist = [f'{ban_entry.user.name}#{ban_entry.user.discriminator}\n' async for ban_entry in banned_users]

    if banlist == []:
        await ctx.reply(embed=discord.Embed(
            title='Банлист:',
            description = 'На этом сервере нет забаненных пользователей.',
            color = discord.Color(0x000000)
        ))
        return

    await ctx.reply(embed=discord.Embed(
        title = 'Банлист:', 
        description = ' '.join(banlist), 
        color = discord.Color(0x000000)
    ))

@kgb.command(description = 'Разбан пользователя')
@commands.has_permissions(ban_members = True)
@helpCategory('moderation')
async def unban(ctx, *, member):
    if isinstance(ctx.channel, discord.DMChannel): return

    banned_users = ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    async for ban_entry in banned_users:
        user = ban_entry.user
    
        if (user.name, user.discriminator) != (member_name, member_discriminator): continue

        await ctx.guild.unban(user)
        await ctx.reply(embed = discord.Embed(
            title = 'Успешно:',
            description = f'Пользователь {user.name}#{user.discriminator} был разбанен',
            color = discord.Color(0x000000)
        ))
        break
      
@kgb.command(description = 'Удаляет сообщения')
@helpCategory('moderation')
async def clear(ctx, amount: int):
    if isinstance(ctx.channel, discord.DMChannel): return
    if not ctx.author.guild_permissions.administrator:
        await send_error_embed(ctx, 'Вы не имеете прав администратора!')
        return

    await ctx.channel.purge(limit = amount + 1)

    await ctx.reply(embed = discord.Embed(
        title = 'Успешно',
        description = f'Успешно удалено {amount} сообщений',
        color = discord.Color(0x000000)
    ))
    
@kgb.command(description = 'Кик пользователя')
@commands.has_permissions(kick_members=True)
@helpCategory('moderation')
async def kick(ctx, member: discord.Member, *, reason: typing.Union[str, None] =None):
    if isinstance(ctx.channel, discord.DMChannel): return

    if member.id == '1061907927880974406' or \
       not kgb.user or \
       member.id == kgb.user.id:
        await send_error_embed(ctx, 'Нет, сэр.')
        return

    if member.top_role >= ctx.author.top_role:
        await send_error_embed(ctx, 'Вы не можете кикнуть пользователя т.к. он выше вас по ролям.')
        return

    await member.kick(reason=reason)

    await ctx.reply(embed = discord.Embed(
        title = 'Успешно',
        description = f'Пользователь {member.name} был кикнут.',
        color = discord.Color(0x000000)
    ))
    
@kgb.command(description = 'Покажет список версий бота' )
@helpCategory('secret')
async def verlist(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    await ctx.reply(embed = discord.Embed(
        title = 'Список версий:',
        description = global_config.ver,
        color = discord.Color(0x000000)
    ))

@kgb.command(description = 'шифр')
@helpCategory('misc')
async def cipher(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    embed = discord.Embed(color=0x000000)
    embed.set_image(url=global_config.cipherURL)
    await ctx.author.send(embed=embed)

    black_embed = discord.Embed(color=0x000000, description='20-9-23-5')
    await ctx.author.send(embed=black_embed)
  
@kgb.command(description = 'Создаёт фейковый ютуб комментарий')
@helpCategory('api')
async def comment(ctx, *, commint: str):
    if isinstance(ctx.channel, discord.DMChannel): return

    comm = commint.replace('\n', ' ').replace('+', '%2B').replace(' ', '+')

    async with ctx.typing():
        async with aiohttp.ClientSession() as trigSession:
            async with trigSession.get(f'https://some-random-api.com/canvas/youtube-comment?avatar={ctx.author.avatar.url}&comment={(comm)}&username={ctx.author.name}') as trigImg:
                imageData = io.BytesIO(await trigImg.read())
                await trigSession.close()
                await ctx.reply(embed=discord.Embed(
                    title='Ваш коммент:',
                    description='',
                    color=discord.Color(0x000000)
                ).set_image(url='attachment://youtube_comment.gif'), file=discord.File(imageData, 'youtube_comment.gif'))

@kgb.command(description = 'Список благодарностей')
@helpCategory('misc')
async def thank(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    await ctx.reply(embed = discord.Embed(
        title = 'Я благодарен:',
        description = 
            'СВЗ(@svz_code_), за предоставленный обучающий материал!\n'
            'Грише(@grisshink), за помощь в разработке бота!\n'
            'Санечке(@demsanechka) за рисование аватара для бота',
        color = discord.Color(0xFFFF00)
    ))
  
@kgb.command(description = 'Даёт информацию о сервере')
@helpCategory('info')
async def server(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    guild = ctx.guild

    server_info = {
        'Участников:'              : guild.member_count,
        'Людей:'                   : len([member for member in guild.members if not member.bot]),
        'Ботов:'                   : len([member for member in guild.members if member.bot]),

        'Владелец сервера:'        : guild.owner,
        'Дата создания сервера:'   : guild.created_at.strftime('%d.%m.%Y %H:%M:%S'),

        'Всего текстовых каналов:' : len(guild.text_channels),
        'Всего войс каналов:'      : len(guild.voice_channels),

        'Регион сервера:'          : guild.preferred_locale,
    }

    embed = discord.Embed(title=f'Информация о сервере {guild.name}', color=0x000000)
    embed.set_thumbnail(url=guild.icon.url)

    for n, v in server_info.items(): 
        embed.add_field(name=n, value=v, inline=True)

    await ctx.reply(embed=embed)
  
@kgb.command(description=
    'Задает канал для приветствия пользователей\n'
    '(написать в канал куда будут отправляться приветствия)\n'
    'Если хотите выключить приветственное сообщение, \n'
    'То в качестве аргумета напишите: off'
)
@commands.has_permissions(administrator=True)
@helpCategory('config')
async def welcome(ctx, *, arg=None):
    if isinstance(ctx.channel, discord.DMChannel): return

    guild_id = str(ctx.guild.id)
    if arg == 'off':
        channels.pop(guild_id, None)

        with open('data/channels.json', 'w') as f:
            json.dump(channels, f)

        await ctx.reply(embed=discord.Embed(
            title='Приветствия выключены:',
            description='Теперь они больше не будут присылаться в этот канал.',
            color=discord.Color(0x000000)
        ))
        return

    channel_id = str(ctx.channel.id)
    channels[guild_id] = channel_id

    with open('data/channels.json', 'w') as f:
        json.dump(channels, f)

    await ctx.reply(embed=discord.Embed(
        title='Приветствия включены:',
        description=f'Приветственные сообщения теперь будут присылаться в этот канал: \n{ctx.channel.mention}',
        color=discord.Color(0x000000)
    ))
  
@kgb.command(description = 'Покажет аватар пользователя')
@helpCategory('info')
async def avatar(ctx: Context, userInp: typing.Union[discord.Member, None]=None):
    if isinstance(ctx.channel, discord.DMChannel): return
    if isinstance(ctx.author, discord.User): return

    if not userInp: userInp = ctx.author

    embed=discord.Embed(title=f'Аватар {no_format(userInp)}', color=userInp.color)
    if userInp.avatar:
        embed.set_image(url=userInp.avatar.url)

    await ctx.reply(embed=embed)
  
@kgb.command(description = 'Даёт информацию о пользователе')
@helpCategory('info')
async def user(ctx, member: discord.Member):
    if isinstance(ctx.channel, discord.DMChannel): return
    if not member.joined_at: return

    user_info = {
        'Статус:'                 : str(member.status),
        'Тэг:'                    : member.name + '#' + member.discriminator,

        'Дата создания аккаунта:' : member.created_at.strftime('%d.%m.%Y %H:%M:%S'),
        'Дата прихода на сервер:' : member.joined_at.strftime('%d.%m.%Y %H:%M:%S'),

        'Тип аккаунта:'           : 'Это аккаунт бота' if member.bot else 'Это аккаунт человека',
        'Роль на сервере:'        : 'Администратор сервера' if member.guild_permissions.administrator else 'Это не администратор сервера',

        'Айди:'                   : member.id,
    }

    embed = discord.Embed(title='Информация о пользователе:', color=0x000000)
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)

    for n,v in user_info.items():
        embed.add_field(name=n, value=v, inline=True)

    await ctx.reply(embed=embed)
  
@kgb.command(description = 'Подбросит монетку')
@helpCategory('fun')
async def coin(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    result = random.choice(['орёл', 'решка'])
    await ctx.reply(embed = discord.Embed(
        title = 'Результат:',
        description = f'Монетка показывает: **{result}**!',
        color = discord.Color(0x000000)
    ))
  
@kgb.command(description = 'Выдаст предупреждение пользователю')
@commands.has_permissions(administrator=True)
@helpCategory('moderation')
async def warn(ctx, member: discord.Member, count: int=1):
    if isinstance(ctx.channel, discord.DMChannel): return

    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
  
    if member.top_role >= ctx.author.top_role:
        await send_error_embed(ctx, 'Вы не можете выдать пользователю предупредение с большей или равной ролью, чем у вас.')
        return

    if user_id == '1061907927880974406':
        await send_error_embed(ctx, 'Нет, сэр')
        return

    with open('data/warn.json', 'r') as f:
        warns = json.load(f)

    if guild_id not in warns:
        warns[guild_id] = {}

    if user_id not in warns[guild_id]:
        warns[guild_id][user_id] = count
    else:
        warns[guild_id][user_id] += count

    total_warns = warns[guild_id][user_id]

    with open('data/stanwarns.json', 'r') as f:
        stanwarns = json.load(f)

    if guild_id not in stanwarns:
        await send_error_embed(ctx, 'Условия кика и/или бана не настроены.\nУстановите их с помощью команды:\n`kgb!configwarn`')
        return

    guild_stanwarns = stanwarns[guild_id]
    
    warn_type = guild_stanwarns.get('warn_type')
    warn_limit = guild_stanwarns.get('warn_limit')

    if total_warns >= warn_limit:
        if warn_type == 'kick':
            await member.kick()
            await ctx.reply(embed = discord.Embed(
                title = 'Кик:',
                description = f'{member.name} был кикнут. \nДостигнут лимит предупреждений: {total_warns}/{warn_limit}',
                color = discord.Color(0x000000)
            ))
            return

        if warn_type == 'ban':
            await member.ban(reason=f'Достигнут лимит предупреждений: {total_warns}/{warn_limit}')
            await ctx.reply(embed = discord.Embed(
                title = 'Бан:',
                description = f'{member.name} был забанен. \nДостигнут лимит предупреждений: {total_warns}/{warn_limit}',
                color = discord.Color(0x000000)
            ))

            del warns[guild_id][user_id]
            with open('data/warn.json', 'w') as f: 
                json.dump(warns, f)
            return

        await ctx.reply(embed=discord.Embed(
            title='Конуз:',
            description=f'Невозможно произвести кик или бан {member.name}, т.к. указан неверный тип в configwarn',
            color=discord.Color(0xFF0000)
        ))

    with open('data/warn.json', 'w') as f: 
        json.dump(warns, f)

    await ctx.reply(embed = discord.Embed(
        title = 'Выдано предупреждение:',
        description = f'{member.mention} получил {count} предупреждение,\nТеперь он имеет {total_warns} предупреждений на этом сервере.',
        color = discord.Color(0x000000)
    ))

@kgb.command(description = 'Снимет предупреждение пользователя')
@commands.has_permissions(administrator=True)
@helpCategory('moderation')
async def unwarn(ctx, member: discord.Member, count: int = 1):
    if isinstance(ctx.channel, discord.DMChannel): return

    guild = str(ctx.guild.id)
    user = str(member.id)
  
    if user == '1061907927880974406':
        await send_error_embed(ctx, 'Нет, сэр')
        return
      
    with open('data/stanwarns.json', 'r') as f:
        stanwarns = json.load(f)

    if guild not in stanwarns:
        await send_error_embed(ctx, 
            'Не установлены условия для предупреждений\n'
            'Установите с помощью команды:\n'
            '`kgb!configwarn`')
        return

    with open('data/warn.json', 'r') as f:
        warns = json.load(f)

    if guild not in warns       or \
       user  not in warns[guild]:
        await ctx.reply(embed=discord.Embed(
            title='Нет предупреждений:',
            description=f'У {member.mention} нет предупреждений на этом сервере.',
            color=discord.Color(0x000000)
        ))
        return

    if count > warns[guild][user]:
        await send_error_embed(ctx, f'У {member.mention} всего {warns[user][str(guild)]} предупреждений на этом сервере, вы не можете снять больше чем у него есть.')
        return

    warns[guild][user] -= count
    total_warns = warns[guild][user]

    with open('data/warn.json', 'w') as f:
        json.dump(warns, f)

    await ctx.reply(embed = discord.Embed(
        title = 'Снято предупреждени(е/и):',
        description = f'{count} предупреждений успешно снято у {member.mention}. \nОсталось {total_warns} предупреждени(й/я/е) на этом сервере.',
        color = discord.Color(0x000000)
    ))

@kgb.command(description = 'Покажет сколько предупреждений у пользователя')
@commands.has_permissions(administrator=True)
@helpCategory('moderation')
async def warnings(ctx, member: discord.Member):
    if isinstance(ctx.channel, discord.DMChannel): return

    guild = str(ctx.guild.id)
    user = str(member.id)
    
    if user == '1061907927880974406':
        await send_error_embed(ctx, 'Нет, сэр')
        return

    with open('data/warn.json', 'r') as f:
        warns = json.load(f)
    
    with open('data/stanwarns.json', 'r') as f:
        stanwarns = json.load(f)

    if guild not in stanwarns:
        await send_error_embed(ctx,
            'Не установлены условия для предупреждений\n'
            'Установите с помощью команды:\n'
            '`kgb!configwarn`')
        return

    if guild not in warns:
        await send_error_embed(ctx, 'На этом сервере не выдавалось никаких предупреждений')
        return

    if user not in warns[guild]:
        await send_error_embed(ctx, f'{member.display_name} не имеет предупреждений на этом сервере.')
        return

    total_warns = warns[guild][user]
    await ctx.reply(embed = discord.Embed(
        title = 'Всего предупреждений:',
        description = f'{member.display_name} имеет {total_warns} предупреждений на этом сервере.',
        color = discord.Color(0x000000)
    ))

@kgb.command(description = 'Установит лимит предупреждений и действия после него')
@commands.has_permissions(administrator=True)
@helpCategory('config')
async def configwarn(ctx, limit: int, warn_type: str):
    if isinstance(ctx.channel, discord.DMChannel): return

    guild_id = str(ctx.guild.id)

    with open('data/stanwarns.json', 'r') as f:
        stanwarns = json.load(f)

    if guild_id not in stanwarns:
        stanwarns[guild_id] = {}

    if warn_type.lower() == 'kick':
        stanwarns[guild_id]['warn_type'] = 'kick'
        stanwarns[guild_id]['warn_limit'] = limit
    elif warn_type.lower() == 'ban':
        stanwarns[guild_id]['warn_type'] = 'ban'
        stanwarns[guild_id]['warn_limit'] = limit
    else:
        await send_error_embed(ctx, 'Неверный тип предупреждения. Доступны "kick" и "ban".')
        return

    with open('data/stanwarns.json', 'w') as f:
        json.dump(stanwarns, f)

    await ctx.reply(embed = discord.Embed(
        title = 'Действие и лимит установлен:',
        description = f'Для сервера {ctx.guild.name} установлено {warn_type} при {limit} предупреждениях.',
        color = discord.Color(0x000000)
    ))

@kgb.command(description='Ищет пользователей по их примерному нику на всех серверах, где присутствует бот')
@helpCategory('info')
async def seek_user(ctx, *, query):
    if isinstance(ctx.channel, discord.DMChannel): return

    users_found = {m.name 
                   for g in kgb.guilds 
                   for m in g.members
                   if query.lower() in m.display_name.lower() or \
                      query.lower() in m.name.lower()}

    if not users_found:
        await send_error_embed(ctx, f'Не могу найти пользователя по запросу "{query}"')
        return

    message = '\n'.join(users_found)
    users_count = f'Найдено пользователей: {len(users_found)}'

    await ctx.reply(embed=discord.Embed(
        title='Найденные пользователи:',
        description=f'{message}\n\n{users_count}',
        color=discord.Color(0x000000)
    ))

@kgb.command(description='Ищет сервер, на котором находится пользователь по его точному нику, на всех серверах где присутствует бот ')
@helpCategory('info')
async def seek_server(ctx, *, user_name):
    if isinstance(ctx.channel, discord.DMChannel): return

    #guild_seek = None
    with open(GUILD_SEEK_FILENAME, 'r', encoding='utf-8') as f:
        guild_seek = json.load(f)

    found_servers = {kgb.get_guild(int(g_id))
                     for g_id, g_info in guild_seek.items()
                     for u in g_info['users']
                     if user_name.lower() == u['name'].lower()}

    found_servers = {v.name for v in found_servers if v}

    if not found_servers:
        await send_error_embed(ctx, f'Не могу найти сервер, на котором находится пользователь {user_name}')
        return

    message = '\n'.join(found_servers)
    message_count = f'Всего найдено серверов: {len(found_servers)}'

    await ctx.reply(embed=discord.Embed(
        title='Вот сервера на которых есть пользователь:',
        description=f'{message}\n\n{message_count}',
        color=discord.Color(0x000000)
    ))
      
@kgb.command(description = 'Покажет пинг бота')
@helpCategory('misc')
async def ping(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    latency = kgb.latency
    await ctx.reply(embed=discord.Embed(
        title='Понг!',
        description=f'Скорость: {latency*1000:.2f} мс',
        color=discord.Color(0x000000)
    ))

@kgb.command(description='Выведет рандомное число')
@helpCategory('fun')
async def rand(ctx, num1: int, num2: typing.Union[int, None]=None):
    if isinstance(ctx.channel, discord.DMChannel): return

    if not num2:
        num1, num2 = 0, num1

    if num1 > num2:
        num2, num1 = num1, num2

    result = random.randint(num1, num2)

    await ctx.reply(embed=discord.Embed(
        title='Результат:',
        description=result,
        color=discord.Color(0x000000)
    ))

@kgb.command(description='Ищет статью на вики')
@helpCategory('api')
async def wiki(ctx, *, query):
    if isinstance(ctx.channel, discord.DMChannel): return

    wikipedia.set_lang('ru')

    try:
        page = wikipedia.page(query)
        await ctx.reply(embed=discord.Embed(
            title='Найдена страница',
            description=page.url,
            color=discord.Color(0x000000)
        ))
    except wikipedia.exceptions.PageError:
        await send_error_embed(ctx, f'Страница на Википедии не найдена для "{query}"')
    except wikipedia.exceptions.DisambiguationError:
        await send_error_embed(ctx, f'Слишком много результатов для "{query}". Пожалуйста, уточните свой запрос.')

@kgb.command(description = ')')
@helpCategory('secret')
async def hentai(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    await ctx.reply(embed = discord.Embed(
        title = 'Не-а)',
        description = 'Эй, школьник! Домашку сделай, а потом др*чи)',
        color = discord.Color(0xFF0000)
    ))

@kgb.command(description='Поцеловать участника')
@helpCategory('rp')
async def kiss(ctx, member: discord.Member):
    if isinstance(ctx.channel, discord.DMChannel): return

    await ctx.reply(f'{ctx.author.mention} поцеловал(а) {member.mention}')

@kgb.command(description='Ударить участника')
@helpCategory('rp')
async def hit(ctx, member: discord.Member):
    if isinstance(ctx.channel, discord.DMChannel): return

    await ctx.reply(f'{ctx.author.mention} ударил(а) {member.mention}')

@kgb.command(description='Лизнуть участника')
@helpCategory('rp')
async def lick(ctx, member: discord.Member):
    if isinstance(ctx.channel, discord.DMChannel): return

    await ctx.reply(f'{ctx.author.mention} лизнул(а) {member.mention}')

@kgb.command(description='Поприветствовать участника')
@helpCategory('rp')
async def hi(ctx, member: discord.Member):
    if isinstance(ctx.channel, discord.DMChannel): return

    await ctx.reply(f'{ctx.author.mention} поприветствовал(а) {member.mention}')

async def rpImage(ctx, user: discord.Member, url: str) -> None:
    if isinstance(ctx.channel, discord.DMChannel): return

    data = requests.get(url).json()
    image_url = data['link']

    embed = discord.Embed(
        description = f'{ctx.author.mention} обнял(a) {user.mention}',
        color=0x000000
    )
    embed.set_image(url=image_url)

    await ctx.reply(embed=embed)

@kgb.command(description='Обнять участника')
@helpCategory('rp')
async def hug(ctx, member: discord.Member):
    await rpImage(ctx, member, 'https://some-random-api.com/animu/hug')

@kgb.command(description='Погладить участника')
@helpCategory('rp')
async def pet(ctx, member: discord.Member):
    await rpImage(ctx, member, 'https://some-random-api.com/animu/pat')

@kgb.command(description='Вызывает голосование в канале\n(принимает длительность голосования только в часах)' )
@helpCategory('moderation')
async def poll(ctx, hours: int, *, text: str):
    if isinstance(ctx.channel, discord.DMChannel): return
    
    end_time = datetime.utcnow() + timedelta(hours=hours)
    end_time_msk = end_time + timedelta(hours=3)
    end_time_str = end_time_msk.strftime('%H:%M:%S')
    
    await ctx.message.delete()

    embedVar = discord.Embed(
        title=f'Голосование от {ctx.author.name}', 
        description=f'{text}\n\n🔼 - Да\n🔽 - Нет\n\nГолосование закончится в {end_time_str} по МСК',
        color=0x000000
    )

    msgp = await ctx.reply(embed=embedVar)

    await msgp.add_reaction('🔼')
    await msgp.add_reaction('🔽')
    
    while datetime.utcnow() < end_time:
        await asyncio.sleep(1)
    
    msgp = await msgp.channel.fetch_message(msgp.id)

    results = msgp.reactions
    yes_votes = results[0].count - 1
    no_votes = results[1].count - 1

    embedVar = discord.Embed(
      title='Голосование завершено!', 
      description=f'{text}\n\n🔼 - Да ({yes_votes})\n🔽 - Нет ({no_votes})', 
      color=0x000000
    )
    await msgp.edit(embed=embedVar)

@kgb.command(description='Пишет информацию о категории\n(указывайте айди категории или её пинг')
@helpCategory('info')
async def category(ctx, category: discord.CategoryChannel):
    if isinstance(ctx.channel, discord.DMChannel): return

    category_info = {
        'Имя:'                : category.name,
        'Создана:'            : category.created_at.strftime('%d.%m.%Y %H:%M:%S'),
        'ID:'                 : category.id,
        'Позиция:'            : category.position,
        'Количество каналов:' : len(channels),
    }

    em = discord.Embed(title='Информация о категории:', color=0x000000)
    em.set_thumbnail(url=ctx.guild.icon.url)

    for n,v in category_info.items():
        em.add_field(name=n, value=v, inline=False)

    await ctx.reply(embed=em)
  
@kgb.command(description='Пишет информацию о канале\n(указывайте айди канала или его пинг)')
@helpCategory('info')
async def channel(ctx, channel: typing.Optional[discord.TextChannel]):
    if isinstance(ctx.channel, discord.DMChannel): return

    channel = channel or ctx.channel

    channel_info = {
        'Имя:': channel.name,
        'Топик:': channel.topic or 'Нет топика.',
        'Категория:': channel.category.name if channel.category else 'Нет категории',
        'Позиция:': channel.position,
        'NSFW:': 'Да' if channel.is_nsfw() else 'Нет',
        'Слоумод:': channel.slowmode_delay,
        'Тип канала:': str(channel.type).capitalize(),
        'Создан:': channel.created_at.strftime('%d.%m.%Y %H:%M:%S'),
    }

    em = discord.Embed(title='Информация о канале:', color=0x000000)
    em.set_thumbnail(url=ctx.guild.icon.url)

    for n,v in channel_info.items():
        em.add_field(name=n, value=v, inline=False)

    await ctx.reply(embed=em)
  
@kgb.command(description='Пишет информацию о роли\n(указывайте айди роли или её пинг' )
@helpCategory('info')
async def role(ctx, *, role: discord.Role):
    if isinstance(ctx.channel, discord.DMChannel): return

    role_info = {
        'Имя:': role.name,
        'ID:': role.id,
        'Создана:': role.created_at.strftime('%d.%m.%Y %H:%M:%S'),
        'Участников с этой ролью:': len(role.members),
        'Позиция:': role.position,
        'Показывается ли она отдельно:': role.hoist,
    }

    em = discord.Embed(title='Информация о роли:', color=0x000000)
    em.set_thumbnail(url=ctx.guild.icon.url)

    for n,v in role_info.items():
        em.add_field(name=n, value=v, inline=False)

    await ctx.reply(embed=em)

@kgb.command(description='Выдаст рандомную цитату')
@helpCategory('fun')
async def quote(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    fortun = fortune.get_random_fortune('static_data/fortune')
    await ctx.reply(f'```{fortun}```')

@kgb.command(description='Выдаст рандомную шутку про Штирлица')
@helpCategory('fun')
async def shtr(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    shtr = fortune.get_random_fortune('static_data/shtirlitz')
    await ctx.reply(f'```{shtr}```')

@kgb.command(description='0x00000000')
@helpCategory('secret')
async def null(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    embed = discord.Embed(title='NULL OF PROJECT', color=0x00000000)
    embed.set_image(url=global_config.secretURL)

    await ctx.reply(embed=embed)

@kgb.command(description='Хорни карта')
@helpCategory('api')
async def horny(ctx, member: typing.Union[discord.Member, None] = None):
    if isinstance(ctx.channel, discord.DMChannel): return

    member = member or ctx.author
    if not member.avatar: return

    async with ctx.typing():
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://some-random-api.com/canvas/horny?avatar={member.avatar.url}') as af:
                if 300 > af.status >= 200:
                    fp = io.BytesIO(await af.read())
                    file = discord.File(fp, 'horny.png')
                    em = discord.Embed(
                        color=0xFFC0CB,
                    )
                    em.set_image(url='attachment://horny.png')
                    await ctx.reply(embed=em, file=file)
                else:
                    await ctx.reply('No horny :(')
                await session.close()

@kgb.command(description='hello comrade!')
@helpCategory('api')
async def comrade(ctx, member: typing.Union[discord.Member, None] = None):
    if isinstance(ctx.channel, discord.DMChannel): return

    member = member or ctx.author
    if not member.avatar: return

    async with ctx.typing():
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://some-random-api.com/canvas/overlay/comrade?avatar={member.avatar.url}') as af:
                if 300 > af.status >= 200:
                    fp = io.BytesIO(await af.read())
                    file = discord.File(fp, 'comrade.png')
                    em = discord.Embed(
                      color=0xff0000,
                    )
                    em.set_image(url='attachment://comrade.png')
                    await ctx.reply(embed=em, file=file)
                else:
                    await ctx.reply('No horny :(')
                await session.close()

@kgb.command(description='Взлом пентагона')
@helpCategory('fun')
async def hack_pentagon(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    progress = 0
    while progress < 100:
        await ctx.reply(f'Pentagon hack progress: {progress}%')
        time.sleep(1)
        progress += random.randint(1, 10)

    await ctx.reply('Pentagon hack progress: 100%')
    time.sleep(1.5)

    if random.randint(1, 30) > 20:
        await ctx.reply('Pentagon hack: Completed successfully.')
    else:
        await ctx.reply('Pentagon hack: Failed.')

@kgb.command(description='Не может проигрывать музыку с ютуба\nМожет проигрывать только прямые ссылки на аудиофайлы')
@helpCategory('music')
async def playaudio(ctx, url):
    if isinstance(ctx.channel, discord.DMChannel): return

    if not ctx.author.voice:
        await send_error_embed(ctx, 'Вы должны быть подключены к голосовому каналу, чтобы воспроизвести музыку.')
        return

    channel = ctx.author.voice.channel
    voice_client = await channel.connect()

    try: 
        voice_client.play(discord.FFmpegPCMAudio(
            url, 
            options='-vn', 
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        ))
    except: pass

    while voice_client.is_playing():
        await asyncio.sleep(1)

    await asyncio.sleep(5)
    await voice_client.disconnect()

@kgb.command(description='Может проигрывать музыку только с ютуба')
@helpCategory('music')
async def play(ctx, url):
    if isinstance(ctx.channel, discord.DMChannel): return

    if not ctx.author.voice:
        await send_error_embed(ctx, 'Вы должны быть подключены к голосовому каналу, чтобы воспроизвести музыку.')
        return

    voice_channel = ctx.author.voice.channel
    voice_client = await voice_channel.connect()

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                await send_error_embed(ctx, 'Произошла ошибка получения данных о музыке. Проверьте правильность ввода ссылки')
                return
            for format in info['formats']:
                if format['audio_ext'] == 'none': continue
                voice_client.play(discord.FFmpegPCMAudio(format['url']))
                break

        await ctx.reply(f'Проигрывается музыка в канале {voice_channel}.')

        while voice_client.is_playing():
            await asyncio.sleep(1)
    except: pass

    await asyncio.sleep(5)
    await voice_client.disconnect()

@kgb.command(description='Выгоняет бота из войс канала')
@helpCategory('music')
async def leave(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return
    if not ctx.voice_client:
        await send_error_embed(ctx, 'Бот должен быть подключён к голосовому каналу, чтобы выйти')
        return

    await ctx.voice_client.disconnect()

@kgb.command(description='Вышлет вам код дискорд бота "SudoBot"')
@helpCategory('misc')
async def code(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    file = discord.File('static_data/sudocode.py')
    await ctx.reply(file=file)

@kgb.command(description=
    'Введите эту команду в тот канал куда вы хотите получать новости.\n'
    'Напишите в качестве агрумента "Off" если хотите отписаться от новостей.'
)
@helpCategory('config')
async def sub(ctx, publisher: str, off: typing.Union[str, None] = None):
    if isinstance(ctx.channel, discord.DMChannel): return

    def getPublishers() -> str:
        out = ''
        for pub in RETR_PUBLISHERS.keys(): out += f'`{pub}`, '
        return out

    if publisher not in RETR_PUBLISHERS:
        await send_error_embed(ctx, f'Неверное имя публикатора! Доступные имена: {getPublishers()}')
        return

    pub = RETR_PUBLISHERS[publisher]

    if off == 'off':
        if not pub.unsubscribe(ctx.channel.id):
            await send_error_embed(ctx, f'Данный канал не находится в списке подписок у публикатора `{publisher}`!')
            return
        await ctx.reply(f'Канал {ctx.channel.mention} удален из списка у публикатора `{publisher}`.')
        return
    
    if not pub.subscribe(ctx.channel.id):
        await send_error_embed(ctx, f'Данный канал уже есть в списке подписок у публикатора `{publisher}`!')
        return

    await ctx.reply(f'Канал {ctx.channel.mention} добавлен в список у публикатора `{publisher}`.')

@kgb.command(description='Выводит всю информацию о скрэтч-пользователе')
@helpCategory('scratch')
async def scratch_user(ctx, username):
    if isinstance(ctx.channel, discord.DMChannel): return

    base_url = 'https://api.scratch.mit.edu/users/'
    url = base_url + username

    try:
        data = requests.get(url).json()
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return

    if 'username' not in data:
        await send_error_embed(ctx, f'Пользователь с именем `{username}` не найден')
        return

    user_info = {
        'Страна:'                 : data['profile']['country'],
        'Обо мне:'                : data['profile']['bio'],
        'Над чем я работаю'       : data['profile']['status'],
        'Дата создания аккаунта:' : data['history']['joined'],
    }

    embed = discord.Embed(
        title=f'Информация о пользователе {username}',
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url=data['profile']['images']['90x90']) 
    embed.set_footer(text=f'ID: {data["id"]}')  

    for n,v in user_info.items():
        embed.add_field(name=n, value=v, inline=False)

    await ctx.reply(embed=embed)

@kgb.command(description='Нейросеть которая рисует несуществующих людей')
@helpCategory('neuro')
async def person(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    response = requests.get('https://thispersondoesnotexist.com')
    await ctx.reply(file=discord.File(io.BytesIO(response.content), 'generated_image.jpg'))

@kgb.command(description='Интересное о Космосе')
@helpCategory('api')
async def nasa(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    url = 'https://api.nasa.gov/planetary/apod'
    params = {
        'api_key': global_config.nasaKEY
    }
    data = requests.get(url, params=params).json()

    embed = discord.Embed(title=data['title'], description=data['explanation'], color=discord.Color.dark_blue())
    embed.set_image(url=data['url'])

    await ctx.reply(embed=embed)

@kgb.command(description='Генератор оскарблений')
@helpCategory('api')
async def insult(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    data = requests.get('https://evilinsult.com/generate_insult.php?lang=ru&type=json').json()

    await ctx.reply(embed = discord.Embed(
          title = data['insult'],
          color = discord.Color(0x000000)
    ))

@kgb.command(description='Генератор бреда Порфирьевич')
@helpCategory('neuro')
async def porfir(ctx, *, prompt):
    if isinstance(ctx.channel, discord.DMChannel): return
    
    async with ctx.typing():
        api_url = 'https://pelevin.gpt.dobro.ai/generate/'
        data = {
            'prompt': prompt,
            'length': random.randint(20, 60)
        }
        try:
            response = requests.post(api_url, json=data, timeout=30)
        except requests.ConnectTimeout:
            await send_error_embed(ctx, 'Превышено время ожидания')
            return

        if response.status_code == 500:
            await ctx.reply(f'Нейросеть отключена, невозможно предположить время её включения.')
            return

        if response.status_code != 200:
            await ctx.reply(f'Произошла ошибка при получении данных от API Профирьевича. Код ошибки: {response.status_code}')
            return

        data = response.json()
        generated_text = data['replies'][0]
        await ctx.reply(f'```\n{prompt}{generated_text}\n```')

@kgb.command(description = 'Перезапускает бота(только для разработчика)')
@helpCategory('secret')
async def reload(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    if ctx.author.id != 745674921774153799 and ctx.author.id != 999606704541020200:
        await send_error_embed(ctx, 'Эта команда только для разработчиков!')
        return

    await ctx.reply(embed = discord.Embed(
        title = 'Пожалуйста подождите:',
        description = 'Бот перезагрузится через 3 секунды!',
        color = discord.Colour(0x000000)
    ))
    await asyncio.sleep(3)
    exit(1)

@kgb.command(description=
    'Генерирует текст как гена.\n'
    'Для того, чтобы бот работал в данном канале,\n'
    'Пропишите: kgb!genconfig read true'
)
@helpCategory('neuro')
async def gen(ctx, *args: str):
    if isinstance(ctx.channel, discord.DMChannel): return

    channelId = str(ctx.channel.id)
    if channelId not in genAiArray or not genAiArray[channelId].config['read']:
        await send_error_embed(ctx, 'Бот не может читать сообщения с этого канала! Включите это через команду `kgb!genconfig read true`!')
        return
    
    try:
        await ctx.reply(genAiArray[channelId].generate(' '.join(args)[:2000]))
    except ValueError as exc:
        await send_error_embed(ctx, str(exc))

@kgb.command(description=
    'Настраивает поведение команды kgb!gen в данном канале.\n'
    'Введите имя опции без значения, чтобы посмотреть её текущее значение.\n'

    'Доступные опции:\n'
    '`read true/false` - Позволяет боту сохранять сообщения и картинки для генерации\n'
    '`reply_on_mention true/false` - Позволяет боту генерировать текст если ответить на его сообщение\n'
    '`remove_mentions true/false` - Не позволяет упоминать участников в сгенерированном тексте'
)
@helpCategory('config')
async def genconfig(ctx, option: str, *, value: typing.Union[str, None] = None):
    if isinstance(ctx.channel, discord.DMChannel): return

    optionKeys = f''.join([f'`{key}` ' for key in markov.DEFAULT_CONFIG])

    def strToBool(inp: str) -> bool: return inp.lower() == 'true'
    
    channelId = str(ctx.channel.id)

    if channelId not in genAiArray:
        if value: genAiArray[channelId] = markov.MarkovGen()
        else:
            if option not in markov.DEFAULT_CONFIG:
                await send_error_embed(ctx, f'Неизвестное значение `{option}`! \nДоступные значения: {optionKeys}`')
                return

            await ctx.reply(embed=discord.Embed(
                title='Инфо',
                description=f'Значение `{option}` равно `{markov.DEFAULT_CONFIG[option]}`',
                color=discord.Colour(0x000000)
            ))
            return

    genAi = genAiArray[channelId]

    if option not in genAi.config:
        await send_error_embed(ctx, f'Неизвестное значение `{option}`! \nПожалуйста, пропишите команду:\n`kgb!help genconfig`')
        return

    if value:
        genAi.config[option] = strToBool(value)
        await ctx.reply(embed=discord.Embed(
            title='Успешно',
            description=f'Значение `{option}` было установлено в `{genAi.config[option]}`',
            color=discord.Colour(0x000000)
        ))
        return

    await ctx.reply(embed=discord.Embed(
        title='Инфо',
        description=f'Значение `{option}` равно `{genAi.config[option]}`',
        color=discord.Colour(0x000000)
    ))

@kgb.command(description='Удаляет все сообщения из базы генерации')
@helpCategory('config')
async def genclear(ctx):
    if isinstance(ctx.channel, discord.DMChannel): return

    if str(ctx.channel.id) in genAiArray:
        del genAiArray[str(ctx.channel.id)]

    await ctx.reply(embed=discord.Embed(
        title='Успешно!',
        description='Все данные команды kgb!gen очищены в этом канале!',
        color=discord.Colour(0x000000)
    ))

@kgb.command(description='Выводит факты о числах(на англиском).\nДоступные типы фактов:\n`math` `date` `year` `trivia`')
@helpCategory('api')
async def factnumber(ctx, number: int, fact_type: str):
    if isinstance(ctx.channel, discord.DMChannel): return

    valid_fact_types = ['trivia', 'math', 'date', 'year']
    if fact_type not in valid_fact_types:
        await send_error_embed(ctx, 'Пожалуйста, введите корректный тип факта.')
        return

    url = f'http://numbersapi.com/{number}/{fact_type}?lang=ru'
    response = requests.get(url)

    if response.status_code != 200:
        await send_error_embed(ctx, f'Извините, не удалось получить факт о числе {number}.')
        return

    fact_text = response.text
    await ctx.reply(embed=discord.Embed(
        title='Факт о числе:',
        description=fact_text,
        color=discord.Colour(0x000000)
    ))

@kgb.command(description='Покажет всю информацию о боте')
@helpCategory('info')
async def bot_info(ctx):
    if isinstance(ctx.channel, discord.DMChannel) or kgb.user is None:
        return
    total_commands = len(kgb.commands)
    embed = discord.Embed(title='Информация о боте:', 
                          description=
                          'КГБ - Комитет Государственной Безопасности\n'
                          'Напишите kgb!help чтобы увидеть полный список команд\n'
                          'Бот очень активно разрабатывается, \n'
                          'Поэтому может падать несколько раз в день. \n'
                          f'{kgb.user.name} находится на {len(kgb.guilds)} серверах и имеет {total_commands} команд', 
                          color=discord.Color(0x000000))
    embed.add_field(name='Версия:', value='3.0', inline=False)
    embed.add_field(name='Полезные ссылки:', 
                    value=f'[Добавить {kgb.user.name} на свой сервер]({global_config.botURL})\n'
                    f'[Присоединится к серверу бота]({global_config.serverURL})\n'
                    f'[Поддержать бота на бусти]({global_config.boostyURL})\n'
                    f'Зайти на [сайт]({global_config.siteURL}) компании', 
                    inline=False
                   )
    embed.set_thumbnail(url=global_config.tumbaYUMBA)
    embed.set_footer(text='© 2023 Soviet WorkShop', icon_url=global_config.avaURL)
    await ctx.reply(embed=embed)

@kgb.command(desciption='Выполняет код языка Hellya')
@helpCategory('neuro')
async def execute(ctx, *, code=None):
    user_id = ctx.author.id

    if user_id in last_command_time:
        current_time = time.time()
        last_time = last_command_time[user_id]
        if current_time - last_time < 15:
            await send_error_embed(ctx, f'Подождите еще {15 - (current_time - last_time):.1f} секунд')
            return
            
    if not code and not ctx.message.attachments:
        await send_error_embed(ctx, 'Вы должны прикрепить файл с кодом или ввести код в сообщении.')
        return

    if not code and ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.filename.endswith('.hellya'):
            code = (await attachment.read()).decode('utf-8')
        else:
            await send_error_embed(ctx, 'Пожалуйста, прикрепите текстовый файл с кодом.')
            return

    result = execute_code(code)
    if result == 'Код успешно выполнен.':
        try:
            with open('result.png', 'rb') as file:
                result_image = discord.File(file)
                await ctx.reply(result)
                await ctx.reply(file=result_image)
                os.remove('result.png')
            last_command_time[user_id] = time.time()
        except FileNotFoundError:
            await send_error_embed(ctx, 'Ваш код не сохраняет картинку, либо не создаёт её')
            last_command_time[user_id] = time.time()
    else:
        await send_error_embed(ctx, result)
        last_command_time[user_id] = time.time()

@kgb.command(description='Подробный хелп по команде execute')
@helpCategory('info')
async def help_execute(ctx):
    file = discord.File('static_data/help.txt')
    await ctx.reply(file=file)

@kgb.command(description='Показывает курс криптовалют по отношению к рублю')
@helpCategory('info')
async def price(ctx, arg=None):
    api_key = "CG-XV44NHn7td9m52kmCLcaxCe4"
    
    symbols = {
        "monero": "monero",
        "dogecoin": "dogecoin",
        "ethereum": "ethereum",
        "bitcoin": "bitcoin",
        "zephyr": "zephyr-protocol",
        "tether": "tether"
    }
    
    if arg is None:
        embed = discord.Embed(
            title='Список криптовалют:', 
            description=
            '1. Монеро (Monero)'
            '\n2. Зефир (Zephyr Protocol)'
            '\n3. Тевер (Tether)'
            '\n4. Догикоин (Dogecoin)'
            '\n5. Эфириум (Ethereum)'
            '\n6. Биткоин (Bitcoin)\n'
            '\nЧто бы узнать курс криптовалюты напишите:'
            '\nkgb!price (название валюты на англ. со строчной буквы)'
            , color=discord.Color(0x000000)
        )
    else:
        symbol = symbols.get(arg.lower())
        if symbol is None:
            await send_error_embed(ctx, "Криптовалюта не найдена")
            return
        
        crypto_price = get_crypto_price(symbol, api_key)
        if crypto_price is not None:
            embed = discord.Embed(title=f"Курс {arg.capitalize()} к рублю", description=f"₽{crypto_price}", color=get_embed_color(arg.lower()))
        else:
            embed = send_error_embed(ctx, f"Не удалось получить курс валюты {arg.capitalize()}.")
    
    await ctx.send(embed=embed)

HELP_EMB = buildHelpEmbed()
HELP_CAT_EMB, HELP_CAT_HIDDEN = buildCategoryEmbeds()
kgb.run(getenv('DISCORD_TOKEN', ''))
