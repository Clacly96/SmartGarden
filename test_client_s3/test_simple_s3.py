import botocore
import boto3
import numpy as np
import sys,os,datetime,piexif
import cv2.cv2 as cv2

nome_bucket = "ortobotanico"
path_oggetto = "test/IN/2.jpg"
nome_oggetto=(path_oggetto.split("/"))[2]
download_path = 'tmp/in/{}{}'.format("1a", nome_oggetto)
upload_path = 'tmp/out/{}'.format(nome_oggetto)
s3 = boto3.resource('s3')
bucket = s3.Bucket(nome_bucket)
try:
    #s3.meta.client.head_bucket(Bucket='ortobotanico')
    #FONDAMENTALI I PERMESSI
    info=bucket.download_file(path_oggetto,download_path) # I PERMESSI
    img=cv2.imread(download_path,cv2.IMREAD_GRAYSCALE)
    cv2.imwrite(upload_path,img)
    bucket.upload_file(upload_path, 'test/OUT/'+nome_oggetto,ExtraArgs={'ACL':'public-read'}) # importante impostare i PERMESSI

    print(info)
except botocore.exceptions.ClientError as e:
    # If a client error is thrown, then check that it was a 404 error.
    # If it was a 404 error, then the bucket does not exist.
    error_code = e.response['Error']['Code']
    if error_code == '404':
        exists = False
