import boto3,jinja2,json
from twython import Twython
import credentials

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

def publish_tweet(tweet,local_chart_path=None):
    #get credentials
    twitter = Twython(credentials.consumer_key,credentials.consumer_secret,credentials.access_token,credentials.access_token_secret)
    #publish tweet; publish chart only if path is given    
    if local_chart_path==None:
        if 'site' in tweet:
            twitter.update_status(status=tweet['text'], lat=tweet['site'][1],long=tweet['site'][0])
        else:
            twitter.update_status(status=tweet['text'])
    else:
        #upload chart, get media id and publish tweet with media
        chart = open(local_chart_path, 'rb')
        response = twitter.upload_media(media=chart)
        twitter.update_status(status=tweet['text'], media_ids=[response['media_id']])

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
    
    #period of chart (week or month or day)
    chart_period=object_key.split('/')[-2]
    
    #type of chart (umidity, ...)
    chart_type=object_name.split('.')[0].split('_')[1]
    
    # key of the summary card
    summary_key=summary_path_S3+chart_period+'/'+object_name.split('.')[0]+'.html'
    
    #test if card exists
    try:
        s3.get_object(Bucket='ortobotanico',Key=summary_key)
        exists=True
    except:
        exists=False
        pass
    
    #create dict to fill summary template
    summary_info=dict()
    summary_info['title']=chart_period.title()+'chart'
    summary_info['description']='{0} chart of {1}'.format(chart_period.title(),chart_type.title())
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

    #publish tweet only if card does not exists on s3
    if exists == False:
        tweet=dict()
        tweet['text']='https://s3.amazonaws.com/{0}/{1}'.format(bucket,summary_key)
        publish_tweet(tweet)

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
        object_key=event['Records'][0]['s3']['object']['key']
        chart_tweet(bucket,object_key,s3,summary_path_S3,summary_template_S3)
    else:
        raise('Trigger event error')

