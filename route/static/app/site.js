/**
 * Get back a list of website data
 * @param {Number} page   current page
 * @param {String} search search condition
 */
function getWeb(page, search, type_id) {
	search = $("#SearchValue").prop("value");
	page = page == undefined ? '1':page;
	var order = getCookie('order');
	if(order){
		order = '&order=' + order;
	} else {
		order = '';
	}

	var type = '';
	if ( typeof(type_id) == 'undefined' ){
		type = '&type_id=0';
	} else {
		type = '&type_id='+type_id;
	}

	var sUrl = '/site/list';
	var pdata = 'limit=10&p=' + page + '&search=' + search + order + type;
	var loadT = layer.load();
	//retrieve data
	$.post(sUrl, pdata, function(data) {
		layer.close(loadT);
		//Construct data list
		var body = '';
		$("#webBody").html(body);
		for (var i = 0; i < data.data.length; i++) {
			//current site status
			if (data.data[i].status == 'running' || data.data[i].status == '1') {
				var status = "<a href='javascript:;' title='Disable this site' onclick=\"webStop(" + data.data[i].id + ",'" + data.data[i].name + "')\" class='btn-defsult'><span style='color:rgb(92, 184, 92)'>running</span><span style='color:rgb(92, 184, 92)' class='glyphicon glyphicon-play'></span></a>";
			} else {
				var status = "<a href='javascript:;' title='Enable this site' onclick=\"webStart(" + data.data[i].id + ",'" + data.data[i].name + "')\" class='btn-defsult'><span style='color:red'>stopped</span><span style='color:rgb(255, 0, 0);' class='glyphicon glyphicon-pause'></span></a>";
			}

			//Is there a backup
			if (data.data[i].backup_count > 0) {
				var backup = "<a href='javascript:;' class='btlink' onclick=\"getBackup(" + data.data[i].id + ")\">Ada</a>";
			} else {
				var backup = "<a href='javascript:;' class='btlink' onclick=\"getBackup(" + data.data[i].id + ")\">Tidak ada</a>";
			}
			//Whether to set the validity period
			var web_end_time = (data.data[i].edate == "0000-00-00") ? 'permanen': data.data[i].edate;
			//body
			var shortwebname = data.data[i].name;
			var shortpath = data.data[i].path;
			if(data.data[i].name.length > 30) {
				shortwebname = data.data[i].name.substring(0, 30) + "...";
			}
			if(data.data[i].path.length > 30){
				shortpath = data.data[i].path.substring(0, 30) + "...";
			}
			var idname = data.data[i].name.replace(/\./g,'_');

			body = "<tr><td><input type='checkbox' name='id' title='"+data.data[i].name+"' onclick='checkSelect();' value='" + data.data[i].id + "'></td>\
					<td><a class='btlink webtips' href='javascript:;' onclick=\"webEdit(" + data.data[i].id + ",'" + data.data[i].name + "','" + data.data[i].edate + "','" + data.data[i].addtime + "')\" title='"+data.data[i].name+"'>" + shortwebname + "</td>\
					<td>" + status + "</td>\
					<td>" + backup + "</td>\
					<td><a class='btlink' title='Buka direktori "+data.data[i].path+"' href=\"javascript:openPath('"+data.data[i].path+"');\">" + shortpath + "</a></td>\
					<td><a class='btlink setTimes' id='site_"+data.data[i].id+"' data-ids='"+data.data[i].id+"'>" + web_end_time + "</a></td>\
					<td><a class='btlinkbed' href='javascript:;' data-id='"+data.data[i].id+"'>" + data.data[i].ps + "</a></td>\
					<td style='text-align:right; color:#bbb'>\
					<a href='javascript:;' class='btlink' onclick=\"webEdit(" + data.data[i].id + ",'" + data.data[i].name + "','" + data.data[i].edate + "','" + data.data[i].addtime + "')\">Edit</a>\
                        | <a href='javascript:;' class='btlink' onclick=\"webDelete('" + data.data[i].id + "','" + data.data[i].name + "')\" title='Delete site'>Delete</a>\
					</td></tr>"

			$("#webBody").append(body);
			//setEdate(data.data[i].id,data.data[i].edate);
         	//Set expiration date
			function getDate(a) {
				var dd = new Date();
				dd.setTime(dd.getTime() + (a == undefined || isNaN(parseInt(a)) ? 0 : parseInt(a)) * 86400000);
				var y = dd.getFullYear();
				var m = dd.getMonth() + 1;
				var d = dd.getDate();
				return y + "-" + (m < 10 ? ('0' + m) : m) + "-" + (d < 10 ? ('0' + d) : d);
			}
            $('#webBody').on('click','#site_'+ data.data[i].id,function(){
				var _this = $(this);
				var id = $(this).attr('data-ids');
				laydate.render({
					elem: '#site_'+ id //Designated element
					,lang: 'en'
					,min:getDate(1)
					,max:'2099-12-31'
					,vlue:getDate(365)
					,type:'date'
					,format :'yyyy-MM-dd'
					,trigger:'click'
					,btns:['perpetual', 'confirm']
					,theme:'#20a53a'
					,done:function(dates){
						if(_this.html() == '永久'){
						 	dates = '0000-00-00';
						}
						var loadT = layer.msg(lan.site.saving_txt, { icon: 16, time: 0, shade: [0.3, "#000"]});
						$.post('/site/set_end_date','id='+id+'&edate='+dates,function(rdata){
							layer.close(loadT);
							layer.msg(rdata.msg,{icon:rdata.status?1:5});
						},'json');
					}
				});
            	this.click();
            });
		}
		if(body.length < 10){
			body = "<tr><td colspan='9'>There is currently no site data</td></tr>";
			// $(".dataTables_paginate").hide();
			$("#webBody").html(body);
		}
		//output data list
		$(".btn-more").hover(function(){
			$(this).addClass("open");
		},function(){
			$(this).removeClass("open");
		});
		//output pagination
		$("#webPage").html(data.page);

		$(".btlinkbed").click(function(){
			var dataid = $(this).attr("data-id");
			var databak = $(this).text();
			if(databak == null){
				databak = '';
			}
			$(this).hide().after("<input class='baktext' type='text' data-id='"+dataid+"' name='bak' value='" + databak + "' placeholder='Remarks' onblur='getBakPost(\"sites\")' />");
			$(".baktext").focus();
		});

		readerTableChecked();
	},'json');
}


function getBakPost(b) {
	$(".baktext").hide().prev().show();
	var c = $(".baktext").attr("data-id");
	var a = $(".baktext").val();
	if(a == "") {
		a = 'null';
	}
	setWebPs(b, c, a);
	$("a[data-id='" + c + "']").html(a);
	$(".baktext").remove();
}

function setWebPs(b, e, a) {
	var d = layer.load({shade: true,shadeClose: false});
	var c = 'ps=' + a;
	$.post('/site/set_ps', 'id=' + e + "&" + c, function(data) {
		if(data['status']) {
			getWeb(1);
			layer.closeAll();
			layer.msg('Successfully modified!', {icon: 1});
		} else {
			layer.closeAll();
			layer.msg('Fail to edit!', {icon: 2});
		}
	},'json');
}

//add site
function webAdd(type) {
	if (type == 1) {
		var array;
		var str="";
		var domainlist='';
		var domain = array = $("#mainDomain").val().replace('http://','').replace('https://','').split("\n");
		var webport=[];
		var checkDomain = domain[0].split('.');
		if(checkDomain.length < 1){
			layer.msg(lan.site.domain_err_txt,{icon:2});
			return;
		}
		for(var i=1; i<domain.length; i++){
			domainlist += '"'+domain[i]+'",';
		}

		webport = domain[0].split(":")[1];//Primary domain name port
		if(webport == undefined){
			webport="80";
		}

		domainlist = domainlist.substring(0,domainlist.length-1);//subdomain json
		domain ='{"domain":"'+domain[0]+'","domainlist":['+domainlist+'],"count":'+domain.length+'}';//splicing json
		var loadT = layer.msg(lan.public.the_get,{icon:16,time:0,shade: [0.3, "#000"]})
		var data = $("#addweb").serialize()+"&port="+webport+"&webinfo="+domain;

		$.post('/site/add', data, function(ret) {
			if (ret.status == true) {
				getWeb(1);
				layer.closeAll();
				layer.msg('Site created successfully',{icon:1})
			} else {
				layer.msg(ret.msg, {icon: 2});
			}
			layer.close(loadT);
		},'json');
		return;
	}

	$.post('/site/get_php_version',function(rdata){

		var defaultPath = $("#defaultPath").html();
		var php_version = "<div class='line'><span class='tname'>"+lan.site.php_ver+"</span><select class='bt-input-text' name='version' id='c_k3' style='width:100px'>";
		for (var i=rdata.length-1;i>=0;i--) {
            php_version += "<option value='"+rdata[i].version+"'>"+rdata[i].name+"</option>";
        }

        var www = syncPost('/site/get_root_dir');

		php_version += "</select><span id='php_w' style='color:red;margin-left: 10px;'></span></div>";
		layer.open({
			type: 1,
			skin: 'demo-class',
			area: '640px',
			title: 'Add a website',
			closeBtn: 2,
			shift: 0,
			shadeClose: false,
			content: "<form class='bt-form pd20 pb70' id='addweb'>\
						<div class='line'>\
		                    <span class='tname'>"+lan.site.domain+"</span>\
		                    <div class='info-r c4'>\
								<textarea id='mainDomain' class='bt-input-text' name='webname' style='width:458px;height:100px;line-height:22px' /></textarea>\
							</div>\
						</div>\
	                    <div class='line'>\
	                    <span class='tname'>Description</span>\
	                    <div class='info-r c4'>\
	                    	<input id='Wbeizhu' class='bt-input-text' type='text' name='ps' placeholder='Website Notes' style='width:458px' />\
	                    </div>\
	                    </div>\
	                    <div class='line'>\
	                    <span class='tname'>Root directory</span>\
	                    <div class='info-r c4'>\
	                    	<input id='inputPath' class='bt-input-text mr5' type='text' name='path' value='"+www['dir']+"/' placeholder='"+www['dir']+"' style='width:458px' />\
	                    	<span class='glyphicon glyphicon-folder-open cursor' onclick='changePath(\"inputPath\")'></span>\
	                    </div>\
	                    </div>\
						"+php_version+"\
	                    <div class='bt-form-submit-btn'>\
							<button type='button' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>Cancel</button>\
							<button type='button' class='btn btn-success btn-sm btn-title' onclick=\"webAdd(1)\">Add</button>\
						</div>\
	                  </form>",
		});

		$(function() {
			var placeholder = "<div class='placeholder c9' style='top:10px;left:10px'>"+lan.site.domain_help+"</div>";
			$('#mainDomain').after(placeholder);
			$(".placeholder").click(function(){
				$(this).hide();
				$('#mainDomain').focus();
			})
			$('#mainDomain').focus(function() {
			    $(".placeholder").hide();
			});

			$('#mainDomain').blur(function() {
				if($(this).val().length==0){
					$(".placeholder").show();
				}
			});

			//Verify PHP version
			$("select[name='version']").change(function(){
				if($(this).val() == '52'){
					var msgerr = 'PHP5.2 has cross-site risk when your site has loopholes, please try to use PHP5.3 or above!';
					$('#php_w').text(msgerr);
				}else{
					$('#php_w').text('');
				}
			})

			$('#mainDomain').on('input', function() {
				var array;
				var res,ress;
				var str = $(this).val().replace('http://','').replace('https://','');
				var len = str.replace(/[^\x00-\xff]/g, "**").length;
				array = str.split("\n");
				ress =array[0].split(":")[0];
				res = ress.replace(new RegExp(/([-.])/g), '_');
				if(res.length > 15){
					res = res.substr(0,15);
				}

				var placeholder = $("#inputPath").attr('placeholder');
				$("#inputPath").val(placeholder+'/'+ress);

				if(res.length > 15){
					res = res.substr(0,15);
				}

				$("#Wbeizhu").val(ress);
			})

			//Remark
			$('#Wbeizhu').on('input', function() {
				var str = $(this).val();
				var len = str.replace(/[^\x00-\xff]/g, "**").length;
				if (len > 20) {
					str = str.substring(0, 20);
					$(this).val(str);
					layer.msg('Cannot exceed 20 characters!', {
						icon: 0
					});
				}
			})
			//Get the current time timestamp, intercept the last 6 digits
			var timestamp = new Date().getTime().toString();
			var dtpw = timestamp.substring(7);
		});
	}, 'json');
}

