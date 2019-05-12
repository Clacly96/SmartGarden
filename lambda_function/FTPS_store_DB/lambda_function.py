import boto3,ftplib,json,datetime
def downloadCsv(cronDate,localFile,ftpsParams):    
    
    #Fix for reuse SSL session
    class MyFTP_TLS(ftplib.FTP_TLS):
        """Explicit FTPS, with shared TLS session"""
        def ntransfercmd(self, cmd, rest=None):
            conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
            if self._prot_p:
                conn = self.context.wrap_socket(conn,
                                                server_hostname=self.host,
                                                session=self.sock.session)  # this is the fix
            return conn, size

    #Fix for bad ip from server after set passive
    _old_makepasv = MyFTP_TLS.makepasv
    def _new_makepasv(self):
        host,port = _old_makepasv(self)
        host = self.sock.getpeername()[0]
        return host,port
    MyFTP_TLS.makepasv = _new_makepasv

    ftps = MyFTP_TLS()    #define new connection object
    ftps.connect(host=ftpsParams['host'],port=ftpsParams['port'],timeout=ftpsParams['timeout'])
    ftps.login(ftpsParams['username'],ftpsParams['password'])           # login anonymously before securing control channel
    ftps.prot_p() #secure connection

    fileList=ftps.nlst()
    for val in fileList:
        if cronDate in val:
            serverFile=val
    
    with open(localFile, 'wb') as data:
            ftps.retrbinary('RETR '+serverFile, data.write)
    
    ftps.quit()

    
def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('devicedata')
    
    #set root folder
    root='test_2/'
    bucket = 'ortobotanico'

    ftpsParametersFile=root+'config/ftpsParameters.json'
    localCsvFile='/tmp/localFile.csv'
    localFtpsParams='/tmp/config.json'

    #get ftps parameters file
    with open(localFtpsParams, 'wb') as data:
        s3_client.download_fileobj(bucket, ftpsParametersFile, data)
    with open(localFtpsParams, 'r') as f:
        ftpsParams = json.load(f)


    cron_date=datetime.datetime.strptime(event['time'],"%Y-%m-%dT%H:%M:%SZ")-datetime.timedelta(days=1)
    dateStr=cron_date.strftime('%Y%m%d')

    downloadCsv(dateStr,localCsvFile,ftpsParams)

    with open(localCsvFile, 'r') as data:
        for row in data.read().splitlines():
            values=row.split(',')
            timestamp=datetime.datetime.timestamp(datetime.datetime.strptime(values[0], '"%Y-%m-%d %H:%M:%S"'))
            item={
                "deviceUUID" : str(ftpsParams['deviceUUID']),
                "timestamp" : int(timestamp),
                "dendrometerCh01_Avg" : str(values[1]),
                "dendrometerCh02_Avg" : str(values[2]),
                "dendrometerCh01_Max" : str(values[3]),
                "dendrometerCh02_Max" : str(values[4]),
                "dendrometerCh01_Min" : str(values[5]),
                "dendrometerCh02_Min" : str(values[6]),
                "battery": str(values[7]),
                "temperature":str(values[8]),
                
            }
            resp=table.put_item(Item=item)
