import boto3

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('devicedata')

    #get all dendrometer data from event
    dendrometers_data=dict()
    for key in event:
        if 'dendrometerCh' in key:
            dendrometers_data[key]=str(event[key])
    item={
        "UUID": str(event['deviceUUID']),
        "timestamp": str(event['timestamp']),
        "temperature": str(event['temperature']),
        "umidity": str(event['umidity']),
    }
    #add dendrometer data to item dict
    item.update(dendrometers_data)
    #insert data into the table
    resp=table.put_item(Item=item)

    if resp['ResponseMetadata']['HTTPStatusCode']==200:
        return {
            'statusCode': 200,
            'body': 'Data entered successfully'
        }