function str2Obj(str){
    var data = {};
    kv = str.split('&');
    for(i in kv){
        v = kv[i].split('=');
        data[v[0]] = v[1];
    }
    return data;
}

function pmaPost(method,args,callback){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(str2Obj(args));
    } else {
        _args = JSON.stringify(args);
    }

    var loadT = layer.msg('Retrieving...', { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'phpmyadmin', func:method, args:_args}, function(data) {
        layer.close(loadT);
        if (!data.status){
            layer.msg(data.msg,{icon:0,time:2000,shade: [0.3, '#000']});
            return;
        }

        if(typeof(callback) == 'function'){
            callback(data);
        }
    },'json');
}


function pmaAsyncPost(method,args){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(str2Obj(args));
    } else {
        _args = JSON.stringify(args);
    }
    return syncPost('/plugins/run', {name:'phpmyadmin', func:method, args:_args});
}

function homePage(){
    pmaPost('get_home_page', '', function(data){
        var rdata = $.parseJSON(data.data);
        if (!rdata.status){
            layer.msg(rdata.msg,{icon:0,time:2000,shade: [0.3, '#000']});
            return;
        }
        var con = '<button class="btn btn-default btn-sm" onclick="window.open(\'' + rdata.data + '\')">Home</button>';
        $(".soft-man-con").html(con);
    });
}

//phpmyadmin switch php version
function phpVer(version) {

    var _version = pmaAsyncPost('get_set_php_ver','')
    if (_version['data'] != ''){
        version = _version['data'];
    }

    $.post('/site/get_php_version', function(rdata) {
        // console.log(rdata);
        var body = "<div class='ver line'><span class='tname'>PHP version</span><select id='phpver' class='bt-input-text mr20' name='phpVersion' style='width:110px'>";
        var optionSelect = '';
        for (var i = 0; i < rdata.length; i++) {
            optionSelect = rdata[i].version == version ? 'selected' : '';
            body += "<option value='" + rdata[i].version + "' " + optionSelect + ">" + rdata[i].name + "</option>"
        }
        body += '</select><button class="btn btn-success btn-sm" onclick="phpVerChange(\'phpversion\',\'get\')">Save</button></div>';
        $(".soft-man-con").html(body);
    },'json');
}

function phpVerChange(type, msg) {
    var phpver = $("#phpver").val();
    pmaPost('set_php_ver', 'phpver='+phpver, function(data){
        if ( data.data == 'ok' ){
            layer.msg('Set successfully!',{icon:1,time:2000,shade: [0.3, '#000']});
        } else {
            layer.msg('Setup failed!',{icon:2,time:2000,shade: [0.3, '#000']});
        }
    });
}


//phpmyadmin security settings
function safeConf() {
    var data = pmaAsyncPost('get_pma_port');
    var rdata = $.parseJSON(data.data);
    if (!rdata.status){
        layer.msg(rdata.msg,{icon:2,time:2000,shade: [0.3, '#000']});
        return;
    }
    var con = '<div class="ver line">\
                    <span style="margin-right:10px">Access port</span>\
                    <input class="bt-input-text phpmyadmindk mr20" name="Name" id="pmport" value="' + rdata['data'] + '" placeholder="Phpmyadmin access port" maxlength="5" type="number">\
                    <button class="btn btn-success btn-sm" onclick="phpmyadminPort()">Save</button>\
                </div>';
    $(".soft-man-con").html(con);
}



//Modify phpmyadmin port
function phpmyadminPort() {
    var pmport = $("#pmport").val();
    if (pmport < 80 || pmport > 65535) {
        layer.msg('Invalid port range!', { icon: 2 });
        return;
    }
    var data = 'port=' + pmport;

    pmaPost('set_pma_port',data, function(data){
        var rdata = $.parseJSON(data.data);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
}
