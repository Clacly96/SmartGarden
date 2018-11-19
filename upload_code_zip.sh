CODEPATH=$1
FUNCTION=$2
BUCKET=$3
KEY=$4

# vado nella cartella
cd $CODEPATH
#zippo tutto il contenuto

zip archivio.zip *
# prima si carica il codice su s3 e poi lo si linka a lambda
aws s3 cp archivio.zip s3://$BUCKET/$KEY
aws lambda update-function-code --function-name $FUNCTION --s3-bucket $BUCKET --s3-key $KEY

rm archivio.zip
