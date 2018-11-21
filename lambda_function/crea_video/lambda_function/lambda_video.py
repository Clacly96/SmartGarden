import datetime
from cv2 import cv2 as cv2
import boto3
import uuid
import json
import subprocess
import os,sys
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
# Automatically report all uncaught exceptions
sentry_sdk.init(
    dsn="url_sentry",
    integrations=[AwsLambdaIntegration()]
)


sys.path.append('/var/task')
os.environ['PATH']=os.environ['PATH']+':'+os.environ['LAMBDA_TASK_ROOT']
os.chdir('/tmp') #necessary for use of relative path otherwise ffmpeg  creates problems

# delete all the photos in the tmp dir
def purge_photos():
    for file in os.listdir('/tmp'):
        if str(file).split('.')[-1]=='jpg' or str(file).split('.')[-1]=='jpeg':
            os.remove('/tmp/{}'.format(str(file)))

# resize of the frame of the video, because for render video all the frame must have the same height and width
def resize_frame(img,frame_height,frame_width):
    prop_size="" # proper size, indicates whether to keep the measurement of fixed height or width to recalculate the other
    height,width=img.shape[:2]
    if height>width:
        new_height=frame_height
        new_width=width*frame_height/height
        prop_size="h"
        if new_width>frame_width:
            height=new_height
            width=new_width
            new_width=frame_width
            new_height=height*frame_width/width
            prop_size="w"
    elif width>height:
        new_width=frame_width
        new_height=height*frame_width/width
        prop_size="w"
        if new_height>frame_height:
            height=new_height
            width=new_width
            new_height=frame_height
            new_width=width*frame_height/height
            prop_size="h"

    img_r = cv2.resize(img, (int(new_width),int(new_height)), interpolation = cv2.INTER_AREA)
    if prop_size=="h":
        dim_bordo=frame_width-img_r.shape[1]
        frame=cv2.copyMakeBorder(img_r,top=0,bottom=0, left=int(dim_bordo/2), right=int(dim_bordo/2),borderType= cv2.BORDER_CONSTANT,value=[0,0,0] )
    elif prop_size=="w":
        dim_bordo=frame_height-img_r.shape[0]
        frame=cv2.copyMakeBorder(img_r,top=int(dim_bordo/2),bottom=int(dim_bordo/2), left=0, right=0,borderType= cv2.BORDER_CONSTANT,value=[0,0,0] )
    # in case the frame with border have sizes different from those desired caused by roundings to int (some pixels), is resized to the exact size

    if frame.shape[0]!=frame_height or frame.shape[1]!=frame_width:
        frame=cv2.resize(frame, (frame_width,frame_height), interpolation = cv2.INTER_AREA)
    return frame
# download all and only the photos that are captured in the time frame, return a list of the paths of the photos
def retrieve_photos(begin,end,path,client,bucket):
    if path[-1]!="/": #to create a correct path
        path=path+"/"

    begin_dt=''.join(begin.split('-')) # from YYYY-MM-DD to YYYYMMDD
    end_dt=''.join(end.split('-'))
    begin_dt=begin_dt+'0000' # conform the string with the naming of photos
    end_dt=end_dt+'2359'
    # necessary for weeks at the turn of two months
    month1=True
    if begin_dt[0:6]!=end_dt[0:6]: #check of the month of begin and end of the week, if they are the same month
        try:
            list_obj=client.list_objects(Bucket=bucket,Prefix=path+begin_dt[0:6])['Contents']
        except:
            month1=False #no photo in the first month
            pass
        try:
            list_obj.update(client.list_objects(Bucket=bucket,Prefix=path+end_dt[0:6])['Contents'])
        except:
            if month1:
                pass # there are photos in second month
            else:
                raise ValueError('No photos in date range.')
    else:
        try:
            list_obj=client.list_objects(Bucket=bucket,Prefix=path+end_dt[0:6])['Contents']
        except:
            raise ValueError('No photos in date range.')

    path_list=[]
    for object in list_obj:
        date_name=object['Key'].split('/')[-1]
        data_int=int(date_name.split('.')[0])
        if data_int>=int(begin_dt) and data_int<=int(end_dt):
            path_list.append('/tmp/{}'.format(date_name))
            with open(path_list[-1], 'wb') as file:
                client.download_fileobj(bucket, object['Key'], file)

    return path_list
# make the timelaps in mjpg format and avi extension return the path of thumbnail to upload on s3,
def make_video(begin,end,path,fps,grayscale,frame_width,frame_height,name_video,client,bucket):
    path_list=retrieve_photos(begin,end,path,client,bucket)
    out = cv2.VideoWriter('/tmp/{}.avi'.format(name_video),cv2.VideoWriter_fourcc(*'MJPG'), fps, (frame_width,frame_height))

    for photo_file in path_list:
        if grayscale==1:
            img=cv2.imread(photo_file,cv2.IMREAD_GRAYSCALE)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif grayscale==0:
            img=cv2.imread(photo_file,cv2.IMREAD_ANYCOLOR)
        # shape restituisce (altezza,larghezza,num_canali)
        #calcolo nuove dimensioni
        if img.shape[0]!=frame_height or img.shape[1]!=frame_width:
            frame=resize_frame(img,frame_height,frame_width)
        else:
            frame=img
        # Aggiunta della data
        #la data deve essere trasformata in un formato leggibile
        date=photo_file.split('/')[-1].split('.')[0]
        date='{}-{}-{} {}:{}'.format(date[0:4],date[4:6],date[6:8],date[8:10],date[10:])
        dimtesto=cv2.getTextSize(date,cv2.FONT_HERSHEY_SIMPLEX,1,1)[0] # (larghezza,altezza)
        altezza_rect=dimtesto[1]+10
        cv2.rectangle(frame,(0,frame_height),(frame_width,frame_height-altezza_rect),(0,0,0),-1)
        cv2.putText(frame,date,(int((frame_width-dimtesto[0])/2),int(frame_height-(altezza_rect-dimtesto[1])/2)),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1,cv2.LINE_AA)
        out.write(frame)

    out.release()
    return path_list[-1]

