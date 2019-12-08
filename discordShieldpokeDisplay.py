import codecs
import csv
import json
import os
import sys
import urllib.parse as urlParse
import urllib.request as urlRequest
import math
from graphqlclient import GraphQLClient

apiVersion = 'alpha'
authTokenPath = os.path.join(os.getcwd(),"auth_token")
client = GraphQLClient('https://api.smash.gg/gql/' + apiVersion)
with open(authTokenPath, 'r') as authFile:
	client.inject_token('Bearer ' + authFile.readline())


eventStandings = client.execute('''query EventStandings($slug: String!) {
	tournament(slug: $slug){
			name,
			events{
				phases {
					name,
					id
				}
			}
		}
	}''',{
"slug":sys.argv[1]
})
print(eventStandings)