//Modify website directory
function webPathEdit(id){
	$.post('/site/get_dir_user_ini','&id='+id, function(data){
		var userini = data['data'];
		var webpath = userini['path'];
		var userinicheckeds = userini.userini?'checked':'';
		var logscheckeds = userini.logs?'checked':'';
		var opt = ''
		var selected = '';
		for(var i=0;i<userini.runPath.dirs.length;i++){
			selected = '';
			if(userini.runPath.dirs[i] == userini.runPath.runPath){
				selected = 'selected';
			}
			opt += '<option value="'+ userini.runPath.dirs[i] +'" '+selected+'>'+ userini.runPath.dirs[i] +'</option>'
		}
		var webPathHtml = "<div class='webedit-box soft-man-con'>\
					<div class='label-input-group ptb10'>\
						<input type='checkbox' name='userini' id='userini'"+userinicheckeds+" /><label class='mr20' for='userini' style='font-weight:normal'>Anti-cross-site attack (open_basedir)</label>\
						<input type='checkbox' name='logs' id='logs'"+logscheckeds+" /><label for='logs' style='font-weight:normal'>Write access log</label>\
					</div>\
					<div class='line mt10'>\
						<span class='mr5'>Website directory</span>\
						<input class='bt-input-text mr5' type='text' style='width:50%' placeholder='Website root directory' value='"+webpath+"' name='webdir' id='inputPath'>\
						<span onclick='changePath(&quot;inputPath&quot;)' class='glyphicon glyphicon-folder-open cursor mr20'></span>\
						<button class='btn btn-success btn-sm' onclick='setSitePath("+id+")'>Save</button>\
					</div>\
					<div class='line mtb15'>\
						<span class='mr5'>Run directory</span>\
						<select class='bt-input-text' type='text' style='width:50%; margin-right:41px' name='runPath' id='runPath'>"+opt+"</select>\
						<button class='btn btn-success btn-sm' onclick='setSiteRunPath("+id+")' style='margin-top: -1px;'>Save</button>\
					</div>\
					<ul class='help-info-text c7 ptb10'>\
						<li>Some programs need to specify a secondary directory as the running directory, such as ThinkPHP5, Laravel</li>\
						<li>Select your running directory and click save</li>\
					</ul>"
					+'<div class="user_pw_tit" style="margin-top: -8px;padding-top: 11px;">'
						+'<span class="tit">Password access</span>'
						+'<span class="btswitch-p"><input '+(userini.pass?'checked':'')+' class="btswitch btswitch-ios" id="pathSafe" type="checkbox">'
							+'<label class="btswitch-btn phpmyadmin-btn" for="pathSafe" onclick="pathSafe('+id+')"></label>'
						+'</span>'
					+'</div>'
					+'<div class="user_pw" style="margin-top: 10px;display:'+(userini.pass?'block;':'none;')+'">'
						+'<p><span>Authorized account</span><input id="username_get" class="bt-input-text" name="username_get" value="" type="text" placeholder="Please leave blank"></p>'
						+'<p><span>Access password</span><input id="password_get_1" class="bt-input-text" name="password_get_1" value="" type="password" placeholder="Please leave blank"></p>'
						+'<p><span>Repeat password</span><input id="password_get_2" class="bt-input-text" name="password_get_1" value="" type="password" placeholder="Please leave blank"></p>'
						+'<p><button class="btn btn-success btn-sm" onclick="setPathSafe('+id+')">Save</button></p>'
					+'</div>'
				+'</div>';

		$("#webedit-con").html(webPathHtml);
		$("#userini").change(function(){
			$.post('/site/set_dir_user_ini','path='+webpath,function(userini){
				layer.msg(userini.msg+'<p style="color:red;">Note: Setting anti-cross-site requires restarting PHP to take effect!</p>',{icon:userini.status?1:2});
			},'json');
		});

		$("#logs").change(function(){
			$.post('/site/logs_open','id='+id,function(userini){
				layer.msg(userini.msg,{icon:userini.status?1:2});
			},'josn');
		});

	},'json');
}

//Whether to set an access password
function pathSafe(id){
	var isPass = $('#pathSafe').prop('checked');
	if(!isPass){
		$(".user_pw").show();
	} else {
		var loadT = layer.msg(lan.public.the,{icon:16,time:10000,shade: [0.3, '#000']});
		$.post('/site/close_has_pwd',{id:id},function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			$(".user_pw").hide();
		},'json');
	}
}

