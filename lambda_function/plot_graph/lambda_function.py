import boto3,datetime,json,os,collections,random
import matplotlib.pyplot as plt
from dynamodb_json import json_util #converts dynamodb json in standard json

import sentry_sdk,sentryDSN
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

#capture all unhandled exceptions
sentry_sdk.init(
    sentryDSN.DSN,
    integrations=[AwsLambdaIntegration()]
)

def dataAvg(device_data,hourStep=None):
    if hourStep is not None:
        intervals=[hourStep for i in range(0,24,hourStep)]
    else:
        intervals=collections.Counter(device_data['timestamp']).values()
    newData={}
    newData['timestamp'] = list(dict.fromkeys(device_data['timestamp']))    #get only unique keys by casting to list
    del device_data['timestamp']

    for key,value in device_data.items():
        currentPosition=0
        for interval in intervals:
            l=value[currentPosition:currentPosition+interval]            
            currentPosition+=interval
            avg=round(sum(l)/len(l), 2)
            try:
                newData[key].append(avg)
            except:
                newData[key]=[avg]
    return newData
            
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
    #for each dendrometer of the device get the correspondent plant and store info into the dict plant_info.
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
    device_data['battery']=list()
    #this for-loop is necessary to create dendrometers lists, because number of dendrometers is variable
    for field in json_resp['Items'][0]:
        if "dendrometerCh" in field:
            device_data[field]=list()
    for item in json_resp['Items']:
        #scan device_data on keys; keys are names of fields in DB table
        for data_list in device_data:
            if data_list=='timestamp':
                #convert timestamp list into a list of date "DD/MM" formatted
                date=datetime.datetime.fromtimestamp(item[data_list])
                date=datetime.datetime.strftime(date,"%d/%m")
                device_data[data_list].append(date)
            else:
                try:
                    device_data[data_list].append(float(item[data_list]))
                except:
                    pass
    device_data={k: v for k, v in device_data.items() if v} #get only list with item
    return device_data

def upload_chart(bucket_name,s3_client,chart_name,chart_path_S3,chart_path_local):    
    with open(chart_path_local+chart_name, 'rb') as data:
        s3_client.upload_fileobj(data, 
                                bucket_name,
                                chart_path_S3+chart_name,
                                ExtraArgs={
                                    "ACL": "public-read",
                                    })

def plot_two_dendrometer(dendrometersData,time,fig_path,bucket_name,s3_client,chart_path_S3,plants_info,device_UUID,chart_config,activation_type):
    #add / in the end of the path if there isn't
    if fig_path[-1]!='/':
        fig_path+='/'

    for dendType in dendrometersData:
        #define chart title
        chart_title='{0} chart of plants: {1} and {2}, data:{3}'.format(activation_type,plants_info[1]['name'],plants_info[2]['name'],dendType)
        if activation_type=='day':
            date=datetime.datetime.now()-datetime.timedelta(days=1)
            chart_title+=' of the day: '+ date.strftime('%d/%m/%y')
        
        #add a random number in the chart name. This is to force card update
        random.seed(int(datetime.datetime.now().timestamp()))
        rand=random.randint(10, 100)
        #define the chart name with sintax: deviceUUID_TS_dendrometerCh1_plantUUID1_dendrometerCh2_plantUUID2  note: TS=Two Scales; it is for double dendrometers charts
        chart_name='_'.join([device_UUID,'TS','&'.join(['dendrometerCh1',dendType]),plants_info[1]['plantUUID'],'&'.join(['dendrometerCh2',dendType]),plants_info[2]['plantUUID'],str(rand)])+'.png'    
        #create chart with matplotlib
        fig, ax1 = plt.subplots(figsize=(chart_config['figureWidth'], chart_config['figureHeight']),dpi=chart_config['figureDPI'])
        ax1.grid(which='major', axis='x', linestyle='--')
        ax1.set_title(label=chart_title,fontsize=chart_config['titleSize'],pad=chart_config['labelPadding'])
        ax1.plot(time, 
                dendrometersData[dendType]['1'],
                color=chart_config['color'],
                marker=chart_config['marker'],
                linestyle=chart_config['linestyle'],
                linewidth=chart_config['linewidth'], 
                markersize=chart_config['markersize'],
                scalex=chart_config['scalex'],
                scaley=chart_config['scaley'],
            )
        ax1.set_ylabel(chart_config['ylabel']['dendrometer']+' plant: '+plants_info[1]['name'], color=chart_config['color'],fontsize=chart_config['labelSize'],labelpad=chart_config['labelPadding'])
        ax1.set_xlabel(chart_config['xlabel'],fontsize=chart_config['labelSize'],labelpad=chart_config['labelPadding'])
        ax1.tick_params(axis='x',labelsize=chart_config['labelValueSize'],pad=chart_config['labelValuePadding'])  
        ax1.tick_params(axis='y', labelcolor=chart_config['color'],labelsize=chart_config['labelValueSize'],pad=chart_config['labelValuePadding'])        
        plt.xticks(rotation='vertical') #rotate x label
        

        ax2 = ax1.twinx()   #generate ax2 with same x axe
        ax2.plot(time, 
                dendrometersData[dendType]['2'],
                color=chart_config['color2'],
                marker=chart_config['marker'],
                linestyle=chart_config['linestyle'],
                linewidth=chart_config['linewidth'], 
                markersize=chart_config['markersize'],
            )
        ax2.set_ylabel(chart_config['ylabel']['dendrometer']+' plant: '+plants_info[2]['name'], color=chart_config['color2'], fontsize=chart_config['labelSize'],labelpad=chart_config['labelPadding'])
        ax2.tick_params(axis='y', labelcolor=chart_config['color2'], labelsize=chart_config['labelValueSize'],pad=chart_config['labelValuePadding'])     
        plt.savefig(''.join([fig_path,chart_name]))

        upload_chart(bucket_name,s3_client,chart_name,chart_path_S3,fig_path)

        print("Uploaded chart: ",chart_name)

