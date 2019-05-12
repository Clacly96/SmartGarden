var WebAppMethods = window.WebAppMethods || {};
(function menuScopeWrapper($) {
    //Get user auth token from authToken promise (in cognito-auth.js)
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
        $("#menu li").click(requestList);
        $("td.selectedItem").click(readData);
    });

    function requestList(event) {
        $("#form-container").html(''); //make form-container empty
        $("#loadingSpinner").show();
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl,
            headers: {
                Authorization: userToken
            },
            data: JSON.stringify(
                {
                    reqType: 'read',
                    objType: $(this).prop('title'),
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
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl,
            headers: {
                Authorization: userToken
            },
            data: JSON.stringify(
                {
                    reqType: 'read',
                    objType: $("#table-type").prop('title'),
                    objName: $(this).children("a").html()
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
        var data=createForm(result['body']['data']);
        var form='<form id="Form">'+data;
        form+='<input class="btn btn-primary mb-2" style="margin:1em 0 0 0;" type="submit" value="Submit">';
        form+='</form>';
        if(result['errorMessage']){
            alert(result['errorMessage']);
        }
        else{
            $("#form-container").html(form);
            $("#Form").submit(sendData);
        }
    }

    function sendData(event) {
        event.preventDefault();
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
                    objType: $("#table-type").prop('title'),
                    data: $("#Form").serializeToJSON({associativeArrays: false})
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
                form+='<div class="form-group><label for="'+a+'">'+a+'</label>';
                if(father){
                    form+='<input class="form-control" type="text" name="'+father+'.'+a+'" value="'+values[a]+'">';
                }else{
                    form+='<input class="form-control" type="text" name="'+a+'" value="'+values[a]+'">';
                }
                form+='</div>'
            }//end if
        }//end for
        return form;
    }
    
}(jQuery));