import boto3,json
from dynamodb_json import json_util #converts dynamodb json in standard json

def delete_old_item(dynamodb,ev_data):
    try:
        table=dynamodb.Table('plant_device')
        table.delete_item(
                Key={'deviceUUID':ev_data['OldImage']['device']['deviceUUID'],
                    'dendrometerCh':int(ev_data['OldImage']['device']['dendrometerCh'])
                    }
        )
    except:
        pass

def plant_update(dynamodb,ev_data):
    #check if device or dendrometer are changed
    table=dynamodb.Table('plant_device')
    resp=table.get_item(
        Key={'deviceUUID':ev_data['NewImage']['device']['deviceUUID'],
            'dendrometerCh':int(ev_data['NewImage']['device']['dendrometerCh'])
            }
    )
    #if Item with deviceUUID and dendrometerCh already exists, just insert new plant ID
    if 'Item' in resp:
        table.update_item(
            ExpressionAttributeNames={'#PU': 'plantUUID'},
            ExpressionAttributeValues={':u': {'S': ev_data['NewImage']['plantUUID']}},
            Key={'deviceUUID':ev_data['NewImage']['device']['deviceUUID'],
            'dendrometerCh':int(ev_data['NewImage']['device']['dendrometerCh'])
            },
            UpdateExpression='SET #PU = :u',
        )
    #create a new item if does not exists
    else:
        table.put_item(
            Item={
                'deviceUUID':ev_data['NewImage']['device']['deviceUUID'],
                'dendrometerCh':int(ev_data['NewImage']['device']['dendrometerCh']),
                'plantUUID':str(ev_data['NewImage']['plantUUID']),
            }
        )
    #delete old item at the end
    delete_old_item(dynamodb,ev_data)

def lambda_handler(event, context):
    dynamodb=boto3.resource('dynamodb')
    #iterate event object to scan all update from db
    for ev in event['Records']:
        ev_type=ev['eventName']
        ev_data=json_util.loads(ev['dynamodb'])

        if ev_type=='MODIFY' or ev_type=='INSERT':
            plant_update(dynamodb,ev_data)
        elif ev_type=='REMOVE':
            delete_old_item(dynamodb,ev_data)

