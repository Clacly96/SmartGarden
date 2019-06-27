var WebAppMethods = window.WebAppMethods || {};
(function menuScopeWrapper($) {
    //Get user auth token from authToken promise (in cognito-auth.js)
    var currentRequestObjType;
    var currentRequestObjName;
    var currentRequestType;
    var userToken;
    WebAppMethods.authToken.then(
        function(token) {
            if (token) {
                userToken = token;
            } else {
                window.location.href = 'signin.html';
            }
        },
        function(error) {
            console.log("Error while getting token: " + error.message);
            window.location.href = 'signin.html'
        }
    );

    $(function onDocReady() {
        $("#list-menu li").click(requestList);
        $("#insert-menu li").click(requestInsert);
    });

    function requestList(event) {
        $("#form-container").html(''); //make form-container empty
        $("#loadingSpinner").show();
        currentRequestObjType=$(this).prop('title');
        currentRequestType='read';
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl,
            headers: {
                Authorization: userToken
            },
            data: JSON.stringify(
                {
                    reqType: 'read',
                    objType: currentRequestObjType,
                    objName: 'list'
                }
            ),
            contentType: 'application/json',
            success: writeList,
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting ride: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting:\n' + jqXHR.responseText);
            }
        });
    }

    function writeList(result){ 
        $("#loadingSpinner").hide();
        $("#table-type").html('List of: '+result['body']['type']);
        $("#table-type").prop('title',result['body']['type']);
        var container = $('#list-pagination');
        //pagination begin
        var sources = function () { //pagination's data
            var data = [];
            for (var element in result['body']['items']) {
                data.push(result['body']['items'][element]);
            }
            return data;
        }();
        var options = { //pagination's options
            dataSource: sources,
            callback: function (response, pagination) {
                window.console && console.log(response, pagination);
                var dataHtml = '<table class="table">';
                var firstParam=null;
                dataHtml+='<tr>'+function(){
                    var th='';
                    for(var elem in response[0]){
                        th+='<th>' + elem + '</th>';
                        if(!firstParam){
                            firstParam=elem;
                        }
                    }
                    return th;
                }() + '</tr>';
                $.each(response, function (index, item) {
                    dataHtml += '<tr>' + function(){
                        var td='';
                        for (var elem in item) {
                            if(elem==firstParam){                        
                                td+='<td class="selectedItem"><a class="nav-link" href="#">' + item[elem] + '</a></td>';
                            }else{
                                td+='<td>' + item[elem] + '</td>';
                            }                        
                        }
                        return td;
                    }() + '</tr>';
                });
                dataHtml += '</table>';
                container.prev().html(dataHtml);
                $("td.selectedItem").click(readData);
            }
        };
        container.pagination(options);
    }

    function readData(event) {
        $("#loadingSpinner").show();
        currentRequestObjName=$(this).children("a").html();
        currentRequestType='read';
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl,
            headers: {
                Authorization: userToken
            },
            data: JSON.stringify(
                {
                    reqType: 'read',
                    objType: currentRequestObjType,
                    objName: currentRequestObjName
                }
            ),
            contentType: 'application/json',
            success: writeInfo,
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting ride: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting:\n' + jqXHR.responseText);
            }
        });
    }

    function writeInfo(result){
        $("#loadingSpinner").hide();
        if(result['errorMessage']){
            alert(result['errorMessage']);
        }       
        else{
            var data=createForm(result['body']['data']);
            var form='<form id="Form">'+data;
            form+='<input class="btn btn-primary mb-2" style="margin:1em 0 0 0;" type="submit" value="Submit">';
            form+='</form>';
            $("#form-container").html(form);
            $("#Form").submit(function(event){
                if(confirm('Are you sure?')){
                    sendData(event);
                }
                else{
                    return false;
                }
            });
            if (currentRequestObjName.includes('chart_config.json')){
                $("#Form").append('<input id="previewButton" class="btn btn-primary mb-2" style="margin:1em 0 0 0;" type="button" value="Preview">');
                $("#previewButton").click(requestChartPreview);
            }

            //add leaflet map
            if($('#map')){
                map = new L.Map('map');
                var osmUrl='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                var osmAttrib='Map data © <a href="https://openstreetmap.org">OpenStreetMap</a> contributors';
                var osm = new L.TileLayer(osmUrl, {minZoom: 1, maxZoom: 22, attribution: osmAttrib});		

                // start the map in initial plant site
                var long=$('input[name="site.geometry.coordinates.0"]').val();
                var lat=$('input[name="site.geometry.coordinates.1"]').val();
                if (long==0 && lat==0){
                    lat=43.5821;
                    long=13.4367;
                }
                var latlong=new L.LatLng(lat, long)
                map.setView(latlong,14);
                var marker=L.marker(latlong).addTo(map);
                map.addLayer(osm);

                map.on('click', function(e) {
                    if(marker)
                        map.removeLayer(marker);
                    console.log(e.latlng); // e is an event object (MouseEvent in this case)
                    marker = L.marker(e.latlng).addTo(map);
                    $('input[name="site.geometry.coordinates.0"]').val(e.latlng.lng); //insert long in form
                    $('input[name="site.geometry.coordinates.1"]').val(e.latlng.lat); //insert lat in form
                });
            }
            //add jquery datepicker
            if($('[name="period_begin"]') || $('[name="period_end"]')){
                $( function() {
                    $( '[name="period_begin"],[name="period_end"]' ).each(function(){
                        $(this).datepicker({
                            changeMonth: true,
                            changeYear: false,
                            dateFormat: 'dd-mm'
                        }
                        );
                    })                    
                });
            }
        }
    }

    
    //function for get property from json with dot notation
    function getPropFromJson(path,obj){
        return path.split('.').reduce(function(prev,curr){
            try{
                return prev[curr]
            }
            catch(e){
                return null
            }
        },obj)
    }

    function createForm(values,father=null){    //father variable is used to store the input father's name. This is for serializeToJSON library
        var form='';
        for(var a in values){            
            if (typeof values[a] == 'object'){                
                form+='<fieldset class="form-group border p-3"><legend class="w-auto">'+a+'</legend>';
                if (father){
                    form+=createForm(values[a],father+'.'+a);
                 }else{
                     form+=createForm(values[a],a);
                 }
                
                form+='</fieldset>';
            }
            else if(a=='S3FileKey'){
                form+='<input type="hidden" name="'+a+'" value="'+values[a]+'">';
            }
            else if(a=='S3TemplateContent'){
                form+='<div class="form-group"><textarea class="form-control" rows = "10" cols = "60" name="'+a+'">'+values[a]+'</textarea></div>';
            }
            else{

                var name=(father) ? [father,a].join('.') : a
                var path=(currentRequestObjType=='plant') ? [currentRequestObjType,name].join('.') : [currentRequestObjName,name].join('.');
                
                var pattern=getPropFromJson([path,'pattern'].join('.'),WebAppMethods.regexList);
                pattern=pattern || pattern != undefined ? 'pattern="'+pattern+'"' : '';
                var title=getPropFromJson([path,'title'].join('.'),WebAppMethods.regexList);
                title=title || title != undefined ? 'title="'+title+'"' : '';
                
                //get readonly field only if request is not a insert request
                if(currentRequestType != 'insert'){ 
                    var readonly=getPropFromJson(path,WebAppMethods.disabledList);
                    readonly=readonly ? 'readonly' : '';
                }

                form+='<div class="form-group"><label for="'+name+'">'+a+'</label>';
                form+='<input class="form-control" type="text" name="'+name+'" value="'+values[a]+'" required '+pattern+' '+title+' '+readonly+'>';
                form+='</div>';
            }//end if
            if(a=='coordinates'){
                form+='<div id="map" style="height:300px"></div>';
            }
        }//end for
        return form;
    }

    function sendData(event) {
        event.preventDefault();
        currentRequestType='write';
        $("#loadingSpinner").show();
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl,
            headers: {
                Authorization: userToken
            },
            data: JSON.stringify(
                {
                    reqType: 'write',
                    objType: currentRequestObjType,
                    data: $("#Form").serializeToJSON({associativeArrays: false,
                                            parseFloat: {
                                                        condition: function(i) {
                                                            var v = i.val().split(",").join("");
                                                            return Number.isInteger(Number(v)); // In this case, conversion will always occur when possible
                                                        }
                                                    }})
                }
            ),
            contentType: 'application/json',
            success: function(result){
                $("#loadingSpinner").hide();
                if(result['body']==0){
                    alert('Success');
                }else {
                    alert('Error');
                }
            },
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting ride: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting:\n' + jqXHR.responseText);
            }
        });
        $("#form-container").html(''); //make form-container empty
    }

    function requestInsert(event) {
        $('#list-pagination,#list-content,#table-type').each(function(){
            $(this).html('');
        })
        event.preventDefault();
        currentRequestType='insert';
        $("#loadingSpinner").show();
        currentRequestObjType=$(this).prop('title').split('-')[1];
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl,
            headers: {
                Authorization: userToken
            },
            data: JSON.stringify(
                {
                    reqType: 'insert',
                    objType: $(this).prop('title').split('-')[1],
                }
            ),
            contentType: 'application/json',
            success: writeInfo,
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting ride: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting:\n' + jqXHR.responseText);
            }
        });
    }

    function requestChartPreview(event) {
        event.preventDefault();
        currentRequestType='chartPreview';
        $("#loadingSpinner").show();
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl,
            headers: {
                Authorization: userToken
            },
            data: JSON.stringify(
                {
                    reqType: 'chartPreview',
                    objType:'chart',
                    chartConfig: $("#Form").serializeToJSON({associativeArrays: false,
                        parseFloat: {
                                    condition: function(i) {
                                        var v = i.val().split(",").join("");
                                        return Number.isInteger(Number(v)); // In this case, conversion will always occur when possible
                                    }
                                }})
                }
            ),
            contentType: 'application/json',
            success: function(result){
                $("#loadingSpinner").hide();
                if (!$("#chart_preview_div").length){
                    $("#form-container").append('<div id="chart_preview_div"></div>')
                }
                $("#chart_preview_div").html('<img id="chart_preview" style="max-width: 100%;" src="'+result['body']+'" alt="Chart preview">')
            },
            error: function ajaxError(jqXHR, textStatus, errorThrown) {
                console.error('Error requesting ride: ', textStatus, ', Details: ', errorThrown);
                console.error('Response: ', jqXHR.responseText);
                alert('An error occured when requesting:\n' + jqXHR.responseText);
            }
        });
    }
    
}(jQuery));