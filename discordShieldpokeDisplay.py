import codecs
import csv
import json
import os
import sys
import urllib.parse as urlParse
import urllib.request as urlRequest
import math
import discord
import time
from datetime import datetime
import locale
import asyncio
from graphqlclient import GraphQLClient

locale.setlocale(locale.LC_TIME, 'fr_FR')
discordTokenPath = os.path.join(os.getcwd(),"discord_token")
discordToken = ''
with open(discordTokenPath, 'r') as discordFile:
    discordToken = discordFile.readline()

apiVersion = 'alpha'
authTokenPath = os.path.join(os.getcwd(),"auth_token")
smashGGClient = GraphQLClient('https://api.smash.gg/gql/' + apiVersion)
with open(authTokenPath, 'r') as authFile:
    smashGGClient.inject_token('Bearer ' + authFile.readline())        

thresholdPath = os.path.join(os.getcwd(),"thresholds")
defaultAnnouncesThresholds = []
with open(thresholdPath, 'r') as thresholdFile:
    defaultAnnouncesThresholds = [float(stringThreshold) for stringThreshold in thresholdFile.readline().split()]

client = discord.Client()

async def annoucement(retrieveTimer=10):
    entrantsAnnouncesThresholds = set(defaultAnnouncesThresholds)
    previousNbEntrants = 0
    current_shieldpoke = retrieve_correct_shortlink()
    previous_tournament_date = ''
    tournament_date = ''
    current_publish_state = False
    tournament_published = False
    while True:
        # Resets if new Shieldpoke 
        if(current_shieldpoke != retrieve_correct_shortlink() or (previous_tournament_date != '' and tournament_date != previous_tournament_date)):
            entrantsAnnouncesThresholds = set(defaultAnnouncesThresholds)
            current_shieldpoke = retrieve_correct_shortlink()
            current_publish_state = False
            tournament_published = False
            previousNbEntrants = 0
        entrantsAndEventSize = smashGGClient.execute('''query EntrantsAndEventSize($slug: String!) {
            tournament(slug: $slug){
                    name
                    venueAddress
                    publishing
                    startAt
                    shortSlug
                    events{
                        name
                        numEntrants
                        startAt
                        phases{
                            name
                        }
                    },
                    
                }
            }''',{
        "slug":current_shieldpoke
        })
        parsedData = json.loads(entrantsAndEventSize)
        tournamentName = parsedData['data']['tournament']['name']
        conditionEvent = lambda event : event['name'] == 'Ultimate Singles'
        ultimateSinglesEvent = next(filter(conditionEvent, parsedData['data']['tournament']['events']))
        nbEntrants = int(ultimateSinglesEvent['numEntrants'])
        tournament_date = datetime.fromtimestamp(parsedData['data']['tournament']['startAt']).strftime('%A %d %B %Y')
        maxEntrants = max([int(phase['name'].split()[1]) for phase in ultimateSinglesEvent['phases']])
        remainingEntrants = maxEntrants-nbEntrants
        publish_state = bool(parsedData['data']['tournament']['publishing']['publish'])
        print(publish_state)
        entrantsRate = remainingEntrants/maxEntrants
        # Publish announcement if tournament published
        if current_publish_state != publish_state and tournament_published == False:
            venue_address = parsedData['data']['tournament']['venueAddress']
            short_slug = parsedData['data']['tournament']['shortSlug']
            current_publish_state = True
            sentence = 'Le **'+ tournamentName + '** est en ligne !\r\n:calendar: '+tournament_date+ '\r\n:euro: Entrée à 2€50 / Ultimate Singles à 2€50\r\n:video_game: '+str(maxEntrants)+' places\r\n:pushpin: '+venue_address+'\r\n:pencil2: https://smash.gg/'+short_slug 
            channel = client.get_channel(653622127815294986)
            await channel.send(sentence)
            tournament_published = True
        # Attendees threshold reached
        if previousNbEntrants != remainingEntrants and entrantsRate <= max(entrantsAnnouncesThresholds):
            sentence = 'Plus que '+str(remainingEntrants)+ (' places ' if remainingEntrants > 1 else ' place ') + 'pour le '+tournamentName+' !\r\n:pushpin: http://smash.gg/'+current_shieldpoke
            previousNbEntrants = remainingEntrants
            channel = client.get_channel(653622127815294986)
            await channel.send(sentence)
            entrantsAnnouncesThresholds = remove_thresholds_reached(entrantsAnnouncesThresholds,entrantsRate)
        previous_tournament_date = tournament_date
        time.sleep(retrieveTimer)

def retrieve_correct_shortlink():    
    mrs_request = smashGGClient.execute('''query EntrantsAndEventSize($slug: String!) {
        tournament(slug: $slug){
                name
                startAt                
            }
        }''',{
    "slug":'shieldpoke-mrs'
    })
    mrs_data = json.loads(mrs_request)
    aix_request = smashGGClient.execute('''query EntrantsAndEventSize($slug: String!) {
        tournament(slug: $slug){
                name
                startAt
                
            }
        }''',{
    "slug":'shieldpoke-aix'
    })
    aix_data = json.loads(aix_request)
    return 'shieldpoke-aix' if datetime.fromtimestamp(aix_data['data']['tournament']['startAt']) > datetime.fromtimestamp(mrs_data['data']['tournament']['startAt']) else 'shieldpoke-mrs' 

def remove_thresholds_reached(thresholds, current_rate):
    while max(thresholds) >= current_rate:
        thresholds.remove(max(thresholds))
    return thresholds

def second_max(list_arg):
    new_list = set(list_arg)
    new_list.remove(max(new_list))
    return max(new_list)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!planning'):
        await message.channel.send(':flag_fr: Planning Smash Ultimate FR :flag_fr:\r\n:pushpin: https://smashultimate.fr/planning')

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')    
    await annoucement()

    
def main():
    client.run(discordToken)

if __name__ == "__main__":
    main()