//Set an access password
function setPathSafe(id){
	var username = $("#username_get").val();
	var pass1 = $("#password_get_1").val();
	var pass2 = $("#password_get_2").val();
	if(pass1 != pass2){
		layer.msg('The two entered passwords do not match!',{icon:2});
		return;
	}
	var loadT = layer.msg('Processing, please wait...',{icon:16,time:10000,shade: [0.3, '#000']});
	$.post('/site/set_has_pwd',{id:id,username:username,password:pass1},function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}

//Submit the run directory
function setSiteRunPath(id){
	var NewPath = $("#runPath").val();
	var loadT = layer.msg(lan.public.the,{icon:16,time:10000,shade: [0.3, '#000']});
	$.post('/site/set_site_run_path','id='+id+'&runPath='+NewPath,function(rdata){
		layer.close(loadT);
		var ico = rdata.status?1:2;
		layer.msg(rdata.msg,{icon:ico});
	},'json');
}

//Submit Site Directory
function setSitePath(id){
	var NewPath = $("#inputPath").val();
	var loadT = layer.msg('Processing, please wait...',{icon:16,time:10000,shade: [0.3, '#000']});
	$.post('/site/set_path','id='+id+'&path='+NewPath,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}

//Modify site notes
function webBakEdit(id){
	$.post("/data?action=getKey','table=sites&key=ps&id="+id,function(rdata){
		var webBakHtml = "<div class='webEdit-box padding-10'>\
					<div class='line'>\
					<label><span>"+lan.site.note_ph+"</span></label>\
					<div class='info-r'>\
					<textarea name='beizhu' id='webbeizhu' col='5' style='width:96%'>"+rdata+"</textarea>\
					<br><br><button class='btn btn-success btn-sm' onclick='SetSitePs("+id+")'>Save</button>\
					</div>\
					</div>";
		$("#webedit-con").html(webBakHtml);
	});
}


//set default document
function setIndexEdit(id){
	$.post('/site/get_index','id='+id,function(data){
		var rdata = data['index'];
		rdata = rdata.replace(new RegExp(/(,)/g), "\n");
		var setIndexHtml = "<div id='SetIndex'><div class='SetIndex'>\
				<div class='line'>\
						<textarea class='bt-input-text' id='Dindex' name='files' style='height: 180px; width:50%; line-height:20px'>"+rdata+"</textarea>\
						<button type='button' class='btn btn-success btn-sm pull-right' onclick='setIndexList("+id+")' style='margin: 70px 130px 0px 0px;'>"+lan.public.save+"</button>\
				</div>\
				<ul class='help-info-text c7 ptb10'>\
					<li>Default documents, one per line, top-to-bottom priority.</li>\
				</ul>\
				</div></div>";
		$("#webedit-con").html(setIndexHtml);
	},'json');
}

/**
* stop a site
* @param {Int} wid site ID
* @param {String} wname website name
*/
function webStop(wid, wname) {
	layer.confirm('The site will be inaccessible after deactivation, do you really want to deactivate this site?', {icon:3,closeBtn:2},function(index) {
		if (index > 0) {
			var loadT = layer.load();
			$.post("/site/stop","id=" + wid + "&name=" + wname, function(ret) {
				layer.msg(ret.msg,{icon:ret.status?1:2})
				layer.close(loadT);
				getWeb(1);
			},'json');
		}
	});
}

/**
* start a website
* @param {Number} wid site ID
* @param {String} wname website name
*/
function webStart(wid, wname) {
	layer.confirm('About to start the site, do you really want to enable this site?',{icon:3,closeBtn:2}, function(index) {
		if (index > 0) {
			var loadT = layer.load()
			$.post("/site/start","id=" + wid + "&name=" + wname, function(ret) {
				layer.msg(ret.msg,{icon:ret.status?1:2})
				layer.close(loadT);
				getWeb(1);
			},'json');
		}
	});
}

/**
 * delete a website
 * @param {Number} wid Site ID
 * @param {String} wname website name
 */
function webDelete(wid, wname){
	var thtml = "<div class='options'>\
	    	<label><input type='checkbox' id='delpath' name='path'><span>Root directory</span></label>\
	    	</div>";
	var info = 'Whether to delete the root directory with the same name';
	safeMessage('Delete site '+"["+wname+"]",info, function(){
		var path='';
		if($("#delpath").is(":checked")){
			path='&path=1';
		}
		var loadT = layer.msg('Processing, please wait...',{icon:16,time:10000,shade: [0.3, '#000']});
		$.post("/site/delete","id=" + wid + "&webname=" + wname + path, function(ret){
			layer.closeAll();
			layer.msg(ret.msg,{icon:ret.status?1:2})
			getWeb(1);
		},'json');
	},thtml);
}


//batch deletion
function allDeleteSite(){
	var checkList = $("input[name=id]");
	var dataList = new Array();
	for(var i=0;i<checkList.length;i++){
		if(!checkList[i].checked) continue;
		var tmp = new Object();
		tmp.name = checkList[i].title;
		tmp.id = checkList[i].value;
		dataList.push(tmp);
	}

	var thtml = "<div class='options'>\
	    	<label style=\"width:100%;\"><input type='checkbox' id='delpath' name='path'><span>"+lan.site.all_del_info+"</span></label>\
	    	</div>";
	safeMessage(lan.site.all_del_site,"<a style='color:red;'>"+lan.get('del_all_site',[dataList.length])+"</a>",function(){
		layer.closeAll();
		var path = '';
		if($("#delpath").is(":checked")){
			path='&path=1';
		}
		syncDeleteSite(dataList,0,'',path);
	},thtml);
}

//Simulate synchronization to start batch deletion
function syncDeleteSite(dataList,successCount,errorMsg,path){
	if(dataList.length < 1) {
		layer.msg(lan.get('del_all_site_ok',[successCount]),{icon:1});
		return;
	}
	var loadT = layer.msg(lan.get('del_all_task_the',[dataList[0].name]),{icon:16,time:0,shade: [0.3, '#000']});
	$.ajax({
			type:'POST',
			url:'/site?action=DeleteSite',
			data:'id='+dataList[0].id+'&webname='+dataList[0].name+path,
			async: true,
			success:function(frdata){
				layer.close(loadT);
				if(frdata.status){
					successCount++;
					$("input[title='"+dataList[0].name+"']").parents("tr").remove();
				}else{
					if(!errorMsg){
						errorMsg = '<br><p>'+lan.site.del_err+':</p>';
					}
					errorMsg += '<li>'+dataList[0].name+' -> '+frdata.msg+'</li>'
				}

				dataList.splice(0,1);
				syncDeleteSite(dataList,successCount,errorMsg,path);
			}
	});
}


/**
 * Domain Name Management
 * @param {Int} id Site ID
 */
function domainEdit(id, name, msg, status) {
	$.post('/site/get_domain' ,{pid:id}, function(domain) {

		var echoHtml = "";
		for (var i = 0; i < domain.length; i++) {
			echoHtml += "<tr>\
				<td><a title='"+lan.site.click_access+"' target='_blank' href='http://" + domain[i].name + ":" + domain[i].port + "' class='btlinkbed'>" + domain[i].name + "</a></td>\
				<td><a class='btlinkbed'>" + domain[i].port + "</a></td>\
				<td class='text-center'><a class='table-btn-del' href='javascript:;' onclick=\"delDomain(" + id + ",'" + name + "','" + domain[i].name + "','" + domain[i].port + "',1)\"><span class='glyphicon glyphicon-trash'></span></a></td>\
				</tr>";
		}
		var bodyHtml = "<textarea id='newdomain' class='bt-input-text' style='height: 100px; width: 340px;padding:5px 10px;line-height:20px'></textarea>\
								<input type='hidden' id='newport' value='80' />\
								<button type='button' class='btn btn-success btn-sm pull-right' style='margin:30px 35px 0 0' onclick=\"domainAdd(" + id + ",'" + name + "',1)\">Add</button>\
							<div class='divtable mtb15' style='height:350px;overflow:auto'>\
								<table class='table table-hover' width='100%'>\
								<thead><tr><th>"+lan.site.domain+"</th><th width='70px'>Port</th><th width='50px' class='text-center'>Action</th></tr></thead>\
								<tbody id='checkDomain'>" + echoHtml + "</tbody>\
								</table>\
							</div>";
		$("#webedit-con").html(bodyHtml);
		if(msg != undefined){
			layer.msg(msg,{icon:status?1:5});
		}
		var placeholder = "<div class='placeholder c9' style='left:28px;width:330px;top:16px;'>Fill in one domain name per line, the default is port 80<br>Add method for pan-analytics *.domain.com<br>If the additional port format is www.domain.com:88</div>";
		$('#newdomain').after(placeholder);
		$(".placeholder").click(function(){
			$(this).hide();
			$('#newdomain').focus();
		})
		$('#newdomain').focus(function() {
		    $(".placeholder").hide();
		});

		$('#newdomain').blur(function() {
			if($(this).val().length==0){
				$(".placeholder").show();
			}
		});
		$("#newdomain").on("input",function(){
			var str = $(this).val();
			if(isChineseChar(str)) {
				$('.btn-zhm').show();
			} else{
				$('.btn-zhm').hide();
			}
		})
		//checkDomain();
	},'json');
}

function DomainRoot(id, name,msg) {
	$.get('/data?action=getData&table=domain&list=True&search=' + id, function(domain) {
		var echoHtml = "";
		for (var i = 0; i < domain.length; i++) {
			echoHtml += "<tr><td><a title='"+lan.site.click_access+"' target='_blank' href='http://" + domain[i].name + ":" + domain[i].port + "' class='btlinkbed'>" + domain[i].name + "</a></td><td><a class='btlinkbed'>" + domain[i].port + "</a></td><td class='text-center'><a class='table-btn-del' href='javascript:;' onclick=\"delDomain(" + id + ",'" + name + "','" + domain[i].name + "','" + domain[i].port + "',1)\"><span class='glyphicon glyphicon-trash'></span></a></td></tr>";
		}
		var index = layer.open({
			type: 1,
			skin: 'demo-class',
			area: '450px',
			title: lan.site.domain_man,
			closeBtn: 2,
			shift: 0,
			shadeClose: true,
			content: "<div class='divtable padding-10'>\
						<textarea id='newdomain'></textarea>\
						<input type='hidden' id='newport' value='80' />\
						<button type='button' class='btn btn-success btn-sm pull-right' style='margin:30px 35px 0 0' onclick=\"domainAdd(" + id + ",'" + name + "')\">Add</button>\
						<table class='table table-hover' width='100%' style='margin-bottom:0'>\
						<thead><tr><th>"+lan.site.domain+"</th><th width='70px'>"+lan.site.port+"</th><th width='50px' class='text-center'>"+lan.site.operate+"</th></tr></thead>\
						<tbody id='checkDomain'>" + echoHtml + "</tbody>\
						</table></div>"
		});
		if(msg != undefined){
			layer.msg(msg,{icon:1});
		}
		var placeholder = "<div class='placeholder'>"+lan.site.domain_help+"</div>";
		$('#newdomain').after(placeholder);
		$(".placeholder").click(function(){
			$(this).hide();
			$('#newdomain').focus();
		})
		$('#newdomain').focus(function() {
		    $(".placeholder").hide();
		});

		$('#newdomain').blur(function() {
			if($(this).val().length==0){
				$(".placeholder").show();
			}
		});
		$("#newdomain").on("input",function(){
			var str = $(this).val();
			if(isChineseChar(str)) $('.btn-zhm').show();
			else $('.btn-zhm').hide();
		})
		//checkDomain();
	});
}
//Edit domain name/port
function cancelSend(){
	$(".changeDomain,.changePort").hide().prev().show();
	$(".changeDomain,.changePort").remove();
}
//Traverse domains
function checkDomain() {
	$("#checkDomain tr").each(function() {
		var $this = $(this);
		var domain = $(this).find("td:first-child").text();
		$(this).find("td:first-child").append("<i class='lading'></i>");
	});
}

/**
* Add domain name
* @param {Int} id website id
* @param {String} webname primary domain name
*/
function domainAdd(id, webname,type) {
	var Domain = $("#newdomain").val().split("\n");

	var domainlist = '';
	for(var i=0; i<Domain.length; i++){
		domainlist += Domain[i]+ ',';
	}

	if(domainlist.length < 3){
		layer.msg(lan.site.domain_empty,{icon:5});
		return;
	}

	domainlist = domainlist.substring(0,domainlist.length-1);
	var loadT = layer.load();
	var data = "domain=" + domainlist + "&webname=" + webname + "&id=" + id;
	$.post('/site/add_domain', data, function(retuls) {
		layer.close(loadT);
		domainEdit(id, webname, retuls.msg, retuls.status);
	},'json');
}

/**
* delete domain
* @param {Number} wid site ID
* @param {String} wname main domain name
* @param {String} domain The domain name to delete
* @param {Number} port corresponding port
*/
function delDomain(wid, wname, domain, port,type) {
	var num = $("#checkDomain").find("tr").length;
	if(num==1){
		layer.msg(lan.site.domain_last_cannot);
	}
	layer.confirm(lan.site.domain_del_confirm,{icon:3,closeBtn:2}, function(index) {
		var url = "/site/del_domain"
		var data = "id=" + wid + "&webname=" + wname + "&domain=" + domain + "&port=" + port;
		var loadT = layer.msg(lan.public.the_del,{time:0,icon:16});
		$.post(url,data, function(ret) {
			layer.close(loadT);
			layer.msg(ret.msg,{icon:ret.status?1:2})
			if(type == 1){
				layer.close(loadT);
				domainEdit(wid,wname)
			}else{
				layer.closeAll();
				DomainRoot(wid, wname);
			}
		},'json');
	});
}

/**
* Determine IP/domain name format
* @param {String} domain source text
* @return bool
*/
function isDomain(domain) {
	//domain = 'http://'+domain;
	var re = new RegExp();
	re.compile("^[A-Za-z0-9-_]+\\.[A-Za-z0-9-_%&\?\/.=]+$");
	if (re.test(domain)) {
		return (true);
	} else {
		return (false);
	}
}


/**
* Set up database backup
* @param {Number} sign operation sign
* @param {Number} id number
* @param {String} name primary domain name
*/
function webBackup(id, name) {
	var loadT =layer.msg('Backing up, please wait...', {icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/to_backup', "id="+id, function(rdata) {
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});

		getBackup(id);
	},'json');
}

/**
* Delete website backup
* @param {Number} webid website number
* @param {Number} id file number
* @param {String} name primary domain name
*/
function webBackupDelete(id,pid){
	layer.confirm('Do you really want to delete the backup package?',{title:'Delete backup file!',icon:3,closeBtn:2},function(index){
		var loadT =layer.msg('Deleting, please wait...', {icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site/del_backup','id='+id, function(rdata){
			layer.closeAll();
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			getBackup(pid);
		},'json');
	})
}

function getBackup(id,name,page) {

	if(page == undefined){
		page = '1';
	}
	$.post('/site/get_backup','search=' + id + '&limit=5&p='+page, function(frdata){
		var body = '';
			for (var i = 0; i < frdata.data.length; i++) {
				if(frdata.data[i].type == '1') {
					continue;
				}

				var ftpdown = "<a class='btlink' href='/files/download?filename="+frdata.data[i].filename+"&name="+frdata.data[i].name+"' target='_blank'>Download</a> | ";
				body += "<tr><td><span class='glyphicon glyphicon-file'></span>"+frdata.data[i].name+"</td>\
						<td>" + (toSize(frdata.data[i].size)) + "</td>\
						<td>" + frdata.data[i].addtime + "</td>\
						<td class='text-right' style='color:#ccc'>"+ ftpdown + "<a class='btlink' href='javascript:;' onclick=\"webBackupDelete('" + frdata.data[i].id + "',"+id+")\">Delete</a></td>\
					</tr>"
			}
		var ftpdown = '';
		frdata.page = frdata.page.replace(/'/g,'"').replace(/getBackup\(/g,"getBackup(" + id + ",0,");

		if(name == 0){
			var sBody = "<table width='100%' id='webBackupList' class='table table-hover'>\
						<thead><tr><th>File name</th><th>Size</th><th>Time</th><th width='140px' class='text-right'>Action</th></tr></thead>\
						<tbody id='webBackupBody' class='list-list'>"+body+"</tbody>\
						</table>"
			$("#webBackupList").html(sBody);
			$(".page").html(frdata.page);
			return;
		}
		layer.closeAll();
		layer.open({
			type: 1,
			skin: 'demo-class',
			area: '700px',
			title: 'Package backup',
			closeBtn: 2,
			shift: 0,
			shadeClose: false,
			content: "<div class='bt-form ptb15 mlr15' id='webBackup'>\
						<button class='btn btn-default btn-sm' style='margin-right:10px' type='button' onclick=\"webBackup('" + frdata['site']['id'] + "','" +  frdata['site']['name'] + "')\">Backup</button>\
						<div class='divtable mtb15' style='margin-bottom:0'><table width='100%' id='webBackupList' class='table table-hover'>\
						<thead><tr><th>File name</th><th>Size</th><th>Time</th><th width='140px' class='text-right'>Action</th></tr></thead>\
						<tbody id='webBackupBody' class='list-list'>"+body+"</tbody>\
						</table><div class='page'>"+frdata.page+"</div></div></div>"
		});
	},'json');

}

function goSet(num) {
	//pick selected object
	var el = document.getElementsByTagName('input');
	var len = el.length;
	var data = '';
	var a = '';
	var count = 0;
	//Construct POST data
	for (var i = 0; i < len; i++) {
		if (el[i].checked == true && el[i].value != 'on') {
			data += a + count + '=' + el[i].value;
			a = '&';
			count++;
		}
	}
	//Determine the type of operation
	if(num==1){
		reAdd(data);
	}
	else if(num==2){
		shift(data);
	}
}


//set default document
function setIndex(id){
	var quanju = (id==undefined)?lan.site.public_set:lan.site.local_site;
	var data=id==undefined?"":"id="+id;
	$.post('/site?action=GetIndex',data,function(rdata){
		rdata= rdata.replace(new RegExp(/(,)/g), "\n");
		layer.open({
				type: 1,
				area: '500px',
				title: lan.site.setindex,
				closeBtn: 2,
				shift: 5,
				shadeClose: true,
				content:"<form class='bt-form' id='SetIndex'><div class='SetIndex'>"
				+"<div class='line'>"
				+"	<span class='tname' style='padding-right:2px'>"+lan.site.default_doc+"</span>"
				+"	<div class='info-r'>"
				+"		<textarea id='Dindex' name='files' style='line-height:20px'>"+rdata+"</textarea>"
				+"		<p>"+quanju+lan.site.default_doc_help+"</p>"
				+"	</div>"
				+"</div>"
				+"<div class='bt-form-submit-btn'>"
				+"	<button type='button' id='web_end_time' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>"+lan.public.cancel+"</button>"
			    +"    <button type='button' class='btn btn-success btn-sm btn-title' onclick='setIndexList("+id+")'>"+lan.public.ok+"</button>"
		        +"</div>"
				+"</div></form>"
		});
	});
}

//set default site
function setDefaultSite(){
	var name = $("#defaultSite").val();
	var loadT = layer.msg('Processing, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/set_default_site','name='+name,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:5});
	},'json');
}


