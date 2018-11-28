import boto3,uuid,jinja2
from twython import Twython
import credentials

def get_plant_info(plant_uuid):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('plant')
    resp=table.get_item(
        Key={
            'UUID': str(plant_uuid)
        }
    )
    return resp['Item']

def build_tweet(plant_info,template_local_path):
    #set jinja environment to /tmp
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('/tmp'),
        trim_blocks=True
    )
    #load and render the template
    template=env.get_template(template_local_path)
    tweet={}
    tweet['text']=template.render(
        name=plant_info['name'],
        species=plant_info['species'],
        variety=plant_info['variety'],
        period_begin=plant_info['period_begin'],
        period_end=plant_info['period_end'],
        site=plant_info['site']['properties']['name']
    )
    tweet['site']=plant_info['site']['geometry']['coordinates']
    return tweet

def publish_tweet(tweet):
    #get credentials
    twitter = Twython(credentials.consumer_key,credentials.consumer_secret,credentials.access_token,credentials.access_token_secret)
    #publish tweet
    resp=twitter.update_status(status=tweet['text'], lat=tweet['site'][1],long=tweet['site'][0])
    print(f"risposta twitter= {resp}")

def lambda_handler(event, context):
    s3 = boto3.client('s3')

    #set root folder
    root='test_2'
    bucket = 'ortobotanico'
    
    #note: cron name syntax: xxxxxx-xxxx-xxxxx-xxxx_begin or xxxxxx-xxxxx-xxxxx-xxx_end
    plant_uuid=event['resources'][0].split('/')[-1].split('_')[0]
    event_type=event['resources'][0].split('/')[-1].split('_')[1]

    # get the right template
    template_path='{0}/template/template_{1}.txt'.format(root,event_type)
    template_local_path='/tmp/template.txt'

    with open(template_local_path, 'wb') as data:
            s3.download_fileobj(bucket, template_path, data)
   
    #get plant info from DynamoDB
    plant_info=get_plant_info(plant_uuid)
    #build tweet from template
    tweet=build_tweet(plant_info,template_local_path)
    #publish tweet
    publish_tweet(tweet)

