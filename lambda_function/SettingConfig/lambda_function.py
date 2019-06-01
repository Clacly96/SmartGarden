import boto3,json

def put_plant_info(data):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('plant')
    resp=table.put_item(
        Item=data)
    print(resp)
    if (resp['ResponseMetadata']['HTTPStatusCode']==200):
        return 0
    else:
        return -1

def put_configTemplateFile(bucket,objectType,data):
    s3 = boto3.client('s3')
    key=data['S3FileKey']
    del data['S3FileKey']
    if objectType=='template':
        body=data['S3TemplateContent'].encode('utf-8')
    elif objectType=='configFile':
        body=json.dumps(data).encode('utf-8')
    #define correct content type with file extension
    if (key.split('.')[-1]=='json'):
        contentType='application/json'
    elif (key.split('.')[-1]=='txt'):
        contentType='text/plain'
    elif (key.split('.')[-1]=='html'):
        contentType='text/html'

    resp = s3.put_object(
        Body=body,
        Bucket=bucket,
        Key=key,
        ContentType=contentType,
    )
    if (resp['ResponseMetadata']['HTTPStatusCode']==200):
        return 0
    else:
        return -1

def get_plant_mockup(bucket,fileName):
    s3 = boto3.client('s3')
    resp=s3.get_object(
            Bucket=bucket,
            Key=fileName,
        )
    data=json.loads(resp['Body'].read())
    data['S3FileKey']=fileName
    try:
        return {"data":data}
    except:
        return resp

def get_plant_info(objName):
    #get plant info from dynamodb
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('plant')
    if objName=='list':
        resp=table.scan(
            AttributesToGet=['plantUUID','name']
        )
    else:
        resp=table.get_item(
            Key={'plantUUID': str(objName)}
        )

    try: #list case
        return {"items":resp['Items'], "count":resp['Count'], "type":"plant"} 
    except KeyError:
        return {"data":resp['Item']}
    except:
        return -1

def get_configTemplateFile(objectType,bucket,folder,fileName):
    s3 = boto3.client('s3')
    if fileName=='list':
        resp = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=folder,
        )
        fileList=[]
        for element in resp['Contents']:
            if(element['Key']!=folder):
                fileList.append(
                    {
                        'Key':element['Key']
                    }
                )

        return {"items":fileList,"count":resp['KeyCount'], "type":objectType} 
        
    else:
        resp=s3.get_object(
            Bucket=bucket,
            Key=fileName,
        )
        if (objectType=='template'):
            data={}
            data['S3TemplateContent']=resp['Body'].read().decode()
            data['S3FileKey']=fileName
        elif (objectType=='configFile'):
            data=json.loads(resp['Body'].read())
            data['S3FileKey']=fileName

        try:
            return {"data":data}
        except:
            return resp


def lambda_handler(event, context):    
    root='test_2/'   #set root folder
    bucket = 'ortobotanico'     #set bucket
    configFolder=root+'config/'   #set config folder
    templateFolder=root+'template/'     #set template folder
    plantMockup=root+'mockupPlant.json'

    requestType=event['reqType'] #e.g. read or write
    objectType=event['objType'] # plant | device | plant_device | configFile | template
    #Note: if objName==list, will be send a list of all table's records
    if requestType == 'read':
        if objectType == 'plant':            
            resp=get_plant_info(event['objName']) #event['objName'] must be a plantUUID
        elif objectType == 'configFile':
            resp=get_configTemplateFile(objectType,bucket,configFolder,event['objName']) #event['objName'] must be name of a S3 config file's path e.g. root/config/graph_config.json
        elif objectType == 'template':
            resp=get_configTemplateFile(objectType,bucket,templateFolder,event['objName']) #event['objName'] must be name of a S3 template's path e.g. root/template/template_begin.txt
    
    elif requestType == 'write':
        if objectType == 'plant':            
            resp=put_plant_info(event['data']) #event['objName'] must be a json with all field of a plant item
        elif objectType == 'configFile':
            resp=put_configTemplateFile(bucket,objectType,event['data']) #event['objName'] must be name of a S3 config file's path e.g. root/config/graph_config.json
        elif objectType == 'template':
            resp=put_configTemplateFile(bucket,objectType,event['data']) #event['objName'] must be name of a S3 template's path e.g. root/template/template_begin.txt
    
    elif requestType == 'insert':
        if objectType == 'plant':            
            resp=get_plant_mockup(bucket,plantMockup) #event['objName'] must be a json with all field of a plant item
    print(resp)
    return{
        'body': resp
    }

event={"reqType":"write","objType":"template","data":{"S3TemplateContent":"La pianta {{name}} della specie {{species}}, varietà {{variety}}, è entrata nel suo periodo! Il suo periodo va da {{period_begin}} a {{period_end}}; la pianta è situata: {{site}}. Modificato","S3FileKey":"test_2/template/template_begin.txt"}}
lambda_handler(event,'1')
