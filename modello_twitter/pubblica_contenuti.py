from twython import Twython
import credenziali 

def pubblica_video(percorso,messaggio,luogo=None):
    twitter = Twython(credenziali.consumer_key,credenziali.consumer_secret,credenziali.access_token,credenziali.access_token_secret)
    video = open(percorso, 'rb')
    response = twitter.upload_video(media=video, media_type='video/mp4')
    if luogo==None:
        twitter.update_status(status=messaggio, media_ids=[response['media_id']])
    else:
        twitter.update_status(status=messaggio, media_ids=[response['media_id']],place_id=luogo)

def pubblica_immagine(percorso,messaggio,luogo=None):
    twitter = Twython(credenziali.consumer_key,credenziali.consumer_secret,credenziali.access_token,credenziali.access_token_secret)
    photo = open(percorso, 'rb')
    response = twitter.upload_media(media=photo)
    if luogo==None:
        twitter.update_status(status=messaggio, media_ids=[response['media_id']])
    else:
        twitter.update_status(status=messaggio, media_ids=[response['media_id']],place_id=luogo)


def pubblica_stato(messaggio,luogo):
    twitter = Twython(credenziali.consumer_key,credenziali.consumer_secret,credenziali.access_token,credenziali.access_token_secret)
    if luogo==None:
        twitter.update_status(status=messaggio)
    else:
        twitter.update_status(status=messaggio,place_id=luogo)

def cerca_luogo(nome,granularity='city',max_risultati=3):
    twitter = Twython(credenziali.consumer_key,credenziali.consumer_secret,credenziali.access_token,credenziali.access_token_secret)
    search_param={'query':nome,'granularity':granularity,'max_results':max_risultati}
    luoghi = twitter.search_geo(**search_param)
    print(luoghi)

if __name__=="__main__":
    pubblica_video("C:/Users/claud/Desktop/Tirocinio/modulo_mp4/video_out.mp4","Prova video")