//default site
function getDefaultSite(){
	$.post('/site/get_default_site','',function(rdata){
		var opt = '<option value="off">Default site not set</option>';
		var selected = '';
		for(var i=0;i<rdata.sites.length;i++){
			selected = '';
			if(rdata.defaultSite == rdata.sites[i].name) selected = 'selected';
			opt += '<option value="' + rdata.sites[i].name + '" ' + selected + '>' + rdata.sites[i].name + '</option>';
		}

		layer.open({
				type: 1,
				area: '530px',
				title: 'Set default site',
				closeBtn: 2,
				shift: 5,
				shadeClose: true,
				content:'<div class="bt-form ptb15 pb70">\
							<p class="line">\
								<span class="tname text-right">Default site</span>\
								<select id="defaultSite" class="bt-input-text" style="width: 300px;">'+opt+'</select>\
							</p>\
							<ul class="help-info-text c6 plr20">\
							    <li>After setting the default site, all unbound domain names and IPs are directed to the default site</li>\
							    <li>Can effectively prevent malicious analysis</li>\
						    </ul>\
							<div class="bt-form-submit-btn">\
								<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">Cancel</button>\
								<button class="btn btn-success btn-sm btn-title" onclick="setDefaultSite()">Submit</button>\
							</div>\
						</div>'
		});
	},'json');
}

function setIndexList(id){
	var Dindex = $("#Dindex").val().replace(new RegExp(/(\n)/g), ",");
	if(id == undefined ){
		var data="id=&index="+Dindex;
	} else{
		var data="id="+id+"&index="+Dindex;
	}
	var loadT= layer.load(2);
	$.post('/site/set_index',data,function(rdata){
		layer.close(loadT);
		var ico = rdata.status? 1:5;
		layer.msg(rdata.msg,{icon:ico});
	},'json');
}


/*site modification*/
function webEdit(id,website,endTime,addtime){
	var eMenu = "<p onclick='dirBinding("+id+")' title='Subdirectory binding'>Binding</p>"
	+"<p onclick='webPathEdit("+id+")' title='website directory'>Directory</p>"
	+"<p onclick='limitNet("+id+")' title='Traffic restrictions'>Traffic</p>"
	+"<p onclick=\"rewrite('"+website+"')\" title='Rewrite rule'>Rewrite</p>"
	+"<p onclick='setIndexEdit("+id+")' title='Default document'>Default</p>"
	+"<p onclick=\"configFile('"+website+"')\" title='Configuration file'>Config</p>"
	+"<p onclick=\"setSSL("+id+",'"+website+"')\" title='SSL'>SSL</p>"
	+"<p onclick=\"phpVersion('"+website+"')\" title='PHP version'>PHP</p>"
	// +"<p onclick=\"to301('"+website+"')\" title='Redirect'>Redirect</p>"
	// +"<p onclick=\"proxyList('"+website+"')\" title='Reverse proxy'>Reverse proxy</p>"
	+"<p id='site_"+id+"' onclick=\"security('"+id+"','"+website+"')\" title='Anti-theft chain'>Security</p>"
	+"<p id='site_"+id+"' onclick=\"getSiteLogs('"+website+"')\" title='View site request logs'>Log</p>";
	layer.open({
		type: 1,
		area: '780px',
		title: 'Site modification ['+website+']  --  add time ['+addtime+']',
		closeBtn: 2,
		shift: 0,
		content: "<div class='bt-form'><div class='bt-w-main'>"
			+"<div class='bt-w-menu'>"
			+"	<p class='bgw'  onclick=\"domainEdit(" + id + ",'" + website + "')\">Domain</p>"
			+"	"+eMenu+""
			+"</div>"
			+"<div id='webedit-con' class='bt-w-con webedit-con pd15'></div>"
			+"</div></div>"
	});
	domainEdit(id,website);
	//Domain name input prompt
	var placeholder = "<div class='placeholder'>Fill in one domain name per line, the default is port 80<br>Add method for pan-analytics *.domain.com<br>If the additional port format is www.domain.com:88</div>";
	$('#newdomain').after(placeholder);
	$(".placeholder").click(function(){
		$(this).hide();
		$('#newdomain').focus();
	});
	$('#newdomain').focus(function() {
	    $(".placeholder").hide();
	});

	$('#newdomain').blur(function() {
		if($(this).val().length==0){
			$(".placeholder").show();
		}
	});
	//toggle
	var $p = $(".bt-w-menu p");
	$p.click(function(){
		$(this).addClass("bgw").siblings().removeClass("bgw");
	});
}

//Get website logs
function getSiteLogs(siteName){
	var loadT = layer.msg('Processing, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/get_logs',{siteName:siteName},function(logs){
		console.log(logs);
		layer.close(loadT);
		if(logs.status !== true){
			logs.msg = '';
		}
		if (logs.msg == '') logs.msg = 'There are currently no logs.';
		var phpCon = '<textarea wrap="off" readonly="" style="white-space: pre;margin: 0px;width: 500px;height: 520px;background-color: #333;color:#fff; padding:0 5px" id="error_log">'+logs.msg+'</textarea>';
		$("#webedit-con").html(phpCon);
		var ob = document.getElementById('error_log');
		ob.scrollTop = ob.scrollHeight;
	},'json');
}


//anti-theft chain
function security(id,name){
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/get_security',{id:id,name:name},function(rdata){
		layer.close(loadT);
		var mbody = '<div>'
					+'<p style="margin-bottom:8px"><span style="display: inline-block; width: 60px;">URL suffix</span><input class="bt-input-text" type="text" name="sec_fix" value="'+rdata.fix+'" style="margin-left: 5px;width: 425px;height: 30px;margin-right:10px;'+(rdata.status?'background-color: #eee;':'')+'" placeholder="Separate multiples with commas, for example：png,jpeg,jpg,gif,zip" '+(rdata.status?'readonly':'')+'></p>'
					+'<p style="margin-bottom:8px"><span style="display: inline-block; width: 60px;">Licensed Domains</span><input class="bt-input-text" type="text" name="sec_domains" value="'+rdata.domains+'" style="margin-left: 5px;width: 425px;height: 30px;margin-right:10px;'+(rdata.status?'background-color: #eee;':'')+'" placeholder="Wildcards are supported, multiple domain names should be separated by commas, for example：*.test.com,test.com" '+(rdata.status?'readonly':'')+'></p>'
					+'<div class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="sec_status" onclick="setSecurity(\''+name+'\','+id+')" '+(rdata.status?'checked':'')+'>Enable</label></div>'
					+'<ul class="help-info-text c7 ptb10">'
						+'<li>By default, resources are allowed to be accessed directly, that is, requests with an empty HTTP_REFERER are not restricted</li>'
						+'<li>Use commas (,) to separate multiple URL suffixes and domain names, such as: png, jpeg, zip, js</li>'
						+'<li>When the anti-theft chain is triggered, it will directly return to the 404 status</li>'
					+'</ul>'
				+'</div>'
		$("#webedit-con").html(mbody);
	},'json');
}

//Setting up anti-leech
function setSecurity(name,id){
	var data = {
		fix:$("input[name='sec_fix']").val(),
		domains:$("input[name='sec_domains']").val(),
		status:$("input[name='sec_status']").val(),
		name:name,
		id:id
	}
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/set_security',data,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		if(rdata.status) setTimeout(function(){Security(id,name);},1000);
	},'json');
}


//Trojan scan
function CheckSafe(id,act){
	if(act != undefined){
		var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site?action=CheckSafe','id='+id,function(rdata){
			$(".btnStart").hide()
			setTimeout(function(){
				CheckSafe(id);
			},3000);
			GetTaskCount();
			layer.close(loadT)
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
		});

		return;
	}

   $.post('/site?action=GetCheckSafe','id='+id,function(rdata){
   		var done = "<button type='button' class='btn btn-success btn-sm btnStart mr5'  onclick=\"CheckSafe("+id+",1)\">"+lan.site.start_scan+"</button>\
   					<button type='button' class='btn btn-default btn-sm btnStart mr20'  onclick=\"UpdateRulelist()\">"+lan.site.update_lib+"</button>\
   					<a class='f14 mr20' style='color:green;'>"+lan.site.scanned+"："+rdata.count+"</a><a class='f14' style='color:red;'>"+lan.site.risk_quantity+"："+rdata.error+"</a>";

   		if(rdata['scan']) done = "<a class='f14 mr20' style='color:green;'>"+lan.site.scanned+"："+rdata.count+"</a><a class='f14' style='color:red;'>"+lan.site.risk_quantity+"："+rdata.error+"</a>";
		var echoHtml = "<div class='mtb15'>"
					   + done
					   +"</div>"
		for(var i=0;i<rdata.phpini.length;i++){
			echoHtml += "<tr><td>"+lan.site.danger_fun+"</td><td>"+lan.site.danger+"</td><td>"+lan.site.danger_fun_no+"："+rdata.phpini[i].function+"<br>"+lan.site.file+"：<a style='color: red;' href='javascript:;' onclick=\"OnlineEditFile(0,'/home/slemp/server/php/"+rdata.phpini[i].version+"/etc/php.ini')\">/home/slemp/server/php/"+rdata.phpini[i].version+"/etc/php.ini</a></td></tr>";
		}

		if(!rdata.sshd){
			echoHtml += "<tr><td>"+lan.site.ssh_port+"</td><td>"+lan.site.high_risk+"</td><td>"+lan.site.sshd_tampering+"</td></tr>";
		}

		if(!rdata.userini){
			echoHtml += "<tr><td>"+lan.site.xss_attack+"</td><td>"+lan.site.danger+"</td><td>"+lan.site.site_xss_attack+"</td></tr>";
		}

		for(var i=0;i<rdata.data.length;i++){
			echoHtml += "<tr><td>"+rdata.data[i].msg+"</td><td>"+rdata.data[i].level+"</td><td>文件：<a style='color: red;' href='javascript:;' onclick=\"OnlineEditFile(0,'"+rdata.data[i].filename+"')\">"+rdata.data[i].filename+"</a><br>"+lan.site.mod_time+"："+rdata.data[i].etime+"<br>"+lan.site.code+"："+rdata.data[i].code+"</td></tr>";
		}

		var body = "<div>"
					+"<div class='divtable mtb15'><table class='table table-hover' width='100%' style='margin-bottom:0'>"
				  	+"<thead><tr><th width='100px'>"+lan.site.behavior+"</th><th width='70px'>"+lan.site.risk+"</th><th>"+lan.site.details+"</th></tr></thead>"
				   	+"<tbody id='checkDomain'>" + echoHtml + "</tbody>"
				   	+"</table></div>"

		$("#webedit-con").html(body);
		$(".btnStart").click(function(){
			fly('btnStart');
		});
		if(rdata['scan']){
			c = $("#site_"+id).attr('class');
			if(c != 'active') return;
			setTimeout(function(){
				CheckSafe(id);
			},1000);
		}
	});
}

function UpdateRulelist(){
	var loadT = layer.msg(lan.site.to_update,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=UpdateRulelist','',function(rdata){
		layer.close(loadT)
		layer.msg(rdata.msg,{icon:rdata.status?1:5});
	});

}


