import discord
import aiohttp
import os
import google.generativeai as genai
from googleapiclient.discovery import build

import random

# sets up Discord client 
client = discord.Client(intents=discord.Intents.all())


with open('googlecloudkey.txt', 'r') as file:
    GOOGLE_CLOUD_KEY = file.read()
    
# sets up Gemini
genai.configure(api_key=GOOGLE_CLOUD_KEY)
model = genai.GenerativeModel('models/gemini-pro')

# sets up Youtube API
youtube = build('youtube', 'v3', developerKey=GOOGLE_CLOUD_KEY)

@client.event
async def on_ready():
    
    print('We have logged in as {0.user}'.format(client))

waiting_for_response = False

@client.event
async def on_message(message):
    global waiting_for_response
    
    # ensures the bot doesn't respond to itself
    if message.author == client.user:
        return
    
    # follow-up prompt for a previously-requested command
    if waiting_for_response:
        number = random.randint(1, 9)
        if message.content.startswith(str(number)):
            await message.channel.send('You guessed right!')
        else:
            await message.channel.send('You guessed wrong! My number was ' + str(number))
        waiting_for_response = False
    
    # random number game
    if message.content.startswith('$randomnumber'):
        await message.channel.send('guess a random number between 1 and 9')
        waiting_for_response = True
        
    # shows random pictures of cats
    if message.content.startswith('$cat'):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.thecatapi.com/v1/images/search') as resp:
                data = await resp.json()
                await message.channel.send(data[0]['url'])
                
    # gemini test response
    if message.content.startswith('$gemini'):
        prompt = message.content[len('$gemini'):].strip()
        
        # Send a typing indicator while processing the request
        async with message.channel.typing():
            try:
                response = model.generate_content(prompt)
                answer = response.text
            except Exception as e:
                answer = f"An error occurred: {e}"
        
        # Send the response back to the Discord channel
        await message.channel.send(answer)
        
    # shows random pictures of a car along with a chatgpt response about it
    if message.content.startswith('$randomcar'):
        
        # get a random car picture from the vehicles folder
        rand_car_model = random.choice(os.listdir('vehicles'))
        rand_car_image = random.choice(os.listdir('./vehicles/' + rand_car_model))
        image = './vehicles/' + rand_car_model + '/' + rand_car_image
        await message.channel.send(file=discord.File(image))
        
        # ask gemini about the specific car model
        async with message.channel.typing(): # sends typing indicator while processing request
            try: 
                response = model.generate_content([
                    "Tell me what the " + rand_car_model + " is and its capabilites in no more than 4 sentences.",
                ])
                answer = response.text
            except Exception as e:
                answer = f"Something went wrong with the request: {e}"
        
        
        await message.channel.send(answer)
        
    # searches for a random OfficialBlooms youtube video
    if message.content.startswith('$officialblooms'):
        try:
            response = youtube.search().list(
                part='snippet',
                channelId='UCuidePcDLDdc_RNsP7DgvLw',
                maxResults=50,
                order='date'
            ).execute()
            
            videos = response['items']
            random_video = random.choice(videos)
            video_url = f"https://www.youtube.com/watch?v={random_video['id']['videoId']}"
            
            await message.channel.send(f"Here's a random video from OfficialBlooms: {video_url}")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
            
        
with open('bottoken.txt', 'r') as file:
    client.run(file.read())