# SmartGarden
This repository was created for a project for UNIVPM, made by Claudio Spada and Roberto Broccoletti with the supervisor A. Mancini.
This project consists of a system for shot daily photos to plants in the botanic garden, process them and post the states on social network like Twitter and Facebook.

## Step 1: testing API of social network
The APIs were tested with POSTMAN; we need for this project APIs for publish a post, a photo and place:

### API for Facebook:
To publish a post on a page, it's required an access token (Facebook uses OAuth 2.0) and the permission to manage pages of user; the advantage of this token is that it can be extended lifetime and for the Facebook policy it isn't possible to use a profile for a company. Therefore we have created a page from a personal profile and after we have obtained access token.
All APIs host is `graph.facebook.com` and the version of APIs is 3.0.
The APIs that we need to use ad the following:
- to publish a post it is necessary to make a POST request on the segment `{page-id}/feed` and in the body of the request insert some parameters like `message` that will contain a string, `link` that can contain a URL or `place` that must contain the ID of a page that represent a place.
- to publish a photo it's required a POST request on the segment `{page-id}/photos` and in the body it's necessary to specify a file or a URL that contains a photo, it's possible to specify also a `caption` and a `place`
- to obtain the ID of a place can be done a GET request on the segment `search` and specify the parameter `type=place` and `q={name-of-place}` or `center=[latitude],[longitude]`. However we cannot obtain the page ID related to place, because the facebook app must be public.

### API for Twitter
To use Twitter's API it's necessary to create an app and get "Consumer Key", "Consumer Secret", "Access Token" and "Token Secret" from the page of the app, because Twitter uses OAuth 1.0; these tokens will not expire.
The APIs that we need to use ad the following:
- to publish a post can be done a POST request to `api.twitter.com/1.1/statuses/update.json` and in the body can be specify parameters like `status` for the text of the post, `lat` and `long` for insert a place and `media_ids` for insert a media.
- media must be uploaded with a POST request to `upload.twitter.com/1.1/media/upload.json` and in the body specify the param `media` and the media file.