//Traffic restrictions
function limitNet(id){
	$.post('/site/get_limit_net','id='+id, function(rdata){
		var status_selected = rdata.perserver != 0?'checked':'';
		if(rdata.perserver == 0){
			rdata.perserver = 300;
			rdata.perip = 25;
			rdata.limit_rate = 512;
		}
		var limitList = "<option value='1' "+((rdata.perserver == 0 || rdata.perserver == 300)?'selected':'')+">"+lan.site.limit_net_1+"</option>"
						+"<option value='2' "+((rdata.perserver == 200)?'selected':'')+">"+lan.site.limit_net_2+"</option>"
						+"<option value='3' "+((rdata.perserver == 50)?'selected':'')+">"+lan.site.limit_net_3+"</option>"
						+"<option value='4' "+((rdata.perserver == 500)?'selected':'')+">"+lan.site.limit_net_4+"</option>"
						+"<option value='5'  "+((rdata.perserver == 400)?'selected':'')+">"+lan.site.limit_net_5+"</option>"
						+"<option value='6' "+((rdata.perserver == 60)?'selected':'')+">"+lan.site.limit_net_6+"</option>"
						+"<option value='7' "+((rdata.perserver == 150)?'selected':'')+">"+lan.site.limit_net_7+"</option>"
		var body = "<div class='dirBinding flow c4'>"
				+'<p class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="status" '+status_selected+' onclick="saveLimitNet('+id+')" style="width:15px;height:15px;margin-right:5px" />'+lan.site.limit_net_8+'</label></p>'
				+"<p class='line' style='padding:10px 0'><span class='span_tit mr5'>"+lan.site.limit_net_9+"：</span><select class='bt-input-text mr20' name='limit' style='width:90px'>"+limitList+"</select></p>"
			    +"<p class='line' style='padding:10px 0'><span class='span_tit mr5'>"+lan.site.limit_net_10+"：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='perserver' value='"+rdata.perserver+"' /></p>"
			    +"<p class='line' style='padding:10px 0'><span class='span_tit mr5'>"+lan.site.limit_net_12+"：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='perip' value='"+rdata.perip+"' /></p>"
			    +"<p class='line' style='padding:10px 0'><span class='span_tit mr5'>"+lan.site.limit_net_14+"：</span><input class='bt-input-text mr20' style='width: 90px;' type='number' name='limit_rate' value='"+rdata.limit_rate+"' /></p>"
			    +"<button class='btn btn-success btn-sm mt10' onclick='saveLimitNet("+id+",1)'>"+lan.public.save+"</button>"
			    +"</div>"
				+"<ul class='help-info-text c7 mtb15'><li>"+lan.site.limit_net_11+"</li><li>"+lan.site.limit_net_13+"</li><li>"+lan.site.limit_net_15+"</li></ul>"
		$("#webedit-con").html(body);

		$("select[name='limit']").change(function(){
			var type = $(this).val();
			perserver = 300;
			perip = 25;
			limit_rate = 512;
			switch(type){
				case '1':
					perserver = 300;
					perip = 25;
					limit_rate = 512;
					break;
				case '2':
					perserver = 200;
					perip = 10;
					limit_rate = 1024;
					break;
				case '3':
					perserver = 50;
					perip = 3;
					limit_rate = 2048;
					break;
				case '4':
					perserver = 500;
					perip = 10;
					limit_rate = 2048;
					break;
				case '5':
					perserver = 400;
					perip = 15;
					limit_rate = 1024;
					break;
				case '6':
					perserver = 60;
					perip = 10;
					limit_rate = 512;
					break;
				case '7':
					perserver = 150;
					perip = 4;
					limit_rate = 1024;
					break;
			}

			$("input[name='perserver']").val(perserver);
			$("input[name='perip']").val(perip);
			$("input[name='limit_rate']").val(limit_rate);
		});
	},'json');
}


//Save traffic limit configuration
function saveLimitNet(id, type){
	var isChecked = $("input[name='status']").attr('checked');
	if(isChecked == undefined || type == 1 ){
		var data = 'id='+id+'&perserver='+$("input[name='perserver']").val()+'&perip='+$("input[name='perip']").val()+'&limit_rate='+$("input[name='limit_rate']").val();
		var loadT = layer.msg(lan.public.config,{icon:16,time:10000})
		$.post('/site/save_limit_net',data,function(rdata){
			layer.close(loadT);
			limitNet(id);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		},'json');
	}else{
		var loadT = layer.msg(lan.public.config,{icon:16,time:10000})
		$.post('/site/close_limit_net',{id:id},function(rdata){
			layer.close(loadT);
			limitNet(id);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		},'json');
	}
}


//subdirectory binding
function dirBinding(id){
	$.post('/site/get_dir_binding',{'id':id},function(data){
		var rdata = data['data'];
		var echoHtml = '';
		for(var i=0;i<rdata.binding.length;i++){
			echoHtml += "<tr><td>"+rdata.binding[i].domain+"</td><td>"+rdata.binding[i].port+"</td><td>"+rdata.binding[i].path+"</td><td class='text-right'><a class='btlink' href='javascript:setDirRewrite("+rdata.binding[i].id+");'>Rewrite</a> | <a class='btlink' href='javascript:delDirBind("+rdata.binding[i].id+","+id+");'>Delete</a></td></tr>";
		}

		var dirList = '';
		for(var n=0;n<rdata.dirs.length;n++){
			dirList += "<option value='"+rdata.dirs[n]+"'>"+rdata.dirs[n]+"</option>";
		}

		var body = "<div class='dirBinding c5'>"
			   + "Domain name: <input class='bt-input-text mr20' type='text' name='domain' />"
			   + "Subdirectories: <select class='bt-input-text mr20' name='dirName'>"+dirList+"</select>"
			   + "<button class='btn btn-success btn-sm' onclick='addDirBinding("+id+")'>Add</button>"
			   + "</div>"
			   + "<div class='divtable mtb15' style='height:470px;overflow:auto'><table class='table table-hover' width='100%' style='margin-bottom:0'>"
			   + "<thead><tr><th>Domain name</th><th width='70'>Port</th><th width='100'>Subdirectory</th><th width='100' class='text-right'>Action</th></tr></thead>"
			   + "<tbody id='checkDomain'>" + echoHtml + "</tbody>"
			   + "</table></div>";

		$("#webedit-con").html(body);
	},'json');
}

//Subdirectory rewrite rule
function setDirRewrite(id){
	$.post('/site/get_dir_bind_rewrite','id='+id,function(rdata){
		if(!rdata.status){
			var confirmObj = layer.confirm('Do you really want to create separate rewrite rules for this subdirectory?',{icon:3,closeBtn:2},function(){
				$.post('/site/get_dir_bind_rewrite','id='+id+'&add=1',function(rdata){
					layer.close(confirmObj);
					showRewrite(rdata);
				},'json');
			});
			return;
		}
		showRewrite(rdata);
	},'json');
}

//display rewrite
function showRewrite(rdata){
	var rList = '';
	for(var i=0;i<rdata.rlist.length;i++){
		rList += "<option value='"+rdata.rlist[i]+"'>"+rdata.rlist[i]+"</option>";
	}
	var webBakHtml = "<div class='c5 plr15'>\
						<div class='line'>\
						<select class='bt-input-text mr20' id='myRewrite' name='rewrite' style='width:30%;'>"+rList+"</select>\
						<textarea class='bt-input-text mtb15' style='height: 260px; width: 470px; line-height:18px;padding:5px;' id='rewriteBody'>"+rdata.data+"</textarea></div>\
						<button id='SetRewriteBtn' class='btn btn-success btn-sm' onclick=\"SetRewrite('"+rdata.filename+"')\">Save</button>\
						<ul class='help-info-text c7 ptb10'>\
							<li>Please select your application, if the website cannot be accessed normally after setting rewrite rule, please try to set it back to default</li>\
							<li>You can modify the rewrite rules and save them after modification.</li>\
						</ul>\
						</div>";
	layer.open({
		type: 1,
		area: '500px',
		title: 'Configure rewrite rules',
		closeBtn: 2,
		shift: 5,
		shadeClose: true,
		content:webBakHtml
	});

	$("#myRewrite").change(function(){
		var rewriteName = $(this).val();
		$.post('/files/get_body','path='+rdata['rewrite_dir']+'/'+rewriteName+'.conf',function(fileBody){
			 $("#rewriteBody").val(fileBody.data.data);
		},'json');
	});
}

