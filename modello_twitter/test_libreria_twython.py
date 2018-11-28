from twython import Twython
from raven import Client
import credenziali

try:
    sentry = Client(credenziali.url_sentry)
    twitter = Twython(credenziali.consumer_key,credenziali.consumer_secret,credenziali.access_token,credenziali.access_token_secret)

    end_point_geo_search='https://api.twitter.com/1.1/geo/search.json'
    search_param={'query':'Ancona','granularity':'city','max_results':3}
    #luoghi = twitter.get(end_point_geo_search,geo_search_param)
    #luoghi = twitter.search_geo(query='Ancona',granularity='city',max_results=3)
    luoghi = twitter.search_geo(**search_param)
    print(luoghi)


except:
    sentry.captureException()
    sentry.captureMessage('Something went fundamentally wrong')
