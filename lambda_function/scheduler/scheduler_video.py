import json
import boto3
import datetime



def create_json(type,time): #type è uno dei valori (settimana,mese,anno)
    json_dict={}
    json_dict["info_video"]={}
    if type=='year':
        json_dict["anno"]=str(time.year)
        json_dict["fps"]="10"
        json_dict["grayscale"]="0"
        json_dict["frame_width"]="1280"
        json_dict["frame_height"]="720"
        json_dict["info_video"]["nome"]="anno"
        json_dict["info_video"]["formato"]="H264"
        json_dict["info_video"]["estensione"]="mp4"

    elif type=='month':
        #rivedere in termini del fatto che la data passata è l'ultimo giorno del mese, quindi  non serve trovare l'ultimo giorno del mese e si può trovare il primo facilmente
        end=time
        delta=datetime.timedelta(days=end.day-1)
        begin=end-delta
        json_dict["data_inizio"]=begin.strftime('%Y-%m-%d')
        json_dict["data_fine"]=end.strftime('%Y-%m-%d')
        json_dict["fps"]="3"
        json_dict["grayscale"]="0"
        json_dict["frame_width"]="1280"
        json_dict["frame_height"]="720"
        json_dict["info_video"]["nome"]="mese"
        json_dict["info_video"]["formato"]="H264"
        json_dict["info_video"]["estensione"]="mp4"

    elif type=='week':
        week_day=time.weekday() #necessario per capire quale sia il giorno della settimana date_extend.tm_wday (Monday 0)
        delta=datetime.timedelta(days=week_day)
        begin=time-delta
        delta=datetime.timedelta(days=6-week_day) #mi interessa la data di domenica
        end=time+delta
        json_dict["data_inizio"]=begin.strftime('%Y-%m-%d')
        json_dict["data_fine"]=end.strftime('%Y-%m-%d')
        json_dict["fps"]="1"
        json_dict["grayscale"]="0"
        json_dict["frame_width"]="1280"
        json_dict["frame_height"]="720"
        json_dict["info_video"]["nome"]="settimana"
        json_dict["info_video"]["formato"]="H264"
        json_dict["info_video"]["estensione"]="mp4"
    else:
        raise ValueError('No good types of config.')
    return json_dict


def lambda_handler(event, context):
    s3 = boto3.client('s3')

    root='demo' # per il momento è demo, in futuro va cambiata se cambia qualcosa
    bucket = 'ortobotanico'
    list_key_plant=s3.list_objects(Bucket=bucket,Prefix='{}/foto/'.format(root),Delimiter='/')['CommonPrefixes'] # non si prendono realmente chiavi, ma prefissi
    type_ev=event['resources'][0].split('/')[-1].split('_')[0]
    #definire il type(anno mese settimana, o year, month,week) a partire dal nome dell'evento weekly_activation ecc ecc

    date_time=event['time'] #prendo il tempo dell'evento
    date_time=datetime.datetime.strptime(date_time.split('.')[0],'%Y-%m-%dT%H:%M:%SZ')  # creo oggetto datetime

    delta=datetime.timedelta(days=1)

    json_dict=create_json(type_ev,date_time-delta)
    #considerare che i trigger parteono il giorno successivo alla settimana, mese,anno di cui vanno fatte

    # lista di tutte le piante presenti in foto

    #una volta creato il file.json corretto upparlo sulla prima pianta della lista e poi copiarlo nelle cartelle di configurazione delle altre piante
    key_json='{}/video/{}/config/{}.json'.format(root,list_key_plant[0]['Prefix'].split('/')[-2],type_ev) #chiave del primo file da caricare per copiare poi sulle altre piante
    path_local_json='/tmp/{}.json'.format(type_ev)

    with open(path_local_json,'w') as file:
        json.dump(json_dict,file)
    with open(path_local_json,'rb') as file:
        s3.upload_fileobj(file,bucket,key_json)

    for index in range(1,len(list_key_plant)):
        new_key='{}/video/{}/config/{}.json'.format(root,list_key_plant[index]['Prefix'].split('/')[-2],type_ev)
        s3.copy_object(CopySource='{0}/{1}'.format(bucket,key_json),Bucket=bucket,Key=new_key)
