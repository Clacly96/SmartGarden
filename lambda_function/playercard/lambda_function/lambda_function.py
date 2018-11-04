import boto3,json
from jinja2 import Environment, FileSystemLoader,select_autoescape

local_player="/tmp/player.html"
local_card="/tmp/card.html"
path_twittercard="demo/card/"

env = Environment(
        loader=FileSystemLoader("/tmp"),
        autoescape=select_autoescape(['html']),
        trim_blocks=True
    )
def html_player(video_url,template):
    player_temp=env.get_template(template)
    player=player_temp.render(video_url=video_url)
    return player

def html_card(title,description,image_url,player_url,video_width,video_height,template):

    card_temp=env.get_template(template)
    card=card_temp.render(title=title,description=description,image_url=image_url,player_url=player_url,video_height=video_height,video_width=video_width)
    return card


def handler(event, context):
    s3_client = boto3.client('s3')
    for record in event['Records']:
        nome_bucket = record['s3']['bucket']['name']
        path_video = record['s3']['object']['key']
        nome_pianta = path_video.split('/')[-2]
        nome_video = path_video.split('/')[-1]
        nome_video=nome_video.split('.')[0]
        #download config file
        with open("/tmp/config.json", 'wb') as data:
            s3_client.download_fileobj(nome_bucket, path_twittercard+"config.json", data)
        with open("/tmp/config.json", 'r') as f:
            config = json.load(f)

        #download template
        with open("/tmp/temp_card.html", 'wb') as data:
            s3_client.download_fileobj(nome_bucket, path_twittercard+"template/card.html", data)
        with open("/tmp/temp_player.html", 'wb') as data:
            s3_client.download_fileobj(nome_bucket, path_twittercard+"template/player.html", data)

        # Crea html player e lo inserisce su s3
        url_video='https://s3.amazonaws.com/{}/{}'.format(nome_bucket,path_video)
        key_player=path_twittercard+'{}/player-{}.html'.format(nome_pianta,nome_video)
        s3_client.put_object(
            Bucket=nome_bucket,
            Body=html_player(url_video,"temp_player.html"),
            Key=key_player,
            ACL='public-read',
            ContentType='text/html'
        )
        # Crea html card e lo carica su s3
        videoobj=s3_client.get_object(Bucket=nome_bucket,Key=path_video)['Metadata']
        url_player='https://s3.amazonaws.com/{}/{}'.format(nome_bucket,key_player)
        key_card=path_twittercard+'{}/card-{}.html'.format(nome_pianta,nome_video)
        s3_client.put_object(
            Bucket=nome_bucket,
            Body=html_card(config['titolo'],config['descrizione'],config['url_immagine'],url_player,videoobj['width'],videoobj['height'],"temp_card.html"),
            Key=key_card,
            ACL='public-read',
            ContentType='text/html'
        )