# make the timelapse in case of timeplapse of the year, create 12 videos and merge togheter, necessary because the the size of tmp dir is only 500 MB, purge the photos every month video created
def make_video_year(year,path,fps,grayscale,frame_width,frame_height,name_video,client,bucket):
    new_thumbpath='/tmp/thumbnail'
    subprocess.call('mkdir {}'.format(new_thumbpath).split())
    new_thumbpath=new_thumbpath+'/thumbnail.jpg'
    text_list_path='/tmp/lista_video.txt'
    text_list=open(text_list_path,'w')

    for month in range(1,10):
        try:
            thumbnail= make_video(
                                    '{}-0{}-01'.format(year,month),
                                    '{}-0{}-31'.format(year,month), #I consider that every month has 31 days, serves only to take all the photos of the month in any case
                                    path,
                                    int(fps),
                                    int(grayscale),
                                    int(frame_width),
                                    int(frame_height),
                                    str(month),
                                    client,
                                    bucket
                                    )
            subprocess.call('cp {} {}'.format(thumbnail,new_thumbpath).split()) #save the thumbnail in another dir
            #delete the photos of the month
            purge_photos()
            # write the file that used to concatenate the videos through ffmpeg
            text_list.write('file \'{}.avi\'\n'.format(str(month)))
        except Exception as e:
            pass ## month without photos need to skip to next month

    for month in range(10,13):
        try:
            thumbnail= make_video(
                                    '{}-{}-01'.format(year,month),
                                    '{}-{}-31'.format(year,month),
                                    path,
                                    int(fps),
                                    int(grayscale),
                                    int(frame_width),
                                    int(frame_height),
                                    str(month),
                                    client,
                                    bucket
                                    )
            subprocess.call('cp {} {}'.format(thumbnail,new_thumbpath).split())
            purge_photos()
            text_list.write('file \'{}.avi\'\n'.format(month))

        except Exception as e:
            pass
    text_list.close()
    cmd='ffmpeg -f concat -safe 0 -i {} -c copy {}.avi'.format(text_list_path,name_video)
    subprocess.call(cmd.split())
    return new_thumbpath

# convert timeplapse from mjpg .avi to h264 .mp4, for browsers
def convert_video(path_in,path_out):
    cmd='ffmpeg -i {0} -c:v libx264 -movflags +faststart -tune stillimage -preset faster {1}'.format(path_in,path_out) #faststart serve per i video sul web
    subprocess.call(cmd.split())



def handler(event, context):
    s3 = boto3.client('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key_conf = event['Records'][0]['s3']['object']['key']
    id_plant= key_conf.split('/')[-3]
    local_conf_path = '/tmp/{}'.format(key_conf.split("/")[-1])
    root=key_conf.split('/')[0]

    #download config file for making video
    with open(local_conf_path, 'wb') as data:
        s3.download_fileobj(bucket, key_conf, data)
    with open(local_conf_path, 'r') as f:
        config = json.load(f)
    # thumbnail è il path dell'immagine che verrà usata come thumbnail, cioè l'ultima
    #thumbnail is the path of the image (the last of the video) that will be used as a thumbnail
    if(key_conf.split('/')[-1].split('.')[0]!='year'):
        thumbnail= make_video(
                                str(config['begin_date']),
                                str(config['end_date']),
                                '{}/foto/{}'.format(root,id_plant),
                                int(config['fps']),
                                int(config['grayscale']),
                                int(config['frame_width']),
                                int(config['frame_height']),
                                str(config['info_video']['name']),
                                s3,
                                bucket
                                )
    else:
        thumbnail=make_video_year(
                                    str(config['year']),
                                    '{}/foto/{}'.format(root,id_plant),
                                    int(config['fps']),
                                    int(config['grayscale']),
                                    int(config['frame_width']),
                                    int(config['frame_height']),
                                    str(config['info_video']['name']), 
                                    s3,
                                    bucket
                                    )


    video_path_avi = '/tmp/{}.avi'.format(config['info_video']['name'])
    video_path_dest = '/tmp/{0}.{1}'.format(config['info_video']['name'],config['info_video']['extension'])

    convert_video(video_path_avi,video_path_dest)

    with open(thumbnail, 'rb') as video:
        s3.upload_fileobj(video,
                                bucket,
                                '{}/video/{}/thumbnail/{}.jpg'.format(root,id_plant,config['info_video']['name']),
                                ExtraArgs={
                                    "ACL": "public-read",
                                    "Metadata": {
                                        "height": str(config['frame_height']),
                                        "width":str(config['frame_width'])
                                        }
                                    })
    with open(video_path_dest, 'rb') as video:
        s3.upload_fileobj(video,
                                bucket,
                                '{}/video/{}/{}.{}'.format(root,id_plant,config['info_video']['name'],config['info_video']['extension']),
                                ExtraArgs={
                                    "ACL": "public-read",
                                    "Metadata": {
                                        "height": str(config['frame_height']),
                                        "width":str(config['frame_width'])
                                        }
                                    })
