import datetime
from cv2 import cv2 as cv2
import boto3
import uuid
import json

def ridimensiona(img,frame_height,frame_width):
    dim_esatta="" # "a" se alt=frame_height "l" altrimenti
    alt,larg=img.shape[:2]
    if alt>larg:
        nuova_alt=frame_height
        nuova_larg=larg*frame_height/alt
        dim_esatta="a"
        if nuova_larg>frame_width:
            alt=nuova_alt
            larg=nuova_larg
            nuova_larg=frame_width
            nuova_alt=alt*frame_width/larg
            dim_esatta="l"
    elif larg>alt:
        nuova_larg=frame_width
        nuova_alt=alt*frame_width/larg
        dim_esatta="l"
        if nuova_alt>frame_height:
            alt=nuova_alt
            larg=nuova_larg
            nuova_alt=frame_height
            nuova_larg=larg*frame_height/alt
            dim_esatta="a"

    img_r = cv2.resize(img, (int(nuova_larg),int(nuova_alt)), interpolation = cv2.INTER_AREA)
    if dim_esatta=="a":
        dim_bordo=frame_width-img_r.shape[1]
        frame=cv2.copyMakeBorder(img_r,top=0,bottom=0, left=int(dim_bordo/2), right=int(dim_bordo/2),borderType= cv2.BORDER_CONSTANT,value=[0,0,0] )
    elif dim_esatta=="l":
        dim_bordo=frame_height-img_r.shape[0]
        frame=cv2.copyMakeBorder(img_r,top=int(dim_bordo/2),bottom=int(dim_bordo/2), left=0, right=0,borderType= cv2.BORDER_CONSTANT,value=[0,0,0] )
    # Nel caso in cui il frame con il bordo ha dimensioni diverse dovute ad arrotondamenti ad int, viene ridimensionato con le dimensioni esatte
    if frame.shape[0]!=frame_height or frame.shape[1]!=frame_width:
        frame=cv2.resize(frame, (frame_width,frame_height), interpolation = cv2.INTER_AREA)
    return frame

def crea_video(inizio,fine,percorso,fps,grayscale,frame_width,frame_height,info_video,s3,nome_bucket):
    if percorso[-1]!="/":
        percorso=percorso+"/"
    
    inizio_dt=datetime.datetime.strptime(inizio,"%Y-%m-%d")
    fine_dt=datetime.datetime.strptime(fine,"%Y-%m-%d")

    out = cv2.VideoWriter('/tmp/{}.{}'.format(info_video['nome'],info_video['estensione']),cv2.VideoWriter_fourcc(*info_video['formato']), fps, (frame_width,frame_height))

    vettore_file_data={}
    lista_oggetti=s3.list_objects(Bucket=nome_bucket,Prefix=percorso)['Contents']
   
    for oggetto in lista_oggetti:
        try:
            data=s3.get_object(Bucket='ortobotanico',Key=oggetto['Key'])['Metadata']['data_creazione']
            data_dt=datetime.datetime.strptime(data,"%Y:%m:%d %H:%M:%S")
            if data_dt>=inizio_dt and data_dt<=fine_dt:                
                nome_foto=oggetto['Key'].split("/")[-1]
                with open('/tmp/{}'.format(nome_foto), 'wb') as data:
                    s3.download_fileobj(nome_bucket, oggetto['Key'], data)
                vettore_file_data[data_dt]='/tmp/{}'.format(nome_foto)
                print('[TEST] Foto {} caricata. Con key {}'.format(nome_foto,oggetto['Key']))
        except KeyError:
            #inserire eventualmente il log
            pass

    for key in sorted(vettore_file_data):
        if grayscale==1:
            img=cv2.imread(vettore_file_data[key],cv2.IMREAD_GRAYSCALE)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)            
        elif grayscale==0:
            img=cv2.imread(vettore_file_data[key],cv2.IMREAD_ANYCOLOR)
            print('[TEST] File aperto {}'.format(vettore_file_data[key]))
        # shape restituisce (altezza,larghezza,num_canali)
        #calcolo nuove dimensioni
        if img.shape[0]!=frame_height or img.shape[1]!=frame_width:
            frame=ridimensiona(img,frame_height,frame_width)            
        else:
            frame=img
        # Aggiunta della data
        dimtesto=cv2.getTextSize(str(key),cv2.FONT_HERSHEY_SIMPLEX,1,1)[0] # (larghezza,altezza)
        altezza_rect=dimtesto[1]+10
        cv2.rectangle(frame,(0,frame_height),(frame_width,frame_height-altezza_rect),(0,0,0),-1)
        cv2.putText(frame,str(key),(int((frame_width-dimtesto[0])/2),int(frame_height-(altezza_rect-dimtesto[1])/2)),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),1,cv2.LINE_AA)
        

        out.write(frame)


    out.release()

def handler(event, context):
    s3_client = boto3.client('s3')
    for record in event['Records']:
        nome_bucket = record['s3']['bucket']['name']
        path_oggetto = record['s3']['object']['key'] 
        nome_oggetto=(path_oggetto.split("/"))[-1]
        download_path = '/tmp/{}'.format(nome_oggetto)
        
        
        #scarica il file di configurazione
        with open(download_path, 'wb') as data:
            s3_client.download_fileobj(nome_bucket, path_oggetto, data)
        with open(download_path, 'r') as f:
            config = json.load(f)
        crea_video(
                    str(config['data_inizio']),
                    str(config['data_fine']),
                    str(config['percorso']),
                    int(config['fps']),
                    int(config['grayscale']),
                    int(config['frame_width']),
                    int(config['frame_height']),
                    dict(config['info_video']),
                    s3_client,
                    nome_bucket
                    )
        video_path = '/tmp/{}.{}'.format(config['info_video']['nome'],config['info_video']['estensione'])
        #s3_client.upload_file('/', nome_bucket, "test2/OUT/out.mp4".format(config['nome_video']))
        with open(video_path, 'rb') as data:
            s3_client.upload_fileobj(data, 
                                    nome_bucket, 
                                    'test2/OUT/{}.{}'.format(config['info_video']['nome'],config['info_video']['estensione']),
                                    ExtraArgs={
                                        "ACL": "public-read",
                                        "Metadata": {
                                            "height": int(config['frame_height']),
                                            "width":int(config['frame_width'])}})
        