import discord
import aiohttp, os
import openai

import random

client = discord.Client(intents=discord.Intents.all())
with open('openaikey.txt', 'r') as file:
    openai.api_key = file.read()

@client.event
async def on_ready():
    
    print('We have logged in as {0.user}'.format(client))

waiting_for_response = False

@client.event
async def on_message(message):
    global waiting_for_response
    if message.author == client.user:
        return
    
    if (waiting_for_response):
        number = random.randint(1, 9)
        if (message.content.startswith(str(number))):
            await message.channel.send('You guessed right!')
        else:
            await message.channel.send('You guessed wrong! My number was ' + str(number))
        waiting_for_response = False
        
    if message.content.startswith('$info'):
        await message.channel.send('Bot made by: @officialblooms')
        
    if message.content.startswith('$randomnumber'):
        await message.channel.send('guess a random number between 1 and 9')
        waiting_for_response = True
        
    if message.content.startswith('$cat'):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.thecatapi.com/v1/images/search') as resp:
                data = await resp.json()
                await message.channel.send(data[0]['url'])
                
    if message.content.startswith('$randomcar'):
        car_list = os.listdir('vehicles')
        rand_choice = random.choice(car_list)
        await message.channel.send(file=discord.File('./vehicles/' + rand_choice))
        
with open('bottoken.txt', 'r') as file:
    client.run(file.read())