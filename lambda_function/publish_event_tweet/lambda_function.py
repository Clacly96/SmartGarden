import boto3,jinja2,json,urllib,datetime,random
from twython import Twython
import credentials

import sentry_sdk,sentryDSN
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

#capture all unhandled exceptions
sentry_sdk.init(
    sentryDSN.DSN,
    integrations=[AwsLambdaIntegration()]
)

def getTweetID(device_UUID,chart_period,chart_type):
    dynamodb=boto3.resource('dynamodb')
    table=dynamodb.Table('tweetIDs')

    response = table.query(
        ConsistentRead=True,
        ProjectionExpression=chart_type,
        KeyConditionExpression='device_UUID = :devUUID AND chart_period = :period',
        ExpressionAttributeValues={
            ':devUUID':device_UUID,
            ':period':chart_period,
        }
    )
    try:
        return response['Items'][0][chart_type]
    except:
        return -1

def uploadTweetID(device_UUID,chart_period,chart_type,tweetID):
    dynamodb=boto3.resource('dynamodb')
    table=dynamodb.Table('tweetIDs')

    response = table.update_item(
        Key={
            'device_UUID': device_UUID,
            'chart_period': chart_period
        },
        UpdateExpression='SET '+chart_type+' = :id',
        ExpressionAttributeValues={
            ':id': tweetID
        }
    )  

def build_summary(summary_info,summary_template_S3):
    #set jinja environment to /tmp
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('/tmp'),
        trim_blocks=True
    )
    #load and render the template
    template=env.get_template('template.html')
    summary=template.render(
        title=summary_info['title'],
        description=summary_info['description'],
        url=summary_info['image_url']
    )
    return summary

def get_plant_info(plant_uuid):
    #get plant info from dynamodb
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('plant')
    resp=table.get_item(
        Key={
            'plantUUID': str(plant_uuid)
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
    template=env.get_template(template_local_path.split('/')[-1])
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

def delete_tweet(id):
    #get credentials
    twitter = Twython(credentials.consumer_key,credentials.consumer_secret,credentials.access_token,credentials.access_token_secret)
    response=twitter.destroy_status(id=id)
    return response

def publish_tweet(tweet,local_chart_path=None):
    #get credentials
    twitter = Twython(credentials.consumer_key,credentials.consumer_secret,credentials.access_token,credentials.access_token_secret)
    #publish tweet; publish chart only if path is given    
    if local_chart_path==None:
        if 'site' in tweet:
            response=twitter.update_status(status=tweet['text'], lat=tweet['site'][1],long=tweet['site'][0])
        else:
            response=twitter.update_status(status=tweet['text'])
    else:
        #upload chart, get media id and publish tweet with media
        chart = open(local_chart_path, 'rb')
        response = twitter.upload_media(media=chart)
        response=twitter.update_status(status=tweet['text'], media_ids=[response['media_id']])
    return response

def status_tweet(bucket,root,s3,plant_uuid,event_type):
    # get the right template
    template_path='{0}/template/template_{1}.txt'.format(root,event_type)
    template_local_path='/tmp/template.txt'

    #download template from s3
    with open(template_local_path, 'wb') as data:
            s3.download_fileobj(bucket, template_path, data)
   
    #get plant info from DynamoDB
    plant_info=get_plant_info(plant_uuid)
    #build tweet from template
    tweet=build_tweet(plant_info,template_local_path)
    #publish tweet
    publish_tweet(tweet)

def chart_tweet(bucket,object_key,s3,summary_path_S3,summary_template_S3):
    object_name=object_key.split('/')[-1]
    
    device_UUID=object_name.split('_')[0]

    #period of chart (week or month or day)
    chart_period=object_key.split('/')[-2]
    
    #type of chart (umidity, ...)
    if object_name.split('_')[1] == 'TS':   #case of two scales chart
        dendrometerDataType=object_name.split('.')[0].split('_')[2].split('&')[-1]
        chart_type='dendrometerCh1_2_'+dendrometerDataType
    else:
        chart_type=object_name.split('.')[0].split('_')[1]

    #add a random number in the card's URL. This is to force card update
    random.seed(int(datetime.datetime.now().timestamp()))
    rand=random.randint(10, 100)
    #define card key
    if 'dendrometer' in object_name.split('.')[0]:
        summary_key=summary_path_S3+chart_period+'/'+object_name.split('.')[0].replace('&','_')+'_'+str(rand)+'.html'
    else:
        # key of the summary card
        summary_key=summary_path_S3+chart_period+'/'+object_name.split('.')[0]+'_'+str(rand)+'.html'
    
    #create dict to fill summary template
    summary_info=dict()
    summary_info['title']=chart_period.title()+'chart'
    summary_info['description']='{0} chart of {1}'.format(chart_period.title(),chart_type.title().replace('_',' '))
    summary_info['image_url']='https://s3.amazonaws.com/{0}/{1}'.format(bucket,object_key)
    
    #download template from s3    
    with open('/tmp/template.html', 'wb') as data:
        s3.download_fileobj(bucket, summary_template_S3, data)
    
    #upload summary card to s3
    s3.put_object(
            Bucket=bucket,
            Body=build_summary(summary_info,summary_template_S3),
            Key=summary_key,
            ACL='public-read',
            ContentType='text/html'
        )

    #------publish tweet if it's ID does not exists on dynamoDB table tweetIDs

    #get tweet Ids from dynamoDB
    tweetID=getTweetID(device_UUID,chart_period,chart_type)

    if tweetID != -1:
        #delete old tweet
        delete_tweet(tweetID)
    
    #publish new tweet
    tweet=dict()
    tweet['text']='https://s3.amazonaws.com/{0}/{1}'.format(bucket,summary_key)
    newTweetID=publish_tweet(tweet)['id_str']

    #save new tweet id list on s3
    uploadTweetID(device_UUID,chart_period,chart_type,newTweetID)

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    
    #set root folder
    root='test_2'
    bucket = 'ortobotanico'    
    summary_template_S3 = root+'/template/template_summary.html'
    summary_path_S3=root+'/summarycard/'

    if 'resources' in event:
        #note: cron name syntax: plantUUID_begin or plantUUID_end
        plant_uuid,event_type=event['resources'][0].split('/')[-1].split('_')
        status_tweet(bucket,root,s3,plant_uuid,event_type)
        
    elif 'Records' in event:
        object_key= urllib.parse.unquote(event['Records'][0]['s3']['object']['key'])
        chart_tweet(bucket,object_key,s3,summary_path_S3,summary_template_S3)
    else:
        raise Exception('Trigger event error')