function str2Obj(str){
    var data = {};
    kv = str.split('&');
    for(i in kv){
        v = kv[i].split('=');
        data[v[0]] = v[1];
    }
    return data;
}

function rsPost(method,args,callback, title){

    var _args = null;
    if (typeof(args) == 'string'){
        _args = JSON.stringify(str2Obj(args));
    } else {
        _args = JSON.stringify(args);
    }

    var _title = 'Retrieving...';
    if (typeof(title) != 'undefined'){
        _title = title;
    }

    var loadT = layer.msg(_title, { icon: 16, time: 0, shade: 0.3 });
    $.post('/plugins/run', {name:'rsyncd', func:method, args:_args}, function(data) {
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


function rsyncdReceive(){
	rsPost('rec_list', '', function(data){
		var rdata = $.parseJSON(data.data);
		if (!rdata.status){
			layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
			return;
		}
		// console.log(rdata);
		var list = rdata.data;
		var con = '';
        con += '<div class="divtable" style="margin-top:5px;"><table class="table table-hover" width="100%" cellspacing="0" cellpadding="0" border="0">';
        con += '<thead><tr>';
        con += '<th>Service Name</th>';
        con += '<th>Path</th>';
        con += '<th>Remark</th>';
        con += '<th>Action (<a class="btlink" onclick="addReceive()"> Add</a>)</th>';
        con += '</tr></thead>';

        con += '<tbody>';

        //<a class="btlink" onclick="modReceive(\''+list[i]['name']+'\')">编辑</a>
        for (var i = 0; i < list.length; i++) {
            con += '<tr>'+
                '<td>' + list[i]['name']+'</td>' +
                '<td>' + list[i]['path']+'</td>' +
                '<td>' + list[i]['comment']+'</td>' +
                '<td>\
                	<a class="btlink" onclick="cmdReceive(\''+list[i]['name']+'\')">Order</a>\
                	| <a class="btlink" onclick="delReceive(\''+list[i]['name']+'\')">Delete</a></td>\
                </tr>';
        }

        con += '</tbody>';
        con += '</table></div>';

        $(".soft-man-con").html(con);
	});
}

function addReceive(){
    var loadOpen = layer.open({
        type: 1,
        title: 'Create a receipt',
        area: '400px',
        content:"<div class='bt-form pd20 pb70 c6'>\
            <div class='line'>\
                <span class='tname'>Item name</span>\
                <div class='info-r c4'>\
                	<input id='name' class='bt-input-text' type='text' name='name' placeholder='Item name' style='width:200px' />\
                </div>\
            </div>\
            <div class='line'>\
                <span class='tname'>Key</span>\
                <div class='info-r c4'>\
                	<input id='MyPassword' class='bt-input-text' type='text' name='pwd' placeholder='Key' style='width:200px' />\
                	<span title='Random code' class='glyphicon glyphicon-repeat cursor' onclick='repeatPwd(16)'></span>\
                </div>\
            </div>\
            <div class='line'>\
                <span class='tname'>Sync to</span>\
                <div class='info-r c4'>\
                	<input id='inputPath' class='bt-input-text' type='text' name='path' placeholder='/' style='width:200px' />\
                	<span class='glyphicon glyphicon-folder-open cursor' onclick=\"changePath('inputPath')\"></span>\
                </div>\
            </div>\
            <div class='line'>\
                <span class='tname'>Remark</span>\
                <div class='info-r c4'>\
                	<input id='ps' class='bt-input-text' type='text' name='ps' placeholder='Remark' style='width:200px' />\
                </div>\
            </div>\
            <div class='bt-form-submit-btn'>\
                <button type='button' id='add_ok' class='btn btn-success btn-sm btn-title bi-btn'>Confirm</button>\
            </div>\
        </div>",
        success:function(layero, index){
        	repeatPwd(16);
        }
    });

    $('#add_ok').click(function(){
        _data = {};
        _data['name'] = $('#name').val();
        _data['pwd'] = $('#MyPassword').val();
        _data['path'] = $('#inputPath').val();
        _data['ps'] = $('#ps').val();
        var loadT = layer.msg('Retrieving...', { icon: 16, time: 0, shade: 0.3 });
        rsPost('add_rec', _data, function(data){
            var rdata = $.parseJSON(data.data);
            layer.close(loadOpen);
            layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
            setTimeout(function(){rsyncdReceive();},2000);
        });
    });
}


function delReceive(name){
	safeMessage('Delete ['+name+']', 'Do you really want to delete ['+name+']?', function(){
		var _data = {};
		_data['name'] = name;
		rsPost('del_rec', _data, function(data){
            var rdata = $.parseJSON(data.data);
            layer.msg(rdata.msg,{icon:rdata.status?1:2,time:2000,shade: [0.3, '#000']});
            setTimeout(function(){rsyncdReceive();},2000);
        });
	});
}

function cmdReceive(name){
	var _data = {};
	_data['name'] = name;
	rsPost('cmd_rec', _data, function(data){
        var rdata = $.parseJSON(data.data);
	    layer.open({
	        type: 1,
	        title: 'Command example',
	        area: '400px',
	        content:"<div class='bt-form pd20 pb70 c6'>"+rdata.data+"</div>"
    	});
    });
}


function rsRead(){
	var readme = '<ul class="help-info-text c7">';
    readme += '<li>To synchronize other server data to the local server, please "create a receive task" in the receive configuration</li>';
    readme += '<li>If you open the firewall, you need to release port 873</li>';
    readme += '</ul>';

    $('.soft-man-con').html(readme);
}
