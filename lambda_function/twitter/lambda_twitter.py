from twython import Twython
import boto3
import credentials
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
# Automatically report all uncaught exceptions
sentry_sdk.init(
    dsn="url_sentry",
    integrations=[AwsLambdaIntegration()]
)

# publish a tweet with a message, a place ad a video integrated, pay attention to twitter size limit for videos
def publish_video(path_video,message,place=None):
    twitter = Twython(credentials.consumer_key,credentials.consumer_secret,credentials.access_token,credentials.access_token_secret)
    video = open(path_video, 'rb')
    response = twitter.upload_video(media=video, media_type='video/mp4')
    if place==None:
        twitter.update_status(status=message, media_ids=[response['media_id']])
    else:
        twitter.update_status(status=message, media_ids=[response['media_id']],place_id=place)
    close(video)

# publish a tweet with a message, a place ad a photo integrated, pay attention to twitter size limit for photos
def publish_image(path_image,message,place=None):
    twitter = Twython(credentials.consumer_key,credentials.consumer_secret,credentials.access_token,credentials.access_token_secret)
    photo = open(path_image, 'rb')
    response = twitter.upload_media(media=photo)
    if place==None:
        twitter.update_status(status=message, media_ids=[response['media_id']])
    else:
        twitter.update_status(status=message, media_ids=[response['media_id']],place_id=place)
    close(photo)

# publish a tweet with a text message and place, pay attention to the limit of number of characters
def publish_status(message,place=None):
    twitter = Twython(credentials.consumer_key,credentials.consumer_secret,credentials.access_token,credentials.access_token_secret)
    if place==None:
        twitter.update_status(status=message)
    else:
        twitter.update_status(status=message,place_id=place)

# return a dict of id_places necessary for the geolocalization of the tweet, starting from a city name
def find_place(city_name,granularity='city',max_results=3): # da migliorare facendo una cernita dei risultati
    twitter = Twython(credentials.consumer_key,credentials.consumer_secret,credentials.access_token,credentials.access_token_secret)
    search_param={'query':city_name,'granularity':granularity,'max_results':max_results}
    found_places = twitter.search_geo(**search_param)
    # found_places is a dict
    return found_places['result']['places'][0]['id']

def handler(event, context):
    s3_client = boto3.client('s3')
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
    url_card="https://s3.amazonaws.com/{0}/{1}".format(bucket,key)
    publish_status(
                    url_card,
                    find_place('Ancona','city',1)
                    )
