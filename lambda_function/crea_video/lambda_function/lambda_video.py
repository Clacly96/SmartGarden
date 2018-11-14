import datetime
from cv2 import cv2 as cv2
import boto3
import uuid
import json
import subprocess
import os,sys
#from raven import Client portare anche raven prendere con docker
#import credenziali

sys.path.append('/var/task') # serve per specificare la directory dove sono contenuti i moduli che vengono importati nello script python

os.environ['PATH']=os.environ['PATH']+':'+os.environ['LAMBDA_TASK_ROOT'] # serve per aggiungere un path dove cercare file eseguibili quando si richiamano da "terminale"
os.chdir('/tmp') #mi posiziono in tmp che è l'unica cartella dove posso scrivere per evitare problemi con i path relativi

def purge_photos(): #da modificare
    for file in os.listdir('/tmp'):
        if str(file).split('.')[-1]=='jpg' or str(file).split('.')[-1]=='jpeg':
            os.remove('/tmp/{}'.format(str(file)))

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

def retrieve_photos(inizio,fine,percorso,client,bucket):
    if percorso[-1]!="/": #fondamentale per creare un path coerente
        percorso=percorso+"/"

    #inizio_dt=datetime.datetime.strptime(inizio,"%Y-%m-%d").strftime("%Y%m%d") #li trasformo in 2 stringhe per usare direttamente i nomi dei file
    #fine_dt=datetime.datetime.strptime(fine,"%Y-%m-%d").strftime("%Y%m%d") #dato che uso il trucco di mettere sempre 31 giorni a mese non so se mi caccia la corretta data
    inizio_dt=''.join(inizio.split('-'))
    fine_dt=''.join(fine.split('-'))
    inizio_dt=inizio_dt+'0000' #necessario per uniformare le date passate dal file ai nomi delle foto
    fine_dt=fine_dt+'2359'
    # questo discorso è valido per la settimana, distinguere i 3 casi settimana |mese| anno
    mese1=True
    if inizio_dt[0:6]!=fine_dt[0:6]: #controllo necessario per listare correttamente tutte le possibili foto nelle settimane a cavallo tra due mesi, così da listare entrambi i mesi
        try:
            lista_oggetti=client.list_objects(Bucket=bucket,Prefix=percorso+inizio_dt[0:6])['Contents']
        except:
            mese1=False #significa che nel primo mese listato non c'erano foto
            pass
        try:
            lista_oggetti.update(client.list_objects(Bucket=bucket,Prefix=percorso+fine_dt[0:6])['Contents'])
        except:
            if mese1:
                pass
            else:
                raise ValueError('No photos in date range.')
        #necessario un try per vedere se effettivamente non torna un qualcosa di vuoto perchè magari non ci sono key in un determinato mese
    else:
        try:
            lista_oggetti=client.list_objects(Bucket=bucket,Prefix=percorso+fine_dt[0:6])['Contents']
        except:
            raise ValueError('No photos in date range.')

    path_list=[]
    for oggetto in lista_oggetti:
        try:
            date_name=oggetto['Key'].split('/')[-1]
            data_int=int(date_name.split('.')[0])
            if data_int>=int(inizio_dt) and data_int<=int(fine_dt):
                path_list.append('/tmp/{}'.format(date_name))
                with open(path_list[-1], 'wb') as file:
                    client.download_fileobj(bucket, oggetto['Key'], file)
        except KeyError:
            #inserire eventualmente il log
            pass
    return path_list

def crea_video(inizio,fine,percorso,fps,grayscale,frame_width,frame_height,nome_video,client,bucket):
    #try:
    path_list=retrieve_photos(inizio,fine,percorso,client,bucket)
    out = cv2.VideoWriter('/tmp/{}.avi'.format(nome_video),cv2.VideoWriter_fourcc(*'MJPG'), fps, (frame_width,frame_height))

    for photo_file in path_list:
        if grayscale==1:
            img=cv2.imread(photo_file,cv2.IMREAD_GRAYSCALE)
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif grayscale==0:
            img=cv2.imread(photo_file,cv2.IMREAD_ANYCOLOR)
        # shape restituisce (altezza,larghezza,num_canali)
        #calcolo nuove dimensioni
        if img.shape[0]!=frame_height or img.shape[1]!=frame_width:
            frame=ridimensiona(img,frame_height,frame_width)
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
    #except Exception e:
        #sentry.captureException()
        #sentry.captureMessage('Something went fundamentally wrong')




