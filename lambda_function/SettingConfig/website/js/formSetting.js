var WebAppMethods = window.WebAppMethods || {};
WebAppMethods.disabledList={
        "plant":
          {
            "plantUUID": 1,    
            "name": 0,
            "species": 0,
            "variety": 0,
            "period_begin": 1,
            "period_end": 1,
            "device": 
              {
              "dendrometerCh": 0,
              "deviceUUID": 0
              },
            "site": {
              "geometry": {
                "coordinates": {
                  "0": 0,
                  "1": 0
                },
                "type": 1
              },
              "properties": {
                "name": 0
              },
              "type": 1
            }
          },
        "graph_config.json":{
            
        },
        "ftpsParameters.json":{

        }
    }
    WebAppMethods.regexList={
      "plant":
        {
          "plantUUID": {
            "pattern":"[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}",
            "title":"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
          },    
          "name": "",
          "species": "",
          "variety": "",
          "period_begin": {
            "pattern":"[0-9]{2}-[0-9]{2}",
            "title":"DD-MM"
          },
          "period_end": {
            "pattern":"[0-9]{2}-[0-9]{2}",
            "title":"DD-MM"
          },
          "device": {
          "dendrometerCh": {
            "pattern":"[0-9]",
            "title":"Only number"
          },
          "deviceUUID": {
              "pattern":"[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}",
              "title":"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            }
          },
          "site": {
            "geometry": {
              "coordinates": {
                "0": "",
                "1": ""
              },
              "type": ""
            },
            "properties": {
              "name": ""
            },
            "type": ""
          }
        }    
      }