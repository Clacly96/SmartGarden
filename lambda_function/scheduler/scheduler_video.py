import json
import boto3
import datetime
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
# Automatically report all uncaught exceptions
sentry_sdk.init(
    dsn="url_sentry",
    integrations=[AwsLambdaIntegration()]
)

# from the type create a json, that is the config file, the json file upload on s3 will trigger the activation of the creation of the video through the video lambda function
def create_json(type,time): #type è uno dei valori (settimana,mese,year)
    json_dict={}
    json_dict["info_video"]={}
    if type=='year':
        json_dict["year"]=str(time.year)
        json_dict["fps"]="10"
        json_dict["grayscale"]="0"
        json_dict["frame_width"]="1280"
        json_dict["frame_height"]="720"
        json_dict["info_video"]["name"]="year"
        json_dict["info_video"]["format"]="H264"
        json_dict["info_video"]["extension"]="mp4"

    elif type=='month':
        end=time
        delta=datetime.timedelta(days=end.day-1)
        begin=end-delta
        json_dict["begin_date"]=begin.strftime('%Y-%m-%d')
        json_dict["end_date"]=end.strftime('%Y-%m-%d')
        json_dict["fps"]="3"
        json_dict["grayscale"]="0"
        json_dict["frame_width"]="1280"
        json_dict["frame_height"]="720"
        json_dict["info_video"]["name"]="month"
        json_dict["info_video"]["format"]="H264"
        json_dict["info_video"]["extension"]="mp4"

    elif type=='week':
        week_day=time.weekday() #necessary to understand what the day of the week is date_extend.tm_wday (Monday 0)
        delta=datetime.timedelta(days=week_day)
        begin=time-delta
        delta=datetime.timedelta(days=6-week_day)
        end=time+delta
        json_dict["begin_date"]=begin.strftime('%Y-%m-%d')
        json_dict["end_date"]=end.strftime('%Y-%m-%d')
        json_dict["fps"]="1"
        json_dict["grayscale"]="0"
        json_dict["frame_width"]="1280"
        json_dict["frame_height"]="720"
        json_dict["info_video"]["name"]="week"
        json_dict["info_video"]["format"]="H264"
        json_dict["info_video"]["extension"]="mp4"
    else:
        raise ValueError('No good types of config.')
    return json_dict


def lambda_handler(event, context):
    s3 = boto3.client('s3')

    root='demo' # necessary to change it in case of the root is changed
    bucket = 'ortobotanico'
    # list of all the plant presents in photo, they are prefixes
    list_key_plant=s3.list_objects(Bucket=bucket,Prefix='{}/foto/'.format(root),Delimiter='/')['CommonPrefixes'] # retrieve prefixes not keys
    type_ev=event['resources'][0].split('/')[-1].split('_')[0]
    date_time=event['time'] #get time event for the correct creation of json file, because in the json file there are dates
    date_time=datetime.datetime.strptime(date_time.split('.')[0],'%Y-%m-%dT%H:%M:%SZ')  # create the date object
    # i need a delta because the event has a date of the day after the year, month, week whose video you want to create
    delta=datetime.timedelta(days=1)

    json_dict=create_json(type_ev,date_time-delta)




    key_json='{}/video/{}/config/{}.json'.format(root,list_key_plant[0]['Prefix'].split('/')[-2],type_ev) #key of the first config file to upload to the first plant
    path_local_json='/tmp/{}.json'.format(type_ev)
    # upload of the first file
    with open(path_local_json,'w') as file:
        json.dump(json_dict,file)
    with open(path_local_json,'rb') as file:
        s3.upload_fileobj(file,bucket,key_json)
    # copy directly throgh s3 of the config file from the first plant on all the others plant
    for index in range(1,len(list_key_plant)):
        new_key='{}/video/{}/config/{}.json'.format(root,list_key_plant[index]['Prefix'].split('/')[-2],type_ev)
        s3.copy_object(CopySource='{0}/{1}'.format(bucket,key_json),Bucket=bucket,Key=new_key)
