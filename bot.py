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
    embed.add_field(name="*quit", value="Quits the current game", inline=False)
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
        await anagram_run(ctx, word, custom_word=True)

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

def create_anagrams_list(words_list, title):
    """Create a formatted list for displaying anagrams"""
    if not words_list:
        if title:
            return f"**{title}**\nNo words to display."
        else:
            return "No words to display."
    
    # Group words by length
    result = ""
    if title:
        result += f"**{title}**\n"
    
    for length in range(max(len(word) for word in words_list), 2, -1):
        words_of_length = [word for word in words_list if len(word) == length]
        if words_of_length:
            # Create a clean list format
            if length == 6:
                result += f"**🔵 {length}-letter words ({len(words_of_length)}):**\n"
            elif length == 5:
                result += f"**🟢 {length}-letter words ({len(words_of_length)}):**\n"
            elif length == 4:
                result += f"**🟡 {length}-letter words ({len(words_of_length)}):**\n"
            else:
                result += f"**🟠 {length}-letter words ({len(words_of_length)}):**\n"
            
            # Split into chunks to avoid Discord's message length limit
            words_str = ', '.join(words_of_length)
            if len(words_str) > 100:  # Discord limit is ~2000 chars
                # Split into smaller chunks
                chunks = [words_str[i:i+100] for i in range(0, len(words_str), 100)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        result += f"`{chunk}`\n"
                    else:
                        result += f"`{chunk}`\n"
            else:
                result += f"`{words_str}`\n"
            result += "\n"
    
    return result

async def anagram_run(ctx, word, custom_word=False):
    if custom_word:
        scramble = word
    else:
        scramble = "".join(random.sample(word, len(word)))
    user = ctx.author
    anagrams = set()
    with open(dictionary_path, 'r') as f:
        for line in f:
            word_check = line.strip().lower()
            if contains_same_letters(word, word_check) and len(word_check) >= 3:
                anagrams.add(word_check)
    
    completed_anagrams = set()

    embed = discord.Embed(
        title="🎯 ANAGRAMS GAME STARTED! 🎯",
        description=f"**Word:** `{scramble}`\n**Time:** 60 seconds\n\n**Type your anagrams now!**",
        color=0x00ff00
    )
    embed.set_footer(text="Use *quit to exit early")
    await ctx.send(embed=embed)
    
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
        elif ' ' in msg.content:
            continue
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
    
    # Create results embed
    results_embed = discord.Embed(
        title="🏆 GAME RESULTS 🏆",
        description=f"**Total points:** {points:,}",
        color=0xffd700
    )
    
    completed_count = len(sorted_completed)
    if completed_count > 0:
        completed_list = create_anagrams_list(sorted_completed, None)
        # Split long lists into multiple fields if needed
        if len(completed_list) > 1024:
            # Split into chunks of 1000 characters
            chunks = [completed_list[i:i+1000] for i in range(0, len(completed_list), 1000)]
            for i, chunk in enumerate(chunks):
                field_name = f"✅ Found Anagrams (Part {i+1})" if i > 0 else f"✅ You found {completed_count} anagram{'s' if completed_count != 1 else ''}"
                results_embed.add_field(
                    name=field_name,
                    value=chunk,
                    inline=False
                )
        else:
            results_embed.add_field(
                name=f"✅ You found {completed_count} anagram{'s' if completed_count != 1 else ''}",
                value=completed_list,
                inline=False
            )
    
    if len(sorted_anagrams) == 0:
        results_embed.add_field(
            name="🎉 Perfect Score! 🎉",
            value="You got every anagram! I'm so proud of you!",
            inline=False
        )
    else:
        missed_count = len(sorted_anagrams)
        missed_list = create_anagrams_list(sorted_anagrams, None)
        # Split long lists into multiple fields if needed
        if len(missed_list) > 1024:
            # Split into chunks of 1000 characters
            chunks = [missed_list[i:i+1000] for i in range(0, len(missed_list), 1000)]
            for i, chunk in enumerate(chunks):
                field_name = f"❌ Missed Anagrams (Part {i+1})" if i > 0 else f"❌ You missed {missed_count} anagram{'s' if missed_count != 1 else ''}"
                results_embed.add_field(
                    name=field_name,
                    value=chunk,
                    inline=False
                )
        else:
            results_embed.add_field(
                name=f"❌ You missed {missed_count} anagram{'s' if missed_count != 1 else ''}",
                value=missed_list,
                inline=False
            )
    
    await ctx.send(embed=results_embed)
    
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