import json
import boto3
import datetime
import piexif

def validate(date_text):
    try:
        # prende la data come stringa date_text poi prova a trasformarla in un oggetto datetime seguendo la regex indicata nel secondo parametro, se non ci riescie vuol dire che non è corretto il nome
        datetime.datetime.strptime(date_text, '%Y%m%d%H%M')
        return True
    except ValueError:
        return False


s3 = boto3.client('s3')


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    path_key=key[::-1].split('/',1)[1][::-1] # serve a trovare il path dell'oggetto da s3 si fa lo split sulla stringa girata al contrario in maniera da splittare solo il primo / e quindi separare il path dal nome del file e poi prendo la stringa girata del path e la rigiro nuovamente
    #date_name= name.split('.')[0]
    #format=name.split('.')[1]
    date_name,format=key.split('/')[-1].split('.') #prende il nome del file e ne ricava il nome(che dovrebbe essere la data) e il formato
    file_tmp="/tmp/photo"

    if len(date_name)!=12 or validate(date_name) is False:
        #metterci il codice per prendere la data dalla foto con i piexiff e poi rinominare l'oggetto con il corretto nome

        with open(file_tmp,'wb') as photo:
            #scarica il file
            s3.download_fileobj(bucket,key, photo)

    #leggi la data da i piexif e crea il nome corretto da dare file come key
        exif_photo=piexif.load(file_tmp)
        #strptipe trasforma il dato piexif in un oggetto datetime e poi con strftime a partire dall'oggetto datetime si crea la stringa formattata nella maniera voluta
        date_name=datetime.datetime.strptime(exif_photo['0th'][piexif.ImageIFD.DateTime].decode('utf-8'),'%Y:%m:%d %H:%M:%S').strftime('%Y%m%d%H%M')
    #rinomina il file su s3 se si può
        new_key='{0}/{1}.{2}'.format(path_key,date_name,format)
        #per rinominare l'oggetto è necessario effettuare una copia dell'oggetto con la nuova chiave e poi cancellare la vecchia copia con la vecchi achiave
        s3.copy_object(CopySource='{0}/{1}'.format(bucket,key),Bucket=bucket,Key=new_key)
        s3.delete_object(Bucket=bucket,Key=key)
