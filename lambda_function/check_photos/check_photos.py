import json
import boto3
import datetime
import piexif

s3 = boto3.client('s3')

def validate(date_text):
    try:
        # prende la data come stringa date_text poi prova a trasformarla in un oggetto datetime seguendo la regex indicata nel secondo parametro, se non ci riescie vuol dire che non è corretto il nome
        datetime.datetime.strptime(date_text, '%Y%m%d%H%M')
        return True
    except ValueError:
        return False

def create_json(type,id_plant,thumbnail_url): #type è uno dei valori (settimana,mese,anno)
    if type=='anno':
        json={}
        json["id_pianta"]=id_plant
        json["titolo"]="Year-span video of {}".format(id_plant) #poi ci andrà il nome della pianta preso nel database,
        json["descrizione"] ="A timelaps of the past year"
        json["url_immagine"]=thumbnail_url
    elif type=='mese':
        json={}
        json["id_pianta"]=id_plant
        json["titolo"]="Month-span video of {}".format(id_plant) #poi ci andrà il nome della pianta preso nel database,
        json["descrizione"] ="A timelaps of the past month"
        json["url_immagine"]=thumbnail_url
    elif type=='settimana':
        json={}
        json["id_pianta"]=id_plant
        json["titolo"]="Week-span video of {}".format(id_plant) #poi ci andrà il nome della pianta preso nel database,
        json["descrizione"] ="A timelaps of the past week"
        json["url_immagine"]=thumbnail_url
    else:
        raise ValueError('No good types of config.')
    return json

def check_name(name,format,bucket,key,temp,path_key,client):
    if len(name)!=12 or validate(name) is False:
        #metterci il codice per prendere la data dalla foto con i piexiff e poi rinominare l'oggetto con il corretto nome

        with open(temp,'wb') as photo:
            #scarica il file
            client.download_fileobj(bucket,key, photo)

    #leggi la data da i piexif e crea il nome corretto da dare file come key
        try:
            exif_photo=piexif.load(temp)
            #strptipe trasforma il dato piexif in un oggetto datetime e poi con strftime a partire dall'oggetto datetime si crea la stringa formattata nella maniera voluta
            name=datetime.datetime.strptime(exif_photo['0th'][piexif.ImageIFD.DateTime].decode('utf-8'),'%Y:%m:%d %H:%M:%S').strftime('%Y%m%d%H%M')
        #rinomina il file su s3 se si può
            new_key='{0}/{1}.{2}'.format(path_key,name,format)
            #per rinominare l'oggetto è necessario effettuare una copia dell'oggetto con la nuova chiave e poi cancellare la vecchia copia con la vecchi achiave
            client.copy_object(CopySource='{0}/{1}'.format(bucket,key),Bucket=bucket,Key=new_key)
            client.delete_object(Bucket=bucket,Key=key)
        except Exception as e:
            #sentry
            raise ValueError('No piexif in photo')

def check_config(bucket,root,id_plant,event_time,client):
    miss_conf={'anno':True,'mese':True,'settimana':True} #lista dei file mancanti
    try: #vedo se ci sono file di configurazione presenti
        conf_list=client.list_objects(Bucket=bucket,Prefix='{}/twitter/card/{}/config/'.format(root,id_plant))['Contents']
        matches = [x for x in conf_list if x['Key'].split('.')[-1]=='json'] # prendo solo gli oggetti della lista che hanno come chiave un oggetto json
        if len(matches)>=3: #se sono presenti almeno 3 file json di configurazione si presume che siano anno mese settimana così chiude direttamente l'esecuzione della lambda function, rischioso ma migliora le performance
            return 0
        for conf in conf_list:
            name=conf['Key'].split('/')[-1].split('.')[0]
            if name=='anno':
                miss_conf['anno']=False
            elif name=='mese':
                miss_conf['mese']=False
            elif name=='settimana':
                miss_conf['settimana']=False
    except:
        pass #se non è presente nessun file di config

    list_json={} # dict di oggetti che poi verranno esportati come file .json e caricati su s3
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
    path_key=key[::-1].split('/',1)[1][::-1] # serve a trovare il path dell'oggetto da s3 si fa lo split sulla stringa girata al contrario in maniera da splittare solo il primo / e quindi separare il path dal nome del file e poi prendo la stringa girata del path e la rigiro nuovamente
    date_name,format=key.split('/')[-1].split('.') #prende il nome del file e ne ricava il nome(che dovrebbe essere la data) e il formato
    file_tmp="/tmp/photo"
    id_plant=key.split('/')[-2]
    root=key.split('/')[0]
    date_time=event['Records'][0]['eventTime'] #prendo il tempo dell'evento
    date_time=datetime.datetime.strptime(date_time.split('.')[0],'%Y-%m-%dT%H:%M:%S')  # creo oggetto datetime , il punto serve perchè la data è nel formato 2018-11-08T00:00:00.000Z
    check_name(date_name,format,bucket,key,file_tmp,path_key,s3)
    check_config(bucket,root,id_plant,date_time,s3)