def draw_chart(variable,time,variable_name,fig_path,bucket_name,s3_client,chart_path_S3,plants_info,device_UUID,chart_config,activation_type):   
    #add / in the end of the path if there isn't
    if fig_path[-1]!='/':
        fig_path+='/'

    #add a random number in the chart name. This is to force card update
    random.seed(int(datetime.datetime.now().timestamp()))
    rand=random.randint(10, 100)
    #create chart title; if the current variable is a dendrometer, chart's title will be the plant name; 
    # else it will be the variable name
    if 'dendrometer' in variable_name:
        try:
            chart_title='{0} chart of plant: {1}'.format(activation_type,plants_info[int(variable_name.split('_')[0].replace("dendrometerCh",''))]['name'])
            plant_UUID=plants_info[int(variable_name.replace("dendrometerCh",''))]['plantUUID']
        except ValueError:
            #compatibility for dendrometer in dendrometerChx_Xxx format e.g. dendrometerCh1_Avg
            chart_title='{0} chart of plant: {1}, data: {2}'.format(activation_type,plants_info[int(variable_name.split('_')[0].replace("dendrometerCh",''))]['name'],variable_name.split('_')[1])
            plant_UUID=plants_info[int(variable_name.split('_')[0].replace("dendrometerCh",''))]['plantUUID']
        #define the chart name with sintax: deviceUUID_variable-name_plantUUID
        chart_name='_'.join([device_UUID,variable_name.replace("_","&"),plant_UUID,str(rand)])+'.png'
    else:
        chart_title='{0} chart of: {1}'.format(activation_type,variable_name)
        #define the chart name with sintax: deviceUUID_variable-name
        chart_name='_'.join([device_UUID,variable_name,str(rand)])+'.png'
    
    if activation_type=='day':
        date=datetime.datetime.now()-datetime.timedelta(days=1)
        chart_title+=' of the day: '+ date.strftime('%d/%m/%y')
    

    #set label for variable type
    if variable_name=='temperature':
        variable_label=chart_config['ylabel']['temperature']
    elif variable_name=='umidity':
        variable_label=chart_config['ylabel']['umidity']
    elif 'dendrometer' in variable_name:
        variable_label=chart_config['ylabel']['dendrometer']
    elif variable_name=='battery':
        variable_label=chart_config['ylabel']['battery']
        
    #create chart with matplotlib
    fig, ax1 = plt.subplots(figsize=(chart_config['figureWidth'], chart_config['figureHeight']),dpi=chart_config['figureDPI'])
    ax1.grid(which='major', axis='x', linestyle='--')
    ax1.set_title(label=chart_title,fontsize=chart_config['titleSize'],pad=chart_config['labelPadding'])
    ax1.plot(time, 
            variable,
            color=chart_config['color'],
            marker=chart_config['marker'],
            linestyle=chart_config['linestyle'],
            linewidth=chart_config['linewidth'], 
            markersize=chart_config['markersize'],
            scalex=chart_config['scalex'],
            scaley=chart_config['scaley'],
        )
    ax1.set_ylabel(variable_label, color=chart_config['color'],fontsize=chart_config['labelSize'],labelpad=chart_config['labelPadding'])
    ax1.set_xlabel(chart_config['xlabel'],fontsize=chart_config['labelSize'],labelpad=chart_config['labelPadding'])
    ax1.tick_params(axis='x',labelsize=chart_config['labelValueSize'],pad=chart_config['labelValuePadding'])  
    ax1.tick_params(axis='y', labelcolor=chart_config['color'],labelsize=chart_config['labelValueSize'],pad=chart_config['labelValuePadding'])        
    plt.xticks(rotation='vertical') #rotate x label

    plt.savefig(''.join([fig_path,chart_name]))

    upload_chart(bucket_name,s3_client,chart_name,chart_path_S3,fig_path)
    
    print("Uploaded chart: ",chart_name)
    
