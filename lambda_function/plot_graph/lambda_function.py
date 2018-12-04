import boto3,datetime,json
import matplotlib.pyplot as plt
from dynamodb_json import json_util #converts dynamodb json in standard json

def get_plant_info(dynamodb,deviceUUID):
    #get dendrometers and plants of the device
    plant_device=dynamodb.query(
        TableName='plant_device',
        KeyConditionExpression='deviceUUID = :dev_id',
        ExpressionAttributeValues= {
            ":dev_id": {'S':deviceUUID}
            }
    )
    plant_device=json_util.loads(plant_device)
    plant_info=dict()
    #for each dendrometer of the device get the correspondet plant and store info into the dict plant_info.
    #plant_info is indexed by dendrometerCH number e.g.: 1,2,3...
    for item in plant_device['Items']:
        plant_resp=dynamodb.get_item(
            TableName='plant',
            Key={'plantUUID':{'S':item['plantUUID']} }
        )['Item']
        plant_info[item['dendrometerCh']]=json_util.loads(plant_resp)

    return plant_info

def organize_device_info(resp):
    json_resp=json_util.loads(resp)
    device_data=dict()
    device_data['timestamp']=list()
    device_data['temperature']=list()
    device_data['umidity']=list()
    #a for is necessary to create dendrometers lists, because number of dendrometers is variable
    for field in json_resp['Items'][0]:
        if "dendrometerCh" in field:
            device_data[field]=list()
    for item in json_resp['Items']:
        #scan device_data on keys; keys are names of fields in DB table
        for data_list in device_data:
            if data_list=='timestamp':
                device_data[data_list].append(item[data_list])
            else:
                device_data[data_list].append(float(item[data_list]))
    return device_data

def upload_graph(bucket_name,s3_client,graph_name,graph_path_S3,graph_path_local):    
    with open(graph_path_local+graph_name, 'rb') as data:
        s3_client.upload_fileobj(data, 
                                bucket_name,
                                graph_path_S3+graph_name,
                                ExtraArgs={
                                    "ACL": "public-read",
                                    })

def draw_graph(variable,time,variable_name,fig_path,bucket_name,s3_client,graph_path_S3,plants_info,device_UUID,graph_config):   
    #add / in the end of the path if there isn't
    if fig_path[-1]!='/':
        fig_path+='/'
    
    #create graph title; if the current variable is a dendrometer, graph's title will be the plant name; 
    # else it will be the variable name
    if 'dendrometer' in variable_name:
        graph_title=plants_info[int(variable_name.replace("dendrometerCh",''))]['name']
        plant_UUID=plants_info[int(variable_name.replace("dendrometerCh",''))]['plantUUID']
        #define the graph name with sintax: deviceUUID_variable-name_plantUUID
        graph_name='_'.join([device_UUID,variable_name,plant_UUID])+'.png'
    else:
        graph_title=variable_name
        #define the graph name with sintax: deviceUUID_variable-name
        graph_name='_'.join([device_UUID,variable_name])+'.png'
    
    

    #set label for variable type
    if variable_name=='temperature':
        variable_label=graph_config['ylabel']['temperature']
    elif variable_name=='umidity':
        variable_label=graph_config['ylabel']['umidity']
    elif 'dendrometer' in variable_name:
        variable_label=graph_config['ylabel']['dendrometer']
    #create graph with matplotlib
    fig, axs = plt.subplots()
    plt.plot(time, 
            variable,
            color=graph_config['color'],
            marker=graph_config['marker'],
            linestyle=graph_config['linestyle'],
            linewidth=graph_config['linewidth'], 
            markersize=graph_config['markersize'],
            scalex=graph_config['scalex'],
            scaley=variable_label,
        )
    axs.set(
            xlabel=graph_config['xlabel'], 
            ylabel=graph_config['scalex'],
            title=graph_title.title()
        )
    axs.grid()
    plt.savefig(''.join([fig_path,graph_name]))

    upload_graph(bucket_name,s3_client,graph_name,graph_path_S3,fig_path)
    
def graph(dynamodb,device,graph_path,begin_date,end_date,bucket_name,s3_client,graph_path_S3,graph_config):
    #get device info from db
    resp=dynamodb.query(
        TableName='devicedata',
        KeyConditionExpression= "deviceUUID = :id AND #date_ts BETWEEN :begin AND :end",
        ScanIndexForward=True,
        ExpressionAttributeNames={
            "#date_ts": "timestamp"
        },
        ExpressionAttributeValues= {
            ":id": {'S':device},
            ":begin": {'N':str(begin_date)},
            ":end": {'N':str(end_date)}
        }
    )

    if resp['Count'] != 0:
        #organize device data in a dict
        device_data=organize_device_info(resp)
        #get info of the plants connected to device
        plants_info=get_plant_info(dynamodb,device)
        #convert timestamp list into a list of date "DD/MM" formatted
        date_list=list()
        for value in device_data['timestamp']:
            date=datetime.datetime.fromtimestamp(value)
            date=datetime.datetime.strftime(date,"%d/%m/%Y")
            date_list.append(date)

        for key,data in device_data.items():
            if key != "timestamp":
                draw_graph(data,date_list,key,graph_path,bucket_name,s3_client,graph_path_S3,plants_info,device,graph_config)
    else:
        print("No data to plot")

def lambda_handler(event,context):
    ## Config parameters
    bucket_name='ortobotanico'
    s3_client=boto3.client('s3')
    dynamodb = boto3.client('dynamodb')
    graph_path='/tmp/'
    root='test_2/chart/'
    #download graph config file
    graph_config_path='test_2/config/graph_config.json'
    #'/tmp/graph_config.json'
    with open(graph_path+'graph_config.json', 'wb') as data:
        s3_client.download_fileobj(bucket_name, graph_config_path, data)
    with open(graph_path+'graph_config.json', 'r') as f:
        graph_config = json.load(f)

    #get time of the rule event
    cron_date=datetime.datetime.strptime(event['time'],"%Y-%m-%dT%H:%M:%SZ")    
    #calculate begin and end dates
    activation_type= event['resources'][0].split('/')[-1].split('_')[0]
    if activation_type=="week":
        graph_path_S3=root+'week/'
        end_date=cron_date-datetime.timedelta(days=1)
        begin_date=cron_date-datetime.timedelta(days=7)
    elif activation_type=="month":
        graph_path_S3=root+'month/'
        end_date=cron_date-datetime.timedelta(days=1)  #last day of the month before schedule rule
        begin_date=end_date.replace(day=1)  #first day of the month
    #convert dates into timestamps for search in DB
    end_date_ts=int(end_date.timestamp())
    begin_date_ts=int(begin_date.timestamp())

    #get all device UUID from devicedata table
    resp=dynamodb.scan(
        TableName='devicedata',
        ProjectionExpression="deviceUUID")

    devices_UUID=set()
    #store uuid in a set, to have only unique uuids
    for item in resp["Items"]:
        devices_UUID.add(item['deviceUUID']['S'])

    for device in devices_UUID:
        graph(dynamodb,device,graph_path,begin_date_ts,end_date_ts,bucket_name,s3_client,graph_path_S3,graph_config)