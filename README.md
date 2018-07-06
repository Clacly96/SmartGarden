# SmartGarden
Questa repository è stata creata per il tirocinio di Claudio Spada e Roberto Broccoletti con il relatore A. Mancini dell'UNIVPM.
Il progetto consiste nella creazione di un sistema in grado di scattare foto giornaliere alle piante dell'orto botanico smart, elaborarle e successivamente pubblicare i risultati sui social come Facebook e Twitter

## Step 1: test delle API dei social network
Le API necessarie, per creare post e pubblicare foto con geo tagging sono state testate con l'ausilio di POSTMAN

### API per Facebook:
Per le policy di Facebook non è possibile creare un profilo per una azienda, ma è necessario creare una pagina, quindi le API usate sono per pubblicare contenuti su una pagina Facebook.
Per l'autorizzazione Facebook usa OAuth 2.0, quindi è necessario ottenere un token di accesso che permette la gestione delle pagine create dall'utente. Questo tipo di token per le pagine può essere esteso con durata illimitata. [Info sui token](https://developers.facebook.com/docs/facebook-login/access-tokens/?locale=it_IT)

L'host di tutte le API è `graph.facebook.com` e la versione corrente è la 3.0.
Le API necessarie sono le seguenti:
- per pubblicare un post su una pagina è necessaria una richiesta POST al segmento [`{page-id}/feed`](https://developers.facebook.com/docs/graph-api/reference/v3.0/page/feed) inserendo nel corpo della richiesta parametri come ad esempio `message` che conterrà il testo del post, `link` che contiene un URL o `place` che contiene l'ID di una pagina corrispondende al luogo.
- per pubblicare una foto è necessaria una richiesta POST al segmento [`{page-id}/photos`](https://developers.facebook.com/docs/graph-api/reference/page/photos/) inserendo nel corpo della richiesta il file da caricare o un URL che contiene la foto; è anche possibile specificare una descrizione della foto con `caption` e il luogo con `place`
- per ottenere l'ID di un luogo è necessario usare l'API [`search`](https://developers.facebook.com/docs/places/web/search) specificando i parametri `type=place` e `q={name-of-place}` o `center=[latitude],[longitude]`. Tuttavia con questa richiesta otteniamo l'ID del luogo, ma non possiamo ottenere l'ID della pagina legata al luogo, dato che la nostra applicazione non è ancora pubblica su Facebook e non ha quindi l'autorizzazione per accedere a pagine e profili pubblici.

### API per Twitter
Per usare le API di twitter è necessario creare un'app e recuperare dalla pagina dell'app le seguenti chiavi: "Consumer Key", "Consumer Secret", "Access Token" e "Token Secret", perché Twitter usa OAuth 1.0; questi token non scadono, se non esplicitamente invalidati. [info sui token](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html)

Le API necessarie sono le seguenti:
- per pubblicare un post sul profilo è necessaria una richiesta POST a `api.twitter.com/1.1/statuses/update.json` specificando nel body parametri come ad esempio `status` per il testo del post, `lat` e `long` per inserire la posizione e `media_ids` per inserire l'ID di un media. [reference](https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-statuses-update)
- i media vengono caricati su twitter con una richiesta POST a [`upload.twitter.com/1.1/media/upload.json`](https://developer.twitter.com/en/docs/media/upload-media/api-reference/post-media-upload) specificando nel body il paramentro `media` e il file, in corrispondenza di questo paramentro; la risposta di questa richiesta contiene il media_id.
