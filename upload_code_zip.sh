CODEPATH=$1
FUNCTION=$2
BUCKET=$3
KEY=$4

cd $CODEPATH
#zip all

zip archivio.zip *
# upload on s3 the zip coantains the code
aws s3 cp archivio.zip s3://$BUCKET/$KEY
# update the code of the lambda function from s3 object
aws lambda update-function-code --function-name $FUNCTION --s3-bucket $BUCKET --s3-key $KEY
# delete zip
rm archivio.zip