//Add subdirectory binding
function addDirBinding(id){
	var domain = $("input[name='domain']").val();
	var dirName = $("select[name='dirName']").val();
	if(domain == '' || dirName == '' || dirName == null){
		layer.msg(lan.site.d_s_empty,{icon:2});
		return;
	}

	var data = 'id='+id+'&domain='+domain+'&dirName='+dirName
	$.post('/site/add_dir_bind',data,function(rdata){
		dirBinding(id);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}

//remove subdirectory binding
function delDirBind(id,siteId){
	layer.confirm(lan.site.s_bin_del,{icon:3,closeBtn:2},function(){
		$.post('/site/del_dir_bind','id='+id,function(rdata){
			dirBinding(siteId);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		},'json');
	});
}

//reverse proxy
function proxyList(siteName,type){
	if(type == 1){
		type = $("input[name='status']").attr('checked')?'0':'1';
		toUrl = encodeURIComponent($("input[name='toUrl']").val());
		toDomain = encodeURIComponent($("input[name='toDomain']").val());
		var sub1 = encodeURIComponent($("input[name='sub1']").val());
		var sub2 = encodeURIComponent($("input[name='sub2']").val());
		var data = 'name='+siteName+'&type='+type+'&proxyUrl='+toUrl+'&toDomain=' + toDomain + '&sub1=' + sub1 + '&sub2=' + sub2;
		var loadT = layer.msg(lan.public.the,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site?action=SetProxy',data,function(rdata){
			layer.close(loadT);
			if(rdata.status) {
				Proxy(siteName);
			}else{
				$("input[name='status']").attr('checked',false)
			}
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
		return;
	}
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=GetProxy','name='+siteName,function(rdata){
		layer.close(loadT);
		if(rdata.proxyUrl == null) rdata.proxyUrl = '';
		var status_selected = rdata.status?'checked':'';
		var disabled = rdata.status?'disabled':'';
		var body = "<div>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 104px;'>"+lan.site.proxy_url+"</span><input "+disabled+" class='bt-input-text' type='text' name='toUrl' value='"+rdata.proxyUrl+"' style='margin-left: 5px;width: 380px;height: 30px;margin-right:10px;' placeholder='"+lan.site.proxy_url_info+"' /></p>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 104px;'>"+lan.site.proxy_domain+"</span><input "+disabled+" class='bt-input-text' type='text' name='toDomain' value='"+rdata.toDomain+"' style='margin-left: 5px;width: 380px;height: 30px;margin-right:10px;' placeholder='"+lan.site.proxy_domian_info+"' /></p>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 104px;'>"+lan.site.con_rep+"</span><input "+disabled+" class='bt-input-text' type='text' name='sub1' value='"+rdata.sub1+"' style='margin-left: 5px;width: 182px;height: 30px;margin-right:10px;' placeholder='"+lan.site.con_rep_info+"' />"
			   +"<input class='bt-input-text' type='text' name='sub2' "+disabled+" value='"+rdata.sub2+"' style='margin-left: 5px;width: 183px;height: 30px;margin-right:10px;' placeholder='"+lan.site.to_con+"' /></p>"
			   +'<div class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="status" '+status_selected+' onclick="Proxy(\''+siteName+'\',1)" />'+lan.site.proxy_enable+'</label><label style="margin-left: 18px;"><input '+(rdata.cache?'checked':'')+' type="checkbox" name="status" onclick="OpenCache(\''+siteName+'\',1)" />'+lan.site.proxy_cache+'</label></div>'
			   +'<ul class="help-info-text c7 ptb10">'
			   +'<li>'+lan.site.proxy_help_1+'</li>'
			   +'<li>'+lan.site.proxy_help_2+'</li>'
			   +'<li>'+lan.site.proxy_help_3+'</li>'
			   +'<li>'+lan.site.proxy_help_4+'</li>'
			   +'<li>'+lan.site.proxy_help_5+'</li>'
			   +'</ul>'
			   +"</div>";
			$("#webedit-con").html(body);
	});
}

//enable cache
function openCache(siteName){
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=ProxyCache',{siteName:siteName},function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

//301 redirect
function to301(siteName,type){
	if(type == 1){
		type = $("input[name='status']").attr('checked')?'0':'1';
		toUrl = encodeURIComponent($("input[name='toUrl']").val());
		srcDomain = encodeURIComponent($("select[name='srcDomain']").val());
		var data = 'siteName='+siteName+'&type='+type+'&toDomain='+toUrl+'&srcDomain='+srcDomain;
		$.post('site?action=Set301Status',data,function(rdata){
			To301(siteName);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
		return;
	}
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site?action=Get301Status','siteName='+siteName,function(rdata){
		layer.close(loadT);
		var domain_tmp = rdata.domain.split(',');
		var domains = '';
		var selected = '';
		for(var i=0;i<domain_tmp.length;i++){
			selected = '';
			if(domain_tmp[i] == rdata.src) selected = 'selected';
			domains += "<option value='"+domain_tmp[i]+"' "+selected+">"+domain_tmp[i]+"</option>";
		}

		if(rdata.url == null) rdata.url = '';
		var status_selected = rdata.status?'checked':'';
		var isRead = rdata.status?'readonly':'';
		var body = "<div>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 90px;'>"+lan.site.access_domain+"</span><select class='bt-input-text' name='srcDomain' style='margin-left: 5px;width: 380px;height: 30px;margin-right:10px;"+(rdata.status?'background-color: #eee;':'')+"' "+(rdata.status?'disabled':'')+"><option value='all'>"+lan.site.all_site+"</option>"+domains+"</select></p>"
			   +"<p style='margin-bottom:8px'><span style='display: inline-block; width: 90px;'>"+lan.site.target_url+"</span><input class='bt-input-text' type='text' name='toUrl' value='"+rdata.url+"' style='margin-left: 5px;width: 380px;height: 30px;margin-right:10px;"+(rdata.status?'background-color: #eee;':'')+"' placeholder='"+lan.site.eg_url+"' "+isRead+" /></p>"
			   +'<div class="label-input-group ptb10"><label style="font-weight:normal"><input type="checkbox" name="status" '+status_selected+' onclick="To301(\''+siteName+'\',1)" />'+lan.site.enable_301+'</label></div>'
			   +'<ul class="help-info-text c7 ptb10">'
			   +'<li>'+lan.site.to301_help_1+'</li>'
			   +'<li>'+lan.site.to301_help_2+'</li>'
			   +'</ul>'
			   +"</div>";
			$("#webedit-con").html(body);
	});
}


//document verification
// function file_check(){
// 	$(".check_message").html('<div style="margin-left:100px">\
// 			<input type="checkbox" name="checkDomain" id="checkDomain" checked="">\
// 			<label class="mr20" for="checkDomain" style="font-weight:normal">Verify domain names in advance (discover problems in advance, reduce failure rate)</label>\
// 		</div>');
// $("#lets_help").html('<li>Before applying, please make sure that the domain name is resolved, if not, the audit will fail</li>\
// <li>Let\'s Encrypt free certificate, valid for 3 months, supports multiple domain names. Auto-renewal by default</li>\
// <li>If your site uses a CDN or 301 redirection, the renewal will fail</li>\
// <li>When the SSL default site is not specified, the site without SSL will use HTTPS to directly access the site with SSL enabled</li>');
// }

//certificate folder
function sslAdmin(siteName){
	var loadT = layer.msg('Submitting task...',{icon:16,time:0,shade: [0.3, '#000']});
	$.get('/site/get_cert_list',function(data){
		layer.close(loadT);
		var rdata = data['data'];
		var tbody = '';
		for(var i=0;i<rdata.length;i++){
			tbody += '<tr><td>'+rdata[i].subject+'</td><td>'+rdata[i].dns.join('<br>')+'</td><td>'+rdata[i].notAfter+'</td><td>'+rdata[i].issuer+'</td><td style="text-align: right;"><a onclick="setCertSsl(\''+rdata[i].subject+'\',\''+siteName+'\')" class="btlink">Deploy</a> | <a onclick="removeSsl(\''+rdata[i].subject+'\')" class="btlink">Delete</a></td></tr>'
		}
		var txt = '<div class="mtb15" style="line-height:30px">\
		<button style="margin-bottom: 7px;display:none;" class="btn btn-success btn-sm">Add</button>\
		<div class="divtable"><table class="table table-hover"><thead><tr><th>Domain name</th><th>Trust name</th><th>Expire</th><th>Brand</th><th class="text-right" width="75">Action</th></tr></thead>\
		<tbody>'+tbody+'</tbody>\
		</table></div></div>';
		$(".tab-con").html(txt);
	},'json');
}

//delete certificate
function removeSsl(certName){
	safeMessage('Delete certificate', 'Do you really want to delete the certificate from the certificate folder?',function(){
		var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site/remove_cert',{certName:certName},function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			$("#ssl_admin").click();
		},'json');
	});
}

//Deploy from certificate folder
function setCertSsl(certName,siteName){
	var loadT = layer.msg('Deploying certificate...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/set_cert_to_site',{certName:certName,siteName:siteName},function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}

//ssl
function setSSL(id,siteName){
	var mBody = '<div class="tab-nav">\
					<span class="on" onclick="opSSL(\'lets\','+id+',\''+siteName+'\')">Let\'s Encrypt</span>\
					<span onclick="opSSL(\'other\','+id+',\''+siteName+'\')">Other</span>\
					<span class="sslclose" onclick="closeSSL(\''+siteName+'\')">Close</span>\
					<span id="ssl_admin" onclick="sslAdmin(\''+siteName+'\')">Certificate</span>'
					+ '<div class="ss-text pull-right mr30" style="position: relative;top:-4px">\
	                    <em>Force HTTPS</em>\
	                    <div class="ssh-item">\
	                    	<input class="btswitch btswitch-ios" id="toHttps" type="checkbox">\
	                    	<label class="btswitch-btn" for="toHttps" onclick="httpToHttps(\''+siteName+'\')"></label>\
	                    </div>\
	                </div></div>'
			  + '<div class="tab-con" style="padding: 0px;"></div>'

	$("#webedit-con").html(mBody);
	opSSL('lets',id,siteName);
	$(".tab-nav span").click(function(){
		$(this).addClass("on").siblings().removeClass("on");
	});
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/get_ssl','siteName='+siteName,function(rdata){
		layer.close(loadT);
		$("#toHttps").attr('checked',rdata.data.httpTohttps);
		switch(rdata.data.type){
			case 1:
				$(".tab-nav span").eq(1).addClass("on").siblings().removeClass("on");
				setCookie('letssl',1);
				var lets = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">Key (KEY)<br><textarea id="key" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.data.key+'</textarea></div>'
					+ '<div class="ssl-con-key pull-left">Certificate (PEM format)<br><textarea id="csr" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.data.csr+'</textarea></div>'
					+ '</div>'
					+ '<ul class="help-info-text c7 pull-left"><li>Let\'s Encrypt free certificate has been automatically generated for you;</li>\
						<li>If you need to use other SSL, please switch other certificates, paste your KEY and PEM content, and then save.</li></ul>'
				$(".tab-con").html(lets);
				$(".help-info-text").after("<div class='line mtb15'><button class='btn btn-default btn-sm' onclick=\"ocSSL('close_ssl_conf','"+siteName+"')\" style='margin-left:10px'>Disable SSL</button></div>");
				break;
			case 0:
			case 3:
				$(".tab-nav span").eq(1).addClass("on").siblings().removeClass("on");
				opSSL('other',id,siteName);
				break;
			case 2:
				$(".tab-nav span").eq(0).addClass("on").siblings().removeClass("on");
				opSSL('a',id,siteName);
				break;
		}
	},'json');
}




function closeSSL(siteName){
	var loadT = layer.msg(lan.site.the_msg,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/get_ssl','siteName='+siteName,function(rdata){
		layer.close(loadT);
		switch(rdata.data.type){
			case -1:
				var txt = "<div class='mtb15' style='line-height:30px'>This site is not set up with SSL, if you need to set up SSL, please select switch category to apply for enabling SSL<br>\
					<p style='color:red;'>After disabling SSL, be sure to clear the browser cache before visiting the site</p></div>";
				setCookie('letssl',0);
				$(".tab-con").html(txt);
				break;
			case 0:
				var txt = "Let's Encrypt";
				closeSSLHTML(txt,siteName);
				break;
			case 1:
				var txt = 'Other';
				closeSSLHTML(txt,siteName);
				break;
			case 2:
				var txt = 'SSL';
				closeSSLHTML(txt,siteName);
				break;
		}
	},'json');
}

//Turn off SSL content
function closeSSLHTML(txt,siteName){
	$(".tab-con").html("<div class='line mtb15'>"+lan.get('ssl_enable',[txt])+"</div><div class='line mtb15'><button class='btn btn-success btn-sm' onclick=\"ocSSL('close_ssl_conf','"+siteName+"')\">Disable SSL</button></div>");
}

//Set Http To Https
function httpToHttps(siteName){
	var isHttps = $("#toHttps").prop('checked');
	if(isHttps){
		layer.confirm('After disabling forced HTTPS, you need to clear the browser cache to see the effect, continue?',{icon:3,title:"Turn off Force HTTPS"},function(){
			$.post('/site/close_to_https','siteName='+siteName,function(rdata){
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
			},'json');
		});
	}else{
		$.post('/site/http_to_https','siteName='+siteName,function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		},'json');
	}
}