def chart(dynamodb,device,chart_path,begin_date,end_date,bucket_name,s3_client,chart_path_S3,chart_config,activation_type):
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

    if resp['Count'] == 0:
        print("No data to plot")
        return -1
    
    #organize device data in a dict
    device_data=organize_device_info(resp)
    date_list=list()
    
    if activation_type =='day':
        date_list=[datetime.time(hour=i).strftime("%H:%M") for i in range(0,24,int(chart_config['hourStep']))]
        device_data=dataAvg(device_data,int(chart_config['hourStep']))
    else:
        device_data=dataAvg(device_data)
        date_list=device_data['timestamp']
    
    #get info of the plants connected to device
    plants_info=get_plant_info(dynamodb,device)

    #check if double scale chart option is enabled
    if bool(chart_config['plotTwoDendrometer']):
        dendrometersData=dict()
        for key,data in list(device_data.items()):
            if key != "timestamp" and 'dendrometer' in key:
                dendName, dendType=key.replace('dendrometerCh','').split('_')
                if not dendType in dendrometersData:
                    dendrometersData[dendType]=dict()
                dendrometersData[dendType][dendName.strip('0')]=data
                del device_data[key]

        plot_two_dendrometer(dendrometersData,date_list,chart_path,bucket_name,s3_client,chart_path_S3,plants_info,device,chart_config,activation_type)
    
    for key,data in device_data.items():
        if key != "timestamp":
            draw_chart(data,date_list,key,chart_path,bucket_name,s3_client,chart_path_S3,plants_info,device,chart_config,activation_type)        

def lambda_handler(event,context):
    ## Config parameters
    bucket_name='ortobotanico'
    s3_client=boto3.client('s3')
    dynamodb = boto3.client('dynamodb')

    chart_path='/tmp/'
    #chart_path=os.path.dirname(os.path.realpath(__file__)) #testing
    root='test_2/'    #define s3 root folder
    chart_root=root+'chart/'
    #download chart config file
    chart_config_path=root+'config/chart_config.json'

    with open(chart_path+'chart_config.json', 'wb') as data:
        s3_client.download_fileobj(bucket_name, chart_config_path, data)
    with open(chart_path+'chart_config.json', 'r') as f:
        chart_config = json.load(f)

    #get time of the rule event
    cron_date=datetime.datetime.strptime(event['time'],"%Y-%m-%dT%H:%M:%SZ")    
    
    #calculate begin and end dates
    activation_type= event['resources'][0].split('/')[-1].split('_')[0]
    if activation_type=="week":
        chart_path_S3=chart_root+'week/'
        end_date=cron_date-datetime.timedelta(days=1)
        begin_date=cron_date-datetime.timedelta(days=7)
    elif activation_type=="twoWeeks":
        chart_path_S3=chart_root+'twoWeeks/'
        end_date=cron_date-datetime.timedelta(days=1)
        begin_date=cron_date-datetime.timedelta(days=14)
    #every first day of months, create chart of previouse month
    elif activation_type=="month":
        chart_path_S3=chart_root+'month/'
        end_date=cron_date-datetime.timedelta(days=1)  #last day of the month before schedule rule
        begin_date=end_date.replace(day=1)  #first day of the month
    #create daily chart
    elif activation_type=="day":
        chart_path_S3=chart_root+'day/'
        begin_date=cron_date-datetime.timedelta(days=1)
        end_date=begin_date
    else:
        raise Exception('Activation error. Wrong trigger event.')
    
    begin_date=begin_date.replace(hour=00, minute=00)   #set time to the begin of the day (00:00)
    end_date=end_date.replace(hour=23, minute=59)   #set time to the end of the day (23:59)
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
        chart(dynamodb,device,chart_path,begin_date_ts,end_date_ts,bucket_name,s3_client,chart_path_S3,chart_config,activation_type)
