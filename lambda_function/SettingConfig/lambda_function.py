import boto3,json,random
import matplotlib.pyplot as plt

def create_preview(chart_path_S3,bucket_name,chart_config):
    fig_path='/tmp/'

    variableA=[i for i in range(1,31)]
    variableB=[random.randint(10, 100) for i in range(1,31)]
    random.seed(10)
    variableC=[random.randint(10, 100) for i in range(1,31)]
    #create chart with matplotlib
    fig, ax1 = plt.subplots(figsize=(chart_config['figureWidth'], chart_config['figureHeight']),dpi=chart_config['figureDPI'])
    ax1.grid(which='major', axis='x', linestyle='--')
    ax1.set_title(label='Chart\'s preview',fontsize=chart_config['titleSize'],pad=chart_config['labelPadding'])
    ax1.plot(variableA, 
            variableB,
            color=chart_config['color'],
            marker=chart_config['marker'],
            linestyle=chart_config['linestyle'],
            linewidth=chart_config['linewidth'], 
            markersize=chart_config['markersize'],
            scalex=chart_config['scalex'],
            scaley=chart_config['scaley'],
        )
    ax1.set_ylabel('Variable label A', color=chart_config['color'],fontsize=chart_config['labelSize'],labelpad=chart_config['labelPadding'])
    ax1.set_xlabel(chart_config['xlabel'],fontsize=chart_config['labelSize'],labelpad=chart_config['labelPadding'])
    ax1.tick_params(axis='x',labelsize=chart_config['labelValueSize'],pad=chart_config['labelValuePadding'])  
    ax1.tick_params(axis='y', labelcolor=chart_config['color'],labelsize=chart_config['labelValueSize'],pad=chart_config['labelValuePadding'])        
    plt.xticks(rotation='vertical') #rotate x label

    ax2 = ax1.twinx()   #generate ax2 with same x axe
    ax2.plot(variableA, 
            variableC,
            color=chart_config['color2'],
            marker=chart_config['marker'],
            linestyle=chart_config['linestyle'],
            linewidth=chart_config['linewidth'], 
            markersize=chart_config['markersize'],
        )
    ax2.set_ylabel('Variable label B', color=chart_config['color2'], fontsize=chart_config['labelSize'],labelpad=chart_config['labelPadding'])
    ax2.tick_params(axis='y', labelcolor=chart_config['color2'], labelsize=chart_config['labelValueSize'],pad=chart_config['labelValuePadding']) 
    
    plt.savefig(''.join([fig_path,'chartPreview.png']))

    s3_client=boto3.client('s3')
    with open(''.join([fig_path,'chartPreview.png']), 'rb') as data:
        s3_client.upload_fileobj(data, 
                                bucket_name,
                                chart_path_S3+'chartPreview.png',
                                ExtraArgs={
                                    "ACL": "public-read",
                                    })
    
    return 'https://s3.amazonaws.com/{0}/{1}'.format(bucket_name,chart_path_S3+'chartPreview.png')

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
    root = 'test_2/'   #set root folder
    bucket = 'ortobotanico'     #set bucket
    configFolder = root + 'config/'   #set config folder
    templateFolder = root + 'template/'     #set template folder
    plantMockup = root + 'mockupPlant.json' #set mockup for plant form
    chartPreviewPath = root + 'chart/preview/'  #set folder for chart preview

    requestType=event['reqType'] #e.g. read, write, chartPreview, insert
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
    elif requestType == 'chartPreview':
        chart_config = event['chartConfig']
        resp=create_preview(chartPreviewPath,bucket,chart_config)
    print(resp)
    return{
        'body': resp
    }

event={"reqType":"write","objType":"template","data":{"S3TemplateContent":"La pianta {{name}} della specie {{species}}, varietà {{variety}}, è entrata nel suo periodo! Il suo periodo va da {{period_begin}} a {{period_end}}; la pianta è situata: {{site}}. Modificato","S3FileKey":"test_2/template/template_begin.txt"}}
lambda_handler(event,'1')
