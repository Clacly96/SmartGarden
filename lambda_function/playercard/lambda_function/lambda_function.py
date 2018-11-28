import boto3,json
from jinja2 import Environment, FileSystemLoader,select_autoescape
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
# Automatically report all uncaught exceptions
sentry_sdk.init(
    dsn="url_sentry",
    integrations=[AwsLambdaIntegration()]
)

local_player="/tmp/player.html"
local_card="/tmp/card.html"


env = Environment(
        loader=FileSystemLoader("/tmp"),
        autoescape=select_autoescape(['html']),
        trim_blocks=True
    )
# create the html page that contains the player of the video based on the html template file  local_player
def html_player(video_url,template):
    player_temp=env.get_template(template)
    player=player_temp.render(video_url=video_url)
    return player
# create the html page that contains the player of the video based on the html template file local_card
def html_card(title,description,image_url,player_url,video_width,video_height,template):

    card_temp=env.get_template(template)
    card=card_temp.render(title=title,description=description,image_url=image_url,player_url=player_url,video_height=video_height,video_width=video_width)
    return card


def handler(event, context):
    s3_client = boto3.client('s3')
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key_video = record['s3']['object']['key']
        id_plant = key_video.split('/')[-2]
        name_video = key_video.split('/')[-1]
        name_video=name_video.split('.')[0]
        path_twittercard="{}/twitter/".format(key_video.split('/')[0])
        #download config file
        with open("/tmp/config.json", 'wb') as data:
            s3_client.download_fileobj(bucket, path_twittercard+"card/{0}/config/{1}.json".format(id_plant,name_video), data)
        with open("/tmp/config.json", 'r') as f:
            config = json.load(f)

        #download template
        with open("/tmp/temp_card.html", 'wb') as data:
            s3_client.download_fileobj(bucket, path_twittercard+"template/card.html", data)
        with open("/tmp/temp_player.html", 'wb') as data:
            s3_client.download_fileobj(bucket, path_twittercard+"template/player.html", data)

        # Create html player and upload it to s3
        url_video='https://s3.amazonaws.com/{}/{}'.format(bucket,key_video)
        key_player=path_twittercard+'player/{}/{}.html'.format(id_plant,name_video)
        s3_client.put_object(
            Bucket=bucket,
            Body=html_player(url_video,"temp_player.html"),
            Key=key_player,
            ACL='public-read',
            ContentType='text/html'
        )
        # Create html card and upload it to s3
        metadata_video=s3_client.get_object(Bucket=bucket,Key=key_video)['Metadata']
        url_player='https://s3.amazonaws.com/{}/{}'.format(bucket,key_player)
        key_card=path_twittercard+'card/{}/{}.html'.format(id_plant,name_video)
        s3_client.put_object(
            Bucket=bucket,
            Body=html_card(config['title'],config['description'],config['url_image'],url_player,metadata_video['width'],metadata_video['height'],"temp_card.html"),
            Key=key_card,
            ACL='public-read',
            ContentType='text/html'
        )
