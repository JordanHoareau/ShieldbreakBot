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
import yaml
import locale
import asyncio
from graphqlclient import GraphQLClient

locale.setlocale(locale.LC_TIME, 'fr_FR')

conf_path = os.path.join(os.getcwd(),'conf.yaml')
with open(conf_path, 'r') as file_stream:
    conf = yaml.safe_load(file_stream)

tokens_path = os.path.join(os.getcwd(),conf["paths"]["tokens-file"])
with open(tokens_path, 'r') as file_stream:
    tokens = yaml.safe_load(file_stream)
discord_token = tokens['discord']
smashgg_token = tokens['smash.gg']

apiVersion = 'alpha'
smashGGClient = GraphQLClient('https://api.smash.gg/gql/' + apiVersion)
smashGGClient.inject_token('Bearer ' + smashgg_token)        

target_channel = conf['channels']['target']
tournament_channel = conf['channels']['tournament']

thresholdPath = os.path.join(os.getcwd(),"thresholds")
default_announces_thresholds = conf['thresholds']

client = discord.Client()

async def annoucement(retrieve_time=10):
    entrants_announces_threshold = set(default_announces_thresholds)
    previousnb_entrants = 0
    current_shieldpoke = retrieve_correct_shortlink()
    previous_tournament_date = ''
    tournament_date = ''
    current_publish_state = False
    tournament_published = False
    while True:
        # Resets if new Shieldpoke 
        if(current_shieldpoke != retrieve_correct_shortlink() or (previous_tournament_date != '' and tournament_date != previous_tournament_date)):
            entrants_announces_threshold = set(default_announces_thresholds)
            current_shieldpoke = retrieve_correct_shortlink()
            current_publish_state = False
            tournament_published = False
            previousnb_entrants = 0
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
        parsed_data = json.loads(entrantsAndEventSize)
        tournament_name = parsed_data['data']['tournament']['name']
        condition_event = lambda event : event['name'] == 'Ultimate Singles'
        ultimate_singles_event = next(filter(condition_event, parsed_data['data']['tournament']['events']))
        nb_entrants = int(ultimate_singles_event['numEntrants'])
        tournament_date = datetime.fromtimestamp(parsed_data['data']['tournament']['startAt']).strftime('%A %d %B %Y')
        max_entrants = max([int(phase['name'].split()[1]) for phase in ultimate_singles_event['phases']])
        remaining_entrants = max_entrants-nb_entrants
        publish_state = bool(parsed_data['data']['tournament']['publishing']['publish'])
        entrants_rate = remaining_entrants/max_entrants
        # Publish announcement if tournament published
        if current_publish_state != publish_state and tournament_published == False:
            venue_address = parsed_data['data']['tournament']['venueAddress']
            short_slug = parsed_data['data']['tournament']['shortSlug']
            current_publish_state = True
            sentence = 'Le **'+ tournament_name + '** est en ligne !\r\n:calendar: '+tournament_date+ '\r\n:euro: Entrée à 2€50 / Ultimate Singles à 2€50\r\n:video_game: '+str(max_entrants)+' places\r\n:pushpin: '+venue_address+'\r\n:pencil2: https://smash.gg/'+short_slug 
            channel = client.get_channel(target_channel)
            await channel.send(sentence)
            tournament_published = True
        # Attendees threshold reached
        if previousnb_entrants != remaining_entrants and entrants_rate <= max(entrants_announces_threshold):
            sentence = 'Plus que '+str(remaining_entrants)+ (' places ' if remaining_entrants > 1 else ' place ') + 'pour le '+tournament_name+' !\r\n:pushpin: http://smash.gg/'+current_shieldpoke
            previousnb_entrants = remaining_entrants
            channel = client.get_channel(target_channel)
            await channel.send(sentence)
            entrants_announces_threshold = remove_thresholds_reached(entrants_announces_threshold,entrants_rate)
        previous_tournament_date = tournament_date
        time.sleep(retrieve_time)

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
    client.run(discord_token)

if __name__ == "__main__":
    main()