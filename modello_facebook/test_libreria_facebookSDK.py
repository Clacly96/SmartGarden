# Questo esempio consente la pubblicazione di un post sulla pagina di cui viene specificato l'access token

import facebook
import credenziali
from raven import Client

try:
    sentry = Client(credenziali.url_sentry)
    graph = facebook.GraphAPI(access_token=credenziali.ac_token, version="3.0")
    messaggio='Hello world!'
    risposta=graph.put_object(parent_object='me', connection_name='feed',message=messaggio)
    print(risposta)
except:
    sentry.captureException()