//SSL
function opSSL(type,id,siteName){
	var lets =  '<div class="btssl"><div class="label-input-group">'
			  + '<div class="line mtb10"><form><span class="tname text-center">Ways of identifying</span><div style="margin-top:7px;display:inline-block"><input type="radio" name="c_type" onclick="file_check()" id="check_file" checked="checked" />\
			  	<label class="mr20" for="check_file" style="font-weight:normal">Document verification</label></label></div></form></div>'
			  + '<div class="check_message line"><div style="margin-left:100px"><input type="checkbox" name="checkDomain" id="checkDomain" checked=""><label class="mr20" for="checkDomain" style="font-weight:normal">Verify domain names in advance (discover problems in advance, reduce failure rate)</label></div></div>'
			  + '</div><div class="line mtb10"><span class="tname text-center">Administrator email</span><input class="bt-input-text" style="width:240px;" type="text" name="admin_email" /></div>'
			  + '<div class="line mtb10"><span class="tname text-center">Domain name</span><ul id="ymlist" style="padding: 5px 10px;max-height:180px;overflow:auto; width:240px;border:#ccc 1px solid;border-radius:3px"></ul></div>'
			  + '<div class="line mtb10" style="margin-left:100px"><button class="btn btn-success btn-sm letsApply">Apply</button></div>'
			  + '<ul class="help-info-text c7" id="lets_help"><li>Before applying, please make sure that the domain name has been resolved, otherwise the review will fail</li>\
			  	<li>Let\'s Encrypt free certificate, valid for 3 months, supports multiple domain names. Auto-renew by default</li>\
			  	<li>If your site uses a CDN or 301 redirection, the renewal will fail</li>\
			  	<li>When the SSL default site is not specified, the site that does not have SSL enabled will use HTTPS to directly access the site that has enabled SSL.</li></ul>'
			  + '</div>';

	var other = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">Key (KEY)<br><textarea id="key" class="bt-input-text"></textarea></div>'
					+ '<div class="ssl-con-key pull-left">Certificate (PEM format)<br><textarea id="csr" class="bt-input-text"></textarea></div>'
					+ '<div class="ssl-btn pull-left mtb15" style="width:100%"><button class="btn btn-success btn-sm" onclick="saveSSL(\''+siteName+'\')">Save</button></div></div>'
					+ '<ul class="help-info-text c7 pull-left"><li>Paste your *.key and *.pem content and save it<a href=\'http://slemp/basoro.id/docs/ssl\' class=\'btlink\' target=\'_blank\'>[help]</a>。</li>\
					<li>If the browser prompts that the certificate chain is incomplete, please check whether the PEM certificate is correctly spliced</li><li>PEM format certificate = domain name certificate.crt + root certificate (root_bundle).crt</li>\
					<li>When the SSL default site is not specified, the site that does not have SSL enabled will use HTTPS to directly access the site that has enabled SSL.</li></ul>';
	switch(type){
		case 'lets':
			if(getCookie('letssl') == 1){
				$.post('/site/get_ssl','siteName='+siteName,function(data){
					var rdata = data['data'];
					if(rdata.csr === false){
						setCookie('letssl',0);
						opSSL(type,id,siteName);
						return;
					}
					var lets = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">Key (KEY)<br><textarea id="key" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.key+'</textarea></div>'
						+ '<div class="ssl-con-key pull-left">Certificate (PEM format)<br><textarea id="csr" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.csr+'</textarea></div>'
						+ '</div>'
						+ '<ul class="help-info-text c7 pull-left"><li>Let\'s Encrypt free certificate has been automatically generated for you</li>\
						<li>If you need to use other SSL, please switch other certificates, paste your KEY and PEM content, and then save.</li></ul>';
					$(".tab-con").html(lets);
					$(".help-info-text").after("<div class='line mtb15'><button class='btn btn-default btn-sm' onclick=\"ocSSL('close_ssl_conf','"+siteName+"')\" style='margin-left:10px'>Disable SSL</button></div>");
				},'json');
				return;
			}
			$(".tab-con").html(lets);
			var opt='';
			$.post('/site/get_site_domains',{id:id}, function(rdata) {
				var data = rdata['data'];
				for(var i=0;i<data.domains.length;i++){
					var isIP = isValidIP(data.domains[i].name);
					var x = isContains(data.domains[i].name, '*');
					if(!isIP && !x){
						opt+='<li style="line-height:26px"><input type="checkbox" style="margin-right:5px; vertical-align:-2px" value="'+data.domains[i].name+'">'+data.domains[i].name+'</li>'
					}
				}
				$("input[name='admin_email']").val(data.email);
				$("#ymlist").html(opt);
				$("#ymlist li input").click(function(e){
					e.stopPropagation();
				})
				$("#ymlist li").click(function(){
					var o = $(this).find("input");
					if(o.prop("checked")){
						o.prop("checked",false)
					}
					else{
						o.prop("checked",true);
					}
				})
				$(".letsApply").click(function(){
					var c = $("#ymlist input[type='checkbox']");
					var str = [];
					var domains = '';
					for(var i=0; i<c.length; i++){
						if(c[i].checked){
							str.push(c[i].value);
						}
					}
					domains = JSON.stringify(str);
					newSSL(siteName,domains);

				})
			},'json');
			break;
		case 'other':
			$(".tab-con").html(other);
			var key = '';
			var csr = '';
			var loadT = layer.msg('Submitting task...',{icon:16,time:0,shade: [0.3, '#000']});
			$.post('site/get_ssl','siteName='+siteName,function(data){
				layer.close(loadT);
				var rdata = data['data'];
				if (rdata.type == 0){
					setCookie('letssl', 1);
				}
				if(rdata.status){
					$(".ssl-btn").append("<button class='btn btn-default btn-sm' onclick=\"ocSSL('close_ssl_conf','"+siteName+"')\" style='margin-left:10px'>Disable SSL</button>");
				}
				if(rdata.key == false) rdata.key = '';
				if(rdata.csr == false) rdata.csr = '';
				$("#key").val(rdata.key);
				$("#csr").val(rdata.csr);
			},'json');
			break;
	}
}


//One-click deployment of certificates
function onekeySSl(partnerOrderId,siteName){
	var loadT = layer.msg(lan.site.ssl_apply_3,{icon:16,time:0,shade:0.3});
	$.post("/ssl?action=GetSSLInfo","partnerOrderId="+partnerOrderId+"&siteName="+siteName,function(zdata){
		layer.close(loadT);
		layer.msg(zdata.msg,{icon:zdata.status?1:2});
		getSSLlist(siteName);
	})
}

//Verify domain name
function verifyDomain(partnerOrderId,siteName){
	var loadT = layer.msg(lan.site.ssl_apply_2,{icon:16,time:0,shade:0.3});
	$.post("/ssl?action=Completed","partnerOrderId="+partnerOrderId+'&siteName='+siteName,function(ydata){
		layer.close(loadT);
		if(!ydata.status){
			layer.msg(ydata.msg,{icon:2});
			return;
		}
		//third step
		var loadT = layer.msg(lan.site.ssl_apply_3,{icon:16,time:0,shade:0.3});
		$.post("/ssl?action=GetSSLInfo","partnerOrderId="+partnerOrderId+"&siteName="+siteName,function(zdata){
			layer.close(loadT);
			if(zdata.status) getSSLlist();
			layer.msg(zdata.msg,{icon:zdata.status?1:2});
		});
	});
}

//Turn SSL on and off
function ocSSL(action,siteName){
	var loadT = layer.msg('Getting certificate list, please wait..',{icon:16,time:0,shade: [0.3, '#000']});
	$.post("/site/"+action,'siteName='+siteName+'&updateOf=1',function(rdata){
		layer.close(loadT)

		if(!rdata.status){
			if(!rdata.out){
				layer.msg(rdata.msg,{icon:rdata.status?1:2});
				setSSL(siteName);
				return;
			}
			data = "<p>Certificate acquisition failed:</p><hr />"
			for(var i=0;i<rdata.out.length;i++){
				data += "<p>Domain name: "+rdata.out[i].Domain+"</p>"
					  + "<p>Error type: "+rdata.out[i].Type+"</p>"
					  + "<p>Details: "+rdata.out[i].Detail+"</p>"
					  + "<hr />";
			}
			layer.msg(data,{icon:2,time:0,shade:0.3,shadeClose:true});
			return;
		}

		setCookie('letssl',0);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		if(action == 'close_ssl_conf'){
			layer.msg('SSL is turned off, please be sure to clear the browser cache before visiting the site!',{icon:1,time:5000});
		}
		$(".tab-nav .on").click();
	},'json');
}

//Generate SSL
function newSSL(siteName,domains){
	var loadT = layer.msg('Verifying domain name, please wait...',{icon:16,time:0,shade: [0.3, '#000']});
	var force = '';
	if($("#checkDomain").prop("checked")) force = '&force=true';
	var email = $("input[name='admin_email']").val();
	$.post('/site/create_let','siteName='+siteName+'&domains='+domains+'&updateOf=1&email='+email + force,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			var mykeyhtml = '<div class="myKeyCon ptb15"><div class="ssl-con-key pull-left mr20">Key (KEY)<br><textarea id="key" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.data.key+'</textarea></div>'
					+ '<div class="ssl-con-key pull-left">Certificate (PEM format)<br><textarea id="csr" class="bt-input-text" readonly="" style="background-color:#f6f6f6">'+rdata.data.csr+'</textarea></div>'
					+ '</div>'
					+ '<ul class="help-info-text c7 pull-left"><li>Let\'s Encrypt free certificate has been automatically generated for you;</li>\
						<li>If you need to use other SSL, please switch other certificates, paste your KEY and PEM content, and then save.</li></ul>';
			$(".btssl").html(mykeyhtml);
			layer.msg(rdata.data.msg,{icon:rdata.status?1:2});
			setCookie('letssl',1);
			return;
		}

		setCookie('letssl',0);
		layer.msg(rdata.msg,{icon:2,area:'500px',time:0,shade:0.3,shadeClose:true});

	},'json');
}

//Save SSL
function saveSSL(siteName){
	var data = 'type=1&siteName='+siteName+'&key='+encodeURIComponent($("#key").val())+'&csr='+encodeURIComponent($("#csr").val());
	var loadT = layer.msg(lan.site.saving_txt,{icon:16,time:20000,shade: [0.3, '#000']})
	$.post('/site/set_ssl',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.msg(rdata.msg,{icon:1});
			$(".ssl-btn").find(".btn-default").remove();
			$(".ssl-btn").append("<button class='btn btn-default btn-sm' onclick=\"ocSSL('close_ssl_conf','"+siteName+"')\" style='margin-left:10px'>"+lan.site.ssl_close+"</button>");
		}else{
			layer.msg(rdata.msg,{icon:2,time:0,shade:0.3,shadeClose:true});
		}
	},'json');
}

//PHP version
function phpVersion(siteName){
	$.post('/site/get_site_php_version','siteName='+siteName,function(version){
		// console.log(version);
		if(version.status === false){
			layer.msg(version.msg,{icon:5});
			return;
		}
		$.post('/site/get_php_version',function(rdata){
			var versionSelect = "<div class='webEdit-box'>\
									<div class='line'>\
										<span class='tname' style='width:100px'>PHP version</span>\
										<div class='info-r'>\
											<select id='phpVersion' class='bt-input-text mr5' name='phpVersion' style='width:110px'>";
			var optionSelect = '';
			for(var i=0;i<rdata.length;i++){
				optionSelect = version.phpversion == rdata[i].version?'selected':'';
				versionSelect += "<option value='"+ rdata[i].version +"' "+ optionSelect +">"+ rdata[i].name +"</option>"
			}
			versionSelect += "</select>\
							<button class='btn btn-success btn-sm' onclick=\"setPHPVersion('"+siteName+"')\">"+lan.site.switch+"</button>\
							</div>\
							<span id='php_w' style='color:red;margin-left: 32px;'></span>\
						</div>\
							<ul class='help-info-text c7 ptb10'>\
							<li>Please select the version according to your program needs</li>\
							<li>If it is not necessary, please try not to use PHP5.2, it will reduce the security of your server;</li>\
							<li>PHP7 does not support the mysql extension, and mysqli and mysql-pdo are installed by default. </li>\
							</ul>\
						</div>\
					</div>";
			$("#webedit-con").html(versionSelect);
			//Verify PHP version
			$("select[name='phpVersion']").change(function(){
				if($(this).val() == '52'){
					var msgerr = 'PHP5.2 has cross-site risk when your site has loopholes, please try to use PHP5.3 or above!';
					$('#php_w').text(msgerr);
				}else{
					$('#php_w').text('');
				}
			})
		},'json');
	},'json');
}


//Set PHP version
function setPHPVersion(siteName){
	var data = 'version='+$("#phpVersion").val()+'&siteName='+siteName;
	var loadT = layer.msg('Saving...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/site/set_php_version',data,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}

//configuration file
function configFile(webSite){
	var info = syncPost('/site/get_host_conf', {siteName:webSite});
	$.post('/files/get_body','path='+info['host'],function(rdata){
		var mBody = "<div class='webEdit-box padding-10'>\
		<textarea style='height: 320px; width: 445px; margin-left: 20px;line-height:18px' id='configBody'>"+rdata.data.data+"</textarea>\
			<div class='info-r'>\
				<button id='SaveConfigFileBtn' class='btn btn-success btn-sm' style='margin-top:15px;'>保存</button>\
				<ul class='help-info-text c7 ptb10'>\
					<li>This is the main configuration file of the site. If you do not understand the configuration rules, please do not modify it at will.</li>\
				</ul>\
			</div>\
		</div>";
		$("#webedit-con").html(mBody);
		var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
			extraKeys: {"Ctrl-Space": "autocomplete"},
			lineNumbers: true,
			matchBrackets:true,
		});
		$(".CodeMirror-scroll").css({"height":"300px","margin":0,"padding":0});
		$("#SaveConfigFileBtn").click(function(){
			$("#configBody").empty();
			$("#configBody").text(editor.getValue());
			saveConfigFile(webSite,rdata.data.encoding, info['host']);
		})
	},'json');
}

