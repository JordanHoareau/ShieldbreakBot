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
import asyncio
from graphqlclient import GraphQLClient

discordToken = 'NjUzNTkwNzQyMDg1Nzk1ODYw.Xe6R0g.i9S26YpZpVlHF13T2hzWaEKvwmk'
apiVersion = 'alpha'
authTokenPath = os.path.join(os.getcwd(),"auth_token")
smashGGClient = GraphQLClient('https://api.smash.gg/gql/' + apiVersion)
with open(authTokenPath, 'r') as authFile:
    smashGGClient.inject_token('Bearer ' + authFile.readline())

client = discord.Client()
clientReady = False
previousNbEntrants = 0

async def annoucement(retrieveTimer=10):
    while True:
        entrantsAndEventSize = smashGGClient.execute('''query EntrantsAndEventSize($slug: String!) {
            tournament(slug: $slug){
                    name,
                    events{
                        numEntrants
                        phases{
                            name
                        }
                    },
                    
                }
            }''',{
        "slug":sys.argv[1]
        })
        parsedData = json.loads(entrantsAndEventSize)
        tournamentName = parsedData['data']['tournament']['name']
        nbEntrants = int(parsedData['data']['tournament']['events'][0]['numEntrants'])
        maxEntrants = max([int(phase['name'].split()[1]) for phase in parsedData['data']['tournament']['events'][0]['phases']])
        remainingEntrants = maxEntrants-nbEntrants
        sentence = 'Plus que '+str(remainingEntrants)+ (' places ' if remainingEntrants > 1 else ' place ') + 'pour le '+tournamentName+' !\r\n:pushpin: http://smash.gg/shieldpoke-aix'
        print(str(nbEntrants)+'/'+str(maxEntrants))
        channel = client.get_channel(653622127815294986)
        await channel.send(sentence)
        time.sleep(retrieveTimer)

def wait_until(somepredicate, timeout, period=0.25, *args, **kwargs):
  mustend = time.time() + timeout
  while time.time() < mustend:
    if somepredicate(*args, **kwargs): return True
    time.sleep(period)
  return False

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