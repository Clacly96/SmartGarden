import boto3
def create_rule(event_client,ev_data,rule_type):
    #extract day and month from the event object
    day,month=ev_data['NewImage']['period_{0}'.format(rule_type)]['S'].split('-')

    #create rule with name: plantuuid_rule_type
    event_response = event_client.put_rule(
        Name=str(ev_data['Keys']['UUID']['S'])+'_{0}'.format(rule_type),
        ScheduleExpression='cron(0 0 {0} {1} ? *)'.format(day,month)
    )
    print(event_response) #testing
    #return the ARN of the created rule
    return event_response['RuleArn']

def add_lambda_permission(lambda_arn,lambda_client,rule_arn):
    #add permission to invoke lambda by the rule
    lambda_client.add_permission(
        FunctionName=lambda_arn,
        StatementId=rule_arn.split('/')[-1]+'_lambda',
        Action='lambda:InvokeFunction',
        Principal='events.amazonaws.com',
        SourceArn=rule_arn
    )

def set_event_rule(ev_type,lambda_arn,lambda_client,event_client,ev_data):
    #get arn of begin and end rules
    arn_rule_begin=create_rule(event_client,ev_data,'begin')
    arn_rule_end=create_rule(event_client,ev_data,'end')

    #add permissions and associate rule to lambda only if new item is inserted
    if ev_type=='INSERT':
        add_lambda_permission(lambda_arn,lambda_client,arn_rule_begin)
        add_lambda_permission(lambda_arn,lambda_client,arn_rule_end)
        event_client.put_targets(
            Rule=arn_rule_begin.split('/')[-1],
            Targets=[{'Arn': lambda_arn,'Id': '1'}]
        )
        event_client.put_targets(
            Rule=arn_rule_end.split('/')[-1],
            Targets=[{'Arn': lambda_arn,'Id': '1'}]
        )

def del_event_rule(lambda_arn,lambda_client,event_client,ev_data):
    #remove begin rule target
    event_client.remove_targets(
        Rule=str(ev_data['Keys']['UUID']['S'])+'_begin',
        Ids=['1']
    )
    #remove end rule target
    event_client.remove_targets(
        Rule=str(ev_data['Keys']['UUID']['S'])+'_end',
        Ids=['1']
    )
    #delete begin rule
    event_client.delete_rule(
        Name=str(ev_data['Keys']['UUID']['S'])+'_begin'
    )
    #delete end rule
    event_client.delete_rule(
        Name=str(ev_data['Keys']['UUID']['S'])+'_end'
    )
    #remove begin rule permission
    lambda_client.remove_permission(
        FunctionName=lambda_arn,
        StatementId=str(ev_data['Keys']['UUID']['S'])+'_begin_lambda'
    )
    #remove end rule permission
    lambda_client.remove_permission(
        FunctionName=lambda_arn,
        StatementId=str(ev_data['Keys']['UUID']['S'])+'_end_lambda'
    )

def lambda_handler(event, context):
    #set arn of the destination lambda function
    destination_lambda_arn='arn:aws:lambda:us-east-1:536732575732:function:publish_event_tweet'
    event_client=boto3.client('events',
        aws_access_key_id='AKIAJFHE3KBGLGRI76IQ',
        aws_secret_access_key='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')
    lambda_client = boto3.client('lambda',    
        aws_access_key_id='AKIAJFHE3KBGLGRI76IQ',
        aws_secret_access_key='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')

    #iterate event object to scan all update from db
    for ev in event['Records']:
        ev_type=ev['eventName']
        ev_data=ev['dynamodb']
        if ev_type=='MODIFY' or ev_type=='INSERT':
            set_event_rule(ev_type,destination_lambda_arn,lambda_client,event_client,ev_data)
        elif ev_type=='REMOVE':
            del_event_rule(destination_lambda_arn,lambda_client,event_client,ev_data)