//save configuration file
function saveConfigFile(webSite,encoding,path){
	var data = 'encoding='+encoding+'&data='+encodeURIComponent($("#configBody").val())+'&path='+path;
	var loadT = layer.msg('Saving...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/files/save_body',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.msg(rdata.msg,{icon:1});
		}else{
			layer.msg(rdata.msg,{icon:2,time:0,shade:0.3,shadeClose:true});
		}
	},'json');
}

//Rewrite
function rewrite(siteName){
	$.post("/site/get_rewrite_list", 'siteName='+siteName,function(rdata){
		var info = syncPost('/site/get_rewrite_conf', {siteName:siteName});
		var filename = info['rewrite'];
		$.post('/files/get_body','path='+filename,function(fileBody){
			var centent = fileBody['data']['data'];
			var rList = '';
			for(var i=0;i<rdata.rewrite.length;i++){
				if (i==0){
					rList += "<option value='0'>"+rdata.rewrite[i]+"</option>";
				} else {
					rList += "<option value='"+rdata.rewrite[i]+"'>"+rdata.rewrite[i]+"</option>";
				}
			}
			var webBakHtml = "<div class='bt-form'>\
						<div class='line'>\
						<select id='myRewrite' class='bt-input-text mr20' name='rewrite' style='width:30%;'>"+rList+"</select>\
						<textarea class='bt-input-text' style='height: 260px; width: 480px; line-height:18px;margin-top:10px;padding:5px;' id='rewriteBody'>"+centent+"</textarea></div>\
						<button id='SetRewriteBtn' class='btn btn-success btn-sm'>Save</button>\
						<button id='SetRewriteBtnTel' class='btn btn-success btn-sm'>Save as</button>\
						<ul class='help-info-text c7 ptb15'>\
							<li>Please select your application, if the website cannot be accessed normally after setting rewrite ruel, please try to set it back to default</li>\
							<li>You can modify the rewrite rules and save them after modification.</li>\
						</ul>\
						</div>";
			$("#webedit-con").html(webBakHtml);

			var editor = CodeMirror.fromTextArea(document.getElementById("rewriteBody"), {
	            extraKeys: {"Ctrl-Space": "autocomplete"},
				lineNumbers: true,
				matchBrackets:true,
			});

			$(".CodeMirror-scroll").css({"height":"300px","margin":0,"padding":0});
			$("#SetRewriteBtn").click(function(){
				$("#rewriteBody").empty();
				$("#rewriteBody").text(editor.getValue());
				setRewrite(filename);
			});
			$("#SetRewriteBtnTel").click(function(){
				$("#rewriteBody").empty();
				$("#rewriteBody").text(editor.getValue());
				setRewriteTel();
			});

			$("#myRewrite").change(function(){
				var rewriteName = $(this).val();
				if(rewriteName == '0'){
					rpath = filename;
				}else{
					var info = syncPost('/site/get_rewrite_tpl', {tplname:rewriteName});
					if (!info['status']){
						layer.msg(info['msg']);
						return;
					}
					rpath = info['data'];
				}

				$.post('/files/get_body','path='+rpath,function(fileBody){
					$("#rewriteBody").val(fileBody['data']['data']);
					editor.setValue(fileBody['data']['data']);
				},'json');
			});
		},'json');
	},'json');
}


//set reritwe rules
function setRewrite(filename){
	var data = 'data='+encodeURIComponent($("#rewriteBody").val())+'&path='+filename+'&encoding=utf-8';
	var loadT = layer.msg(lan.site.saving_txt,{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/files/save_body',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.msg(rdata.msg,{icon:1});
		}else{
			layer.msg(rdata.msg,{icon:2,time:0,shade:0.3,shadeClose:true});
		}
	},'json');
}
var aindex = null;

//save as template
function setRewriteTel(act){
	if(act != undefined){
		name = $("#rewriteName").val();
		if(name == ''){
			layer.msg(lan.site.template_empty,{icon:5});
			return;
		}
		var data = 'data='+encodeURIComponent($("#rewriteBody").val())+'&name='+name;
		var loadT = layer.msg(lan.site.saving_txt,{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/site?action=SetRewriteTel',data,function(rdata){
			layer.close(loadT);
			layer.close(aindex);

			layer.msg(rdata.msg,{icon:rdata.status?1:5});
		});
		return;
	}

	aindex = layer.open({
		type: 1,
		shift: 5,
		closeBtn: 2,
		area: '320px', //Width Height
		title: 'Save as Rewrite Template',
		content: '<div class="bt-form pd20 pb70">\
					<div class="line">\
						<input type="text" class="bt-input-text" name="rewriteName" id="rewriteName" value="" placeholder="'+lan.site.template_name+'" style="width:100%" />\
					</div>\
					<div class="bt-form-submit-btn">\
					<button type="button" class="btn btn-danger btn-sm">'+lan.public.cancel+'</button>\
					<button type="button" id="rewriteNameBtn" class="btn btn-success btn-sm" onclick="SetRewriteTel(1)">'+lan.public.ok+'</button>\
					</div>\
				</div>'
	});
	$(".btn-danger").click(function(){
		layer.close(aindex);
	});
	$("#rewriteName").focus().keyup(function(e){
		if(e.keyCode == 13) $("#rewriteNameBtn").click();
	});
}
//Modify default page
function siteDefaultPage(){
	stype = getCookie('serverType');
	layer.open({
		type: 1,
		area: '460px',
		title: 'Modify default page',
		closeBtn: 2,
		shift: 0,
		content: '<div class="changeDefault pd20">\
		<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(1)">Default document</button>\
		<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(2)">404 error page</button>\
		<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(3)"Bblank page</button>\
		<button class="btn btn-default btn-sm mg10" style="width:188px" onclick="changeDefault(4)">Default site stop page</button>\
				</div>'
	});
}

function changeDefault(type){
	$.post('/site/get_site_doc','type='+type, function(rdata){
		showMsg('Successful operation!',function(){
			if (rdata.status){
				vhref = rdata.data.path;
				onlineEditFile(0,vhref);
			}
		},{icon:rdata.status?1:2});
	},'json');
}


function getClassType(){
	var select = $('.site_type > select');
	$.post('/site/get_site_types',function(rdata){
		$(select).html('');
		$(select).append('<option value="-1">All Categories</option>');
		for (var i = 0; i<rdata.length; i++) {
			$(select).append('<option value="'+rdata[i]['id']+'">'+rdata[i]['name']+'</option>');
		}

		$(select).bind('change',function(){
			var select_id = $(this).val();
			// console.log(select_id);
			getWeb(1,'',select_id);
		})
	},'json');
}
getClassType();




function setClassType(){
	$.post('/site/get_site_types',function(rdata){
		var list = '';
		for (var i = 0; i<rdata.length; i++) {
			list +='<tr><td>' + rdata[i]['name'] + '</td>\
				<td><a class="btlink edit_type" onclick="editClassType(\''+rdata[i]['id']+'\',\''+rdata[i]['name']+'\')">Edit</a> | <a class="btlink del_type" onclick="removeClassType(\''+rdata[i]['id']+'\',\''+rdata[i]['name']+'\')">Delete</a>\
				</td></tr>';
		}

		layer.open({
			type: 1,
			area: '350px',
			title: 'Website classification management',
			closeBtn: 2,
			shift: 0,
			content: '<div class="bt-form edit_site_type">\
					<div class="divtable mtb15" style="overflow:auto">\
						<div class="line "><div class="info-r  ml0">\
							<input name="type_name" class="bt-input-text mr5 type_name" placeholder="Please fill in the category name" type="text" style="width:50%" value=""><button name="btn_submit" class="btn btn-success btn-sm mr5 ml5 btn_submit" onclick="addClassType();">Add</button></div>\
						</div>\
						<table id="type_table" class="table table-hover" width="100%">\
							<thead><tr><th>Name</th><th width="80px">Action</th></tr></thead>\
							<tbody>'+list+'</tbody>\
						</table>\
					</div>\
				</div>'
		});
	},'json');
}

function addClassType(){
	var name = $("input[name=type_name]").val();
	$.post('/site/add_site_type','name='+name, function(rdata){
		showMsg(rdata.msg,function(){
			if (rdata.status){
				layer.closeAll();
				setClassType();
				getClassType();
			}
		},{icon:rdata.status?1:2});
	},'json');
}

function removeClassType(id,name){
	if (id == 0){
		layer.msg('Kategori default tidak dapat dihapus/diedit!',{icon:2});
		return;
	}
	layer.confirm('Are you sure you want to delete the classification? ',{title: 'Delete category ['+ name +']' }, function(){
		$.post('/site/remove_site_type','id='+id, function(rdata){
			showMsg(rdata.msg,function(){
				if (rdata.status){
					layer.closeAll();
					setClassType();
					getClassType();
				}
			},{icon:rdata.status?1:2});
		},'json');
	});
}

function editClassType(id,name){
	if (id == 0){
		layer.msg('Kategori default tidak dapat dihapus/diedit!',{icon:2});
		return;
	}

	layer.open({
		type: 1,
		area: '350px',
		title: 'Modify classification management【' + name + '】',
		closeBtn: 2,
		shift: 0,
		content: "<form class='bt-form bt-form pd20 pb70' id='mod_pwd'>\
                    <div class='line'>\
                        <span class='tname'>Category Name</span>\
                        <div class='info-r'><input name=\"site_type_mod\" class='bt-input-text mr5' type='text' value='"+name+"' /></div>\
                    </div>\
                    <div class='bt-form-submit-btn'>\
                        <button id='site_type_mod' type='button' class='btn btn-success btn-sm btn-title'>Submit</button>\
                    </div>\
                  </form>"
	});

	$('#site_type_mod').unbind().click(function(){
		var _name = $('input[name=site_type_mod]').val();
		$.post('/site/modify_site_type_name','id='+id+'&name='+_name, function(rdata){
			showMsg(rdata.msg,function(){
				if (rdata.status){
					layer.closeAll();
					setClassType();
					getClassType();
				}
			},{icon:rdata.status?1:2});
		},'json');

	});
}


function moveClassTYpe(){
	$.post('/site/get_site_types',function(rdata){
		var option = '';
		for (var i = 0; i<rdata.length; i++) {
			option +='<option value="'+rdata[i]['id']+'">'+rdata[i]['name']+'</option>';
		}

		layer.open({
			type: 1,
			area: '350px',
			title: 'Set site classification',
			closeBtn: 2,
			shift: 0,
			content: '<div class="bt-form edit_site_type">\
					<div class="divtable mtb15" style="overflow:auto;height:80px;">\
						<div class="line"><span class="tname">Default site</span>\
							<div class="info-r">\
							<select class="bt-input-text mr5" name="type_id" style="width:200px">'+option+'\
							</select>\
							</div>\
						</div>\
					</div>\
					<div class="bt-form-submit-btn"><button onclick="setSizeClassType();" type="button" class="btn btn-sm btn-success">Submit</button></div>\
				</div>'
		});
	},'json');
}


function setSizeClassType(){
	var data = {};
	data['id'] = $('select[name=type_id]').val();
	var ids = [];
    $('table').find('td').find('input').each(function(i,obj){
        checked = $(this).prop('checked');
        if (checked) {
        	ids.push($(this).val());
        }
    });
	data['site_ids'] = JSON.stringify(ids);
	$.post('/site/set_site_type',data, function(rdata){
		showMsg(rdata.msg,function(){
			if (rdata.status){
				layer.closeAll();
			}
		},{icon:rdata.status?1:2});
	},'json');
}