def crea_video_anno(anno,percorso,fps,grayscale,frame_width,frame_height,nome_video,client,bucket):
    new_thumbpath='/tmp/thumbnail'
    subprocess.call('mkdir {}'.format(new_thumbpath).split())
    new_thumbpath=new_thumbpath+'/thumbnail.jpg'
    text_list_path='/tmp/lista_video.txt'
    text_list=open(text_list_path,'w') # lo apro in scrittura di stringhe e non wb cioè come scrittura a byte

    for mese in range(1,10):
        try:
            thumbnail= crea_video(
                                    '{}-0{}-01'.format(anno,mese),
                                    '{}-0{}-31'.format(anno,mese), #considero che ogni mese ha 31 giorni, serve solo per prendere tutte le foto del mese in ogni caso
                                    percorso,
                                    int(fps),
                                    int(grayscale),
                                    int(frame_width),
                                    int(frame_height),
                                    str(mese), #da riconsiderare come fare le info video dato che il nome è legato alla singola piantina quindi univoco e non basta un singolo file di config in quel modo sennò
                                    client,
                                    bucket
                                    )
            #necessario cancellare le foto del mese
            subprocess.call('cp {} {}'.format(thumbnail,new_thumbpath).split()) #bisogna salvare la thumbnail
            purge_photos()
            text_list.write('file \'{}.avi\'\n'.format(str(mese)))
        except Exception as e:
            pass #mese in cui non ci sono foto

    for mese in range(10,13):
        try:
            thumbnail= crea_video(
                                    '{}-{}-01'.format(anno,mese),
                                    '{}-{}-31'.format(anno,mese), #considero che ogni mese ha 31 giorni, serve solo per prendere tutte le foto del mese in ogni caso
                                    percorso,
                                    int(fps),
                                    int(grayscale),
                                    int(frame_width),
                                    int(frame_height),
                                    str(mese), #da riconsiderare come fare le info video dato che il nome è legato alla singola piantina quindi univoco e non basta un singolo file di config in quel modo sennò
                                    client,
                                    bucket
                                    )
            subprocess.call('cp {} {}'.format(thumbnail,new_thumbpath).split())
            purge_photos()
            text_list.write('file \'{}.avi\'\n'.format(mese))

        except Exception as e:
            pass #mese in cui non ci sono foto
    text_list.close()
    comando='ffmpeg -f concat -safe 0 -i {} -c copy {}.avi'.format(text_list_path,nome_video) #attenzione ai path perchè posso scrivere solo dentro a /tmp
    subprocess.call(comando.split())
    return new_thumbpath

def converti_video(path_in,path_out):
    comando='ffmpeg -i {0} -c:v libx264 -movflags +faststart -tune stillimage -preset faster {1}'.format(path_in,path_out) #faststart serve per i video sul web
    try:
        subprocess.call(comando.split()) # usa split per passargli la stringa di comando come tupla
    except Exception as e:
        #url_sentry
        pass


def handler(event, context):
    s3 = boto3.client('s3')
    #sentry = Client(credenziali.url_sentry)


    bucket = event['Records'][0]['s3']['bucket']['name']
    key_conf = event['Records'][0]['s3']['object']['key']
    id_plant= key_conf.split('/')[-3]
    local_conf_path = '/tmp/{}'.format(key_conf.split("/")[-1])
    root=key_conf.split('/')[0]

    #scarica il file di configurazione
    with open(local_conf_path, 'wb') as data:
        s3.download_fileobj(bucket, key_conf, data)
    with open(local_conf_path, 'r') as f:
        config = json.load(f)
    # thumbnail è il path dell'immagine che verrà usata come thumbnail, cioè l'ultima
    if(key_conf.split('/')[-1].split('.')[0]!='anno'):
        thumbnail= crea_video(
                                str(config['data_inizio']),
                                str(config['data_fine']),
                                '{}/foto/{}'.format(root,id_plant),
                                int(config['fps']),
                                int(config['grayscale']),
                                int(config['frame_width']),
                                int(config['frame_height']),
                                str(config['info_video']['nome']), #da riconsiderare come fare le info video dato che il nome è legato alla singola piantina quindi univoco e non basta un singolo file di config in quel modo sennò
                                s3,
                                bucket
                                )
    else:
        thumbnail=crea_video_anno(
                                    str(config['anno']),
                                    '{}/foto/{}'.format(root,id_plant),
                                    int(config['fps']),
                                    int(config['grayscale']),
                                    int(config['frame_width']),
                                    int(config['frame_height']),
                                    str(config['info_video']['nome']), #da riconsiderare come fare le info video dato che il nome è legato alla singola piantina quindi univoco e non basta un singolo file di config in quel modo sennò
                                    s3,
                                    bucket
                                    )


    video_path_avi = '/tmp/{}.avi'.format(config['info_video']['nome'])
    video_path_dest = '/tmp/{0}.{1}'.format(config['info_video']['nome'],config['info_video']['estensione'])

    converti_video(video_path_avi,video_path_dest)

    with open(thumbnail, 'rb') as video:
        s3.upload_fileobj(video,
                                bucket,
                                '{}/video/{}/thumbnail/{}.jpg'.format(root,id_plant,config['info_video']['nome']),
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
                                '{}/video/{}/{}.{}'.format(root,id_plant,config['info_video']['nome'],config['info_video']['estensione']),
                                ExtraArgs={
                                    "ACL": "public-read",
                                    "Metadata": {
                                        "height": str(config['frame_height']),
                                        "width":str(config['frame_width'])
                                        }
                                    })
