import discord
from discord.ext import commands
import random
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DICTIONARY_FILEPATH = os.getenv("DICTIONARY_FILEPATH")

current_dir = os.path.dirname(os.path.abspath(__file__))
dictionary_path = os.path.join(current_dir, DICTIONARY_FILEPATH)

bot = commands.Bot(command_prefix="*", intents=discord.Intents.all())
bot.remove_command('help')

valid_6 = set()
valid_7 = set()
with open(dictionary_path, 'r') as f:
    for line in f:
        word = line.strip().lower()
        if len(word) == 6:
            valid_6.add(word)
        elif len(word) == 7:
            valid_7.add(word)

@bot.event
async def on_ready():
    print('Bananagrams is now online!')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Help", description="I am Anagrams!", color=0xFFE135)
    embed.add_field(name= "", value="List of commands:")
    embed.add_field(name="*anagrams 6", value="Plays anagrams with a random 6-letter word", inline=False)
    embed.add_field(name="*anagrams 7", value="Plays anagrams with a random 7-letter word", inline=False)
    embed.add_field(name="*anagrams <word>", value="Plays anagrams with a given word", inline=False)
    embed.add_field(name="*letters", value="Shows the current game's original letters", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def letters(ctx):
    if ctx.channel.id in current_game_info:
        info = current_game_info[ctx.channel.id]
        await ctx.send(f"🎯 **Current Game Info:**\n"
                       f"**Scrambled:** `{info['scrambled']}`\n"
                       f"**Time remaining:** {info['time_left']} seconds")
    else:
        await ctx.send("No active game in this channel. Start one with `*anagrams`!")

current_game_info = {}

@bot.command()
async def anagrams(ctx, word=None):
    if word == "6":
        await anagram_run(ctx, random.choice(list(valid_6)))
    elif word == "7":
        await anagram_run(ctx, random.choice(list(valid_7)))
    elif word is None:
        await ctx.send("No given anagram. Type *help for a list of commands")
    elif not valid_word(word):
        await ctx.send(word + " is not a valid word. Type *help for a list of commands")
    elif len(word) < 3:
        await ctx.send(word + " is too short! Please make your word 3 letters or more")
    else:
        await anagram_run(ctx, word)

def contains_same_letters(word1, word2):
    for letter in word2:
        if letter not in word1:
            return False
        word1 = word1.replace(letter, '', 1)
    return True

def valid_word(word):
    word_lower = word.lower()
    with open(dictionary_path, 'r') as f:
        for line in f:
            if word_lower == line.strip().lower():
                return True
    return False

def create_anagrams_table(words_list, title):
    if not words_list:
        if title:
            return f"**{title}**\nNo words to display."
        else:
            return "No words to display."
    
    table = "```\n"
    table += f"{'Length':<6} {'Count':<6} {'Words':<50}\n"
    table += "-" * 62 + "\n"
    
    for length in range(max(len(word) for word in words_list), 2, -1):
        words_of_length = [word for word in words_list if len(word) == length]
        if words_of_length:
            words_str = ', '.join(words_of_length)
            if len(words_str) > 50:
                words_list_split = words_of_length
                chunks = []
                current_chunk = []
                current_length = 0
                
                for word in words_list_split:
                    if current_length + len(word) + 2 <= 50:
                        current_chunk.append(word)
                        current_length += len(word) + 2
                    else:
                        if current_chunk:
                            chunks.append(', '.join(current_chunk))
                        current_chunk = [word]
                        current_length = len(word)
                
                if current_chunk:
                    chunks.append(', '.join(current_chunk))
                
                table += f"{length:<6} {len(words_of_length):<6} {chunks[0]:<50}\n"
                for chunk in chunks[1:]:
                    table += f"{'':<6} {'':<6} {chunk:<50}\n"
            else:
                table += f"{length:<6} {len(words_of_length):<6} {words_str:<50}\n"
    
    table += "```"
    if title:
        return f"**{title}**\n{table}"
    else:
        return table

async def anagram_run(ctx, word):
    scramble = "".join(random.sample(word, len(word)))
    user = ctx.author
    anagrams = set()
    with open(dictionary_path, 'r') as f:
        for line in f:
            word_check = line.strip().lower()
            if contains_same_letters(word, word_check) and len(word_check) >= 3:
                anagrams.add(word_check)
    
    completed_anagrams = set()

    await ctx.send(f"🎯 **ANAGRAMS GAME STARTED!** 🎯\n"
                   f"**Scrambled:** `{scramble}`\n"
                   f"**Time:** 60 seconds\n\n"
                   f"**Type your anagrams now!**")
    
    current_game_info[ctx.channel.id] = {
        'scrambled': scramble,
        'time_left': 60
    }
    points = 0

    timer_expired = [False]
    timer_task = bot.loop.create_task(timer(ctx, timer_expired))

    while not timer_expired[0]:
        if len(anagrams) == 0:
            break
        msg = await bot.wait_for('message', check=lambda m: m.author == user)
        if msg.content == '*quit':
            await ctx.send("Exiting")
            break
        elif msg.content.lower() in anagrams:
            if len(msg.content) == 3:
                points += 100
                await ctx.send("+ 100")
            elif len(msg.content) == 4:
                points += 400
                await ctx.send("+ 400")
            elif len(msg.content) == 5:
                points += 1200
                await ctx.send("+ 1200")
            elif len(msg.content) == 6:
                points += 2000
                await ctx.send("+ 2000")
            else:
                points += (len(msg.content) - 6) * 1000 + 2000
                await ctx.send("+ " + str((len(msg.content) - 6) * 1000 + 2000))
            #await msg.add_reaction('👍')
            anagrams.remove(msg.content.lower())
            completed_anagrams.add(msg.content.lower())
        elif msg.content.lower() in completed_anagrams:
            await ctx.send(msg.content + " (Already used)")
        elif len(msg.content) < 3:
            await ctx.send("(Words must be at least 3 letters long)")
        else:
            await ctx.send(msg.content + " (Not in vocabulary)")

    timer_task.cancel()
    sorted_anagrams = sorted(anagrams, key=lambda x: (-len(x), x))
    sorted_completed = sorted(completed_anagrams, key=lambda x: (-len(x), x))
    
    await ctx.send(f"**Total points: {points:,}**")
    
    completed_count = len(sorted_completed)
    await ctx.send(f"**✅ You found {completed_count} anagram{'s' if completed_count != 1 else ''}:**")
    
    if completed_count > 0:
        completed_table = create_anagrams_table(sorted_completed, None)
        await ctx.send(completed_table)
    
    if len(sorted_anagrams) == 0:
        await ctx.send("**You got every anagram! I'm so proud of you!**")
    else:
        missed_count = len(sorted_anagrams)
        missed_table = create_anagrams_table(sorted_anagrams, f"❌ You missed {missed_count} anagram{'s' if missed_count != 1 else ''}")
        await ctx.send(missed_table)
    
async def timer(ctx, timer_expired):
    await bot.wait_until_ready()

    await asyncio.sleep(30)
    
    if ctx.channel.id in current_game_info:
        current_game_info[ctx.channel.id]['time_left'] = 30
        await ctx.send("**⏰ 30 seconds remaining!**")
    
    await asyncio.sleep(20)
    
    if ctx.channel.id in current_game_info:
        current_game_info[ctx.channel.id]['time_left'] = 10
        await ctx.send("**⏰ 10 seconds remaining!**")
    
    await asyncio.sleep(10)
    await ctx.send("**Time's up!**")
    timer_expired[0] = True
    
    if ctx.channel.id in current_game_info:
        del current_game_info[ctx.channel.id]

bot.run(TOKEN)