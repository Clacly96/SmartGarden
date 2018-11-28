import json
import boto3
import datetime
import piexif
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
# Automatically report all uncaught exceptions
sentry_sdk.init(
    dsn="url_sentry",
    integrations=[AwsLambdaIntegration()]
)
s3 = boto3.client('s3')

# verify that the string date_text is a correct date format in string like YYYYMMDDHHMM
def validate(date_text):
    try:
        # takes the date as a date_text string then tries to transform it into a datetime object following the regex indicated in the second argument, if it fails it means that the name is not correct
        datetime.datetime.strptime(date_text, '%Y%m%d%H%M')
        return True
    except ValueError:
        return False
# from the type create a json, that is the config file, for the creation of twitter player card
def create_json(type,id_plant,thumbnail_url): #type is year || month || week
    if type=='year':
        json={}
        json["id_plant"]=id_plant
        json["title"]="Year-span video of {}".format(id_plant) #in future will be the name fetched from the db,
        json["description"] ="A timelaps of the past year"
        json["url_image"]=thumbnail_url
    elif type=='month':
        json={}
        json["id_plant"]=id_plant
        json["title"]="Month-span video of {}".format(id_plant) #in future will be the name fetched from the db
        json["description"] ="A timelaps of the past month"
        json["url_image"]=thumbnail_url
    elif type=='week':
        json={}
        json["id_plant"]=id_plant
        json["title"]="Week-span video of {}".format(id_plant) #in future will be the name fetched from the db
        json["description"] ="A timelaps of the past week"
        json["url_image"]=thumbnail_url
    else:
        raise ValueError('No good types of config.')
    return json

# check if the name of the file that uploaded on s3 is correct or not, if the name isn't correct the function rename the file with the correct name based on the date the photo was captured, through the piexiff info
def check_name(name,format,bucket,key,temp,path_key,client):
    if len(name)!=12 or validate(name) is False:
        #download the file
        with open(temp,'wb') as photo:
            client.download_fileobj(bucket,key, photo)

    #reads the date from  piexif and creates the correct name to give file as key
        try:
            exif_photo=piexif.load(temp)
            #strptipe transforms the piexif data into a datetime object and then with strftime from the datetime object creates the formatted string as desired
            name=datetime.datetime.strptime(exif_photo['0th'][piexif.ImageIFD.DateTime].decode('utf-8'),'%Y:%m:%d %H:%M:%S').strftime('%Y%m%d%H%M')
            new_key='{0}/{1}.{2}'.format(path_key,name,format)
            #for rename an object on s3 is necessary to copy the object that you want to rename with a new (desired) key and then delet the object with old key
            client.copy_object(CopySource='{0}/{1}'.format(bucket,key),Bucket=bucket,Key=new_key)
            client.delete_object(Bucket=bucket,Key=key)
        except Exception as e:
            raise ValueError('No piexif in photo')

def check_config(bucket,root,id_plant,client):
    miss_conf={'year':True,'month':True,'week':True} #list of missing file
    try: #look for all the playercard's config files
        conf_list=client.list_objects(Bucket=bucket,Prefix='{}/twitter/card/{}/config/'.format(root,id_plant))['Contents']
        matches = [x for x in conf_list if x['Key'].split('.')[-1]=='json'] # list with only the json file of the s3 dir
        if len(matches)>=3: #if there are at least  3 json file there will be ,arguably ,year, month, week configuration file, so this cut the exucution of this lambda_function to improve the performance
            return 0
        for conf in conf_list:
            name=conf['Key'].split('/')[-1].split('.')[0]
            if name=='year':
                miss_conf['year']=False
            elif name=='month':
                miss_conf['month']=False
            elif name=='week':
                miss_conf['week']=False
    except:
        pass #if all the config files are missing

    list_json={} # dict of object that will be exported as .json files and will be uploaded to s3
    for conf_key,val in miss_conf.items():
        if val==True:
            path_json='/tmp/{}.json'.format(conf_key)
            thumbnail_url="https://{}.s3.amazonaws.com/{}/video/{}/thumbnail/{}.jpg".format(bucket,root,id_plant,conf_key)
            list_json[conf_key]=create_json(conf_key,id_plant,thumbnail_url)
            with open(path_json,'w') as file:
                json.dump(list_json[conf_key],file)
            with open(path_json,'rb') as file:
                client.upload_fileobj(file,bucket,'{}/twitter/card/{}/config/{}.json'.format(root,id_plant,conf_key))

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    path_key=key[::-1].split('/',1)[1][::-1] # is used to find the path of the object from s3 split on the string turned in reverse so as to split only the first / and then separate the path from the file name and then take the turned string of the path and turn it again
    date_name,format=key.split('/')[-1].split('.') #takes the file name and gets the name of the file (which should be the date) and the format
    file_tmp="/tmp/photo"
    id_plant=key.split('/')[-2]
    root=key.split('/')[0]
    check_name(date_name,format,bucket,key,file_tmp,path_key,s3)
    check_config(bucket,root,id_plant,s3)
