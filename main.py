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

# get a random song's URL from a given playlist
def get_random_song(playlist_id):
    try:
        song_list = extract_songs(playlist_id)
        
        if (len(song_list) == 0):
            return "No songs found in the playlist."
                    
        random_track = random.choice(song_list)
        track_url = random_track['external_urls']['spotify']
                    
        return track_url
    except Exception as e:
        return "An error has occurred: " + e

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
attempts = 0

# --random number game vars--
random_number_game = False
number = 0

# --hard random number game vars--
random_number_game_hard = False
number_list = [0, 0, 0, 0, 0]

# --spotify playlist vars--
global_playlist_url = ''

@client.event
async def on_message(message):
    
    global waiting_for_response, attempts
    
    global random_number_game, number
    
    global random_number_game_hard, number_list
    
    global global_playlist_url
    
    # ensures the bot doesn't respond to itself
    if message.author == client.user:
        return
    
    # follow-up prompt for a previously-requested command
    if waiting_for_response:
        
        if (message.content == 'quit'):
            await message.channel.send('Previous command has been terminated.')
            waiting_for_response = False
            return
        
        # random number game
        if (random_number_game):
            # initializes number (only on first att)
            if (attempts == 0):
                number = random.randint(1, 37)
            # ensures pre-condition is right
            if (not message.content.isdigit() or int(message.content) < 1 or int(message.content) > 37):
                await message.channel.send('Please enter a valid number.')
            else:
                attempts += 1
                if message.content == str(number):
                    await message.channel.send(f'You guessed the right number! You got it in {attempts} attempts. Good job!')
                    await message.channel.send('Up for a challenge? Do $randomnumberhard to play a harder version of this game.')
                    waiting_for_response = False
                    random_number_game = False
                else:
                    await message.channel.send(f'You guessed wrong! {message.content} is {'greater' if int(message.content) > number else 'less'} than the correct number.') 
            
        # hard random number game
        if (random_number_game_hard):
            # initialize array if first att
            if (attempts == 0):
                number_list = list(map(lambda x: random.randint(1, 37), number_list))
                while (len(set(number_list)) < 5): # avoid duplicates (thanks copilot for the algo)
                    number_list = list(map(lambda x: random.randint(1, 37), number_list))
            
            if (not message.content.isdigit() or int(message.content) < 1 or int(message.content) > 37):
                await message.channel.send('Please enter a valid number.')
            else:
                attempts += 1
                if int(message.content) in number_list:
                    number_list.remove(int(message.content))
                    await message.channel.send(f'You guessed one of the numbers! Good job!')
                
                # -- start branch -- #
                if (len(number_list) != 0):
                    result = list(map(lambda x: 'higher' if int(message.content) - x > 0 else 'lower', number_list))
                    if (attempts % 5 == 0):
                        number_list.append(random.randint(1, 37)) 
                    await message.channel.send(f'Your guess is {result} than each number in the list. {'Another number has been added to the list.' if attempts % 5 == 0 else ''}') 
                    await message.channel.send(f'{len(number_list)} more numbers to guess!')
                else:    
                    await message.channel.send(f'You have excavated all the numbers in the list! You did it in {attempts} attempts! Good job!')
                    random_number_game_hard = False
                    waiting_for_response = False
                # -- end branch -- #   
            
        # playlist link request
        elif (global_playlist_url):
            if (message.content == 'next'):
                async with message.channel.typing():
                    await message.channel.send(f'Here\'s another random song from your playlist: {get_random_song(global_playlist_url)}')
            else:
                waiting_for_response = False
        
    # random number game
    if message.content == '$randomnumber':
        await message.channel.send('guess a random number between 1 and 37! (type \'quit\' to stop playing)')
        waiting_for_response = True
        random_number_game = True
        
    # random number hard game
    if message.content == '$randomnumberhard':
        await message.channel.send('i have 5 random numbers. every 5 guesses, another number will be added to the list. start by typing a number between 1 to 37! (type \'quit\' to stop playing)')
        waiting_for_response = True
        random_number_game_hard = True
        
    # shows random pictures of a car along with a chatgpt response about it
    if message.content == '$randomcar':
        
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
    if message.content.lower().__contains__('officialblooms') or message.content.lower().__contains__('blooms'):
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
            
            await message.channel.send(f"Did someone call my name? No? Well here's a random vid you should watch anyway: {video_url}")
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")
            
    # sends a random song on a provided playlist on Spotify
    if message.content.startswith('$playlist'): 
        link = message.content.split('$playlist')[1].strip()
        # checks if proper URL is provided
        if (link == ''): # if user does not include URL
            await message.channel.send("Proper syntax: $playlist <URL of Spotify playlist>")
            return
        elif (not link.startswith('https://open.spotify.com/playlist/')):
            await message.channel.send("Invalid playlist URL")
            return
            

        playlist_url = link.split('playlist/')[1].split('?')[0]
        async with message.channel.typing():
            song_url = get_random_song(playlist_url)
            if (song_url.startswith('https://open.spotify.com/track/')):
                await message.channel.send(f'Here is a random song from your playlist: {song_url}. Type "next" for another song from the same playlist.')
                waiting_for_response = True # see if user wants another song from the same playlist
                global_playlist_url = playlist_url
            else: # error handling
                await message.channel.send(song_url)
        
    # sends a random beatles song on Spotify 
    if message.content == '$beatles':
        async with message.channel.typing():
            try:
                song_list = extract_songs('0rWlHb2uqgRv6bTXEiFcZY')
                random_track = random.choice(song_list)
                track_url = random_track['external_urls']['spotify']
                
                await message.channel.send(f"Here's a random song from Beatles: {track_url}")
            except Exception as e:
                await message.channel.send(f"An error occurred: {e}") 
                  
    # shows random pictures of cats
    if message.content == '$cat':
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.thecatapi.com/v1/images/search') as resp:
                data = await resp.json()
                await message.channel.send(data[0]['url'])
                
    # gemini test response
    if message.content == '$gemini':
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
    
with open('bottoken.txt', 'r') as file:
    client.run(file.read())