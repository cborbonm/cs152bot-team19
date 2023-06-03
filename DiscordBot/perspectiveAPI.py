from googleapiclient import discovery
import json

API_KEY = 'AIzaSyAKAFbnHmHMCgvtRrCsujZ1p0LrWvLFnhA'

# Available types of scores for Google API
class productionType:
    TOXICITY = 'TOXICITY'
    SEVERE_TOXICITY = 'SEVERE_TOXICITY'
    IDENTITY_ATTACK = 'IDENTITY_ATTACK'
    INSULT = 'INSULT'
    PROFANITY = 'PROFANITY'
    THREAT = 'THREAT'

class experimentalType:
    TOXICITY_EXPERIMENTAL = 'TOXICITY_EXPERIMENTAL'
    SEVERE_TOXICITY_EXPERIEMNTAL = 'SEVERE_TOXICITY_EXPERIEMNTAL'
    IDENTITY_ATTACK_EXPERIMENTAL = 'IDENTITY_ATTACK_EXPERIMENTAL'
    INSULT_EXPERIMENTAL = 'INSULT_EXPERIMENTAL'
    PROFANITY_EXPERIMENTAL = 'PROFANITY_EXPERIMENTAL'
    THREAT_EXPERIMENTAL =  'THREAT_EXPERIMENTAL'
    SEXUALLY_EXPLICIT = 'SEXUALLY_EXPLICIT'
    FLIRTATION = 'FLIRTATION'

class NYTType:
    ATTACK_ON_AUTHOR = 'ATTACK_ON_AUTHOR'
    ATTACK_ON_COMMENTER = 'ATTACK_ON_COMMENTER'
    INCOHERENT = 'INCOHERENT'
    INFLAMMATORY = 'INFLAMMATORY'
    LIKELY_TO_REJECT = 'LIKELY_TO_REJECT'
    OBSCENE = 'OBSCENE'
    SPAM = 'SPAM'
    UNSUBSTANTIAL = 'UNSUBSTANTIAL'



client = discovery.build(
  "commentanalyzer",
  "v1alpha1",
  developerKey=API_KEY,
  discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
  static_discovery=False,
)

def getAPIScore (message: str):

    analyze_request = {
     'comment': { 'text': f'`{message}`'},
     'requestedAttributes': {experimentalType.SEXUALLY_EXPLICIT: {}, experimentalType.FLIRTATION: {}, productionType.THREAT: {}, productionType.TOXICITY: {}}
     }
    response = client.comments().analyze(body=analyze_request).execute()    
    getTypeScores(response, analyze_request)

def getTypeScores (response, analyze_request):
    print("Scores from Google Perspective API:")
    for type in analyze_request['requestedAttributes'].keys():
        score = response['attributeScores'][type]['summaryScore']['value']
        print('Type:' + f"`{type}` \n `{score}`" )

if __name__ == "__main__":
    getAPIScore("When you get back you better drive me to go get a dipped cone or else.")