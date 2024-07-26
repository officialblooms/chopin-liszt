import discord
import aiohttp
import os
import google.generativeai as genai
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy 

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

# sets up Spotify API

SPOTIFY_CLIENT_ID = '571cdd92da0446afbcad9a37d80edbf7'

with open('spotifysecret.txt', 'r') as file:
    SPOTIFY_CLIENT_SECRET = file.read()

spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))   

# store all songs from a given playlist
def extract_songs(playlist_id, offset=0):
    song_list = []
    leftover_songs = [track['track'] for track in spotify.playlist_items(playlist_id=playlist_id, fields="items(track)", offset=offset)['items']]
    if (len(leftover_songs) > 0):
        song_list = leftover_songs
        song_list.extend(extract_songs(playlist_id, offset + 100))
    return song_list

@client.event
async def on_ready():
    
    print('We have logged in as {0.user}'.format(client))

waiting_for_response = False
random_number = False # random number game
playlist_url = False # spotify playlist url


@client.event
async def on_message(message):
    
    global waiting_for_response, random_number, playlist_url
    
    # ensures the bot doesn't respond to itself
    if message.author == client.user:
        return
    
    # follow-up prompt for a previously-requested command
    if waiting_for_response:
        waiting_for_response = False
        if (random_number):
            number = random.randint(1, 9)
            if message.content.startswith(str(number)):
                await message.channel.send('You guessed right!')
            else:
                await message.channel.send('You guessed wrong! My number was ' + str(number))
            random_number = False    
        elif (playlist_url):
            playlist_id = message.content.split('playlist/')[1].split('?')[0]
            try:
                song_list = extract_songs(playlist_id)
    
                print(len(song_list))
                if (len(song_list) == 0):
                    await message.channel.send("No songs found in the playlist")
                    return
                
                random_track = random.choice(song_list)
                track_url = random_track['external_urls']['spotify']
                
                await message.channel.send(f"Here's a random song from your playlist: {track_url}")
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}")
            playlist_url = False
            # TODO: allow user to choose another song from playlist by typing "next"
        
            
        
    # random number game
    if message.content.startswith('$randomnumber'):
        await message.channel.send('guess a random number between 1 and 9')
        waiting_for_response = True
        random_number = True
        
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
            # gets 50 random videos
            response = youtube.search().list(
                part='snippet',
                channelId='UCuidePcDLDdc_RNsP7DgvLw',
                maxResults=50,
            ).execute()
            
            videos = response['items']
            random_video = random.choice(videos)
            video_url = f"https://www.youtube.com/watch?v={random_video['id']['videoId']}"
            
            await message.channel.send(f"Here's a random video from OfficialBlooms: {video_url}")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
            
    # sends a random beatles song on Spotify
    if message.content.startswith('$beatles'):
        try:
            song_list = extract_songs('0rWlHb2uqgRv6bTXEiFcZY')
            random_track = random.choice(song_list)
            track_url = random_track['external_urls']['spotify']
            
            await message.channel.send(f"Here's a random song from Beatles: {track_url}")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
            
    # sends a random song on a provided playlist on Spotify
    if message.content.startswith('$playlist'):
        await message.channel.send("Please provide a playlist URL")
        waiting_for_response = True
        playlist_url = True
        
with open('bottoken.txt', 'r') as file:
    client.run(file.read())