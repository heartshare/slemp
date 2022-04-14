
// $.post('/config/get','',function(rdata){
// 	console.log(rdata);
// },'json');


$(".set-submit").click(function(){
	var data = $("#set_config").serialize();
	layer.msg('Saving configuration...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/set',data,function(rdata){
		layer.closeAll();
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		if(rdata.status){
			setTimeout(function(){
				window.location.href = ((window.location.protocol.indexOf('https') != -1)?'https://':'http://') + rdata.data.host + window.location.pathname;
			},2500);
		}
	},'json');
});


//close panel
function closePanel(){
	layer.confirm('Closing the panel will cause you to lose access to the panel, do you really want to close the SLEMP Panel?',{title:'Close panel',closeBtn:2,icon:13,cancel:function(){
		$("#closePl").prop("checked",false);
	}}, function() {
		$.post('/config/close_panel','',function(rdata){
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
			setTimeout(function(){window.location.reload();},1000);
		},'json');
	},function(){
		$("#closePl").prop("checked",false);
	});
}


function modifyAuthPath() {
    var auth_path = $("#admin_path").val();
    btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'b')\">Yes</button>";
    layer.open({
        type: 1,
        area: "500px",
        title: "Modify security entry",
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: '<div class="bt-form bt-form pd20 pb70">\
                    <div class="line ">\
                        <span class="tname">Entry address</span>\
                        <div class="info-r">\
                            <input name="auth_path_set" class="bt-input-text mr5" type="text" style="width: 311px" value="'+ auth_path+'">\
                        </div></div>\
                        <div class="bt-form-submit-btn">\
                            <button type="button" class= "btn btn-sm btn-danger" onclick="layer.closeAll()">Close</button>\
                            <button type="button" class="btn btn-sm btn-success" onclick="setAuthPath();">Submit</button>\
                    </div></div>'
    });
}

function setAuthPath() {
    var auth_path = $("input[name='auth_path_set']").val();
    var loadT = layer.msg(lan.config.config_save, { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config/set_admin_path', { admin_path: auth_path }, function (rdata) {
        layer.close(loadT);
        if (rdata.status) {
            layer.closeAll();
            $("#admin_path").val(auth_path);
        }
        setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 }); }, 200);
    },'json');
}

function setPassword(a) {
	if(a == 1) {
		p1 = $("#p1").val();
		p2 = $("#p2").val();
		if(p1 == "" || p1.length < 8) {
			layer.msg('The panel password cannot be less than 8 digits!', {icon: 2});
			return
		}

		//Prepare weak password match elements
		var checks = ['admin888','123123123','12345678','45678910','87654321','asdfghjkl','password','qwerqwer'];
		pchecks = 'abcdefghijklmnopqrstuvwxyz1234567890';
		for(var i=0;i<pchecks.length;i++){
			checks.push(pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]);
		}

		//Check for weak passwords
		cps = p1.toLowerCase();
		var isError = "";
		for(var i=0;i<checks.length;i++){
			if(cps == checks[i]){
				isError += '['+checks[i]+'] ';
			}
		}

		if(isError != ""){
			layer.msg('Panel password cannot be a weak password '+isError,{icon:5});
			return;
		}

		if(p1 != p2) {
			layer.msg('The two entered passwords do not match', {icon: 2});
			return;
		}
		$.post("/config/set_password", "password1=" + encodeURIComponent(p1) + "&password2=" + encodeURIComponent(p2), function(b) {
			if(b.status) {
				layer.closeAll();
				layer.msg(b.msg, {icon: 1});
			} else {
				layer.msg(b.msg, {icon: 2});
			}
		},'json');
		return;
	}
	layer.open({
		type: 1,
		area: "290px",
		title: 'Change Password',
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content: "<div class='bt-form pd20 pb70'>\
				<div class='line'>\
					<span class='tname'>Password</span>\
					<div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='New password' style='width:100%'/></div>\
				</div>\
				<div class='line'>\
					<span class='tname'>Re-Password</span>\
					<div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='Repeat Password' style='width:100%' /></div>\
				</div>\
				<div class='bt-form-submit-btn'>\
					<span style='float: left;' title='Sandom code' class='btn btn-default btn-sm' onclick='randPwd(10)'>Random</span>\
					<button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">Close</button>\
					<button type='button' class='btn btn-success btn-sm' onclick=\"setPassword(1)\">Submit</button>\
				</div>\
			</div>"
	});
}


function randPwd(){
	var pwd = randomStrPwd(12);
	$("#p1").val(pwd);
	$("#p2").val(pwd);
	layer.msg(lan.bt.pass_rep_ps,{time:2000})
}

function setUserName(a) {
	if(a == 1) {
		p1 = $("#p1").val();
		p2 = $("#p2").val();
		if(p1 == "" || p1.length < 3) {
			layer.msg('Username must be at least 3 characters long', {icon: 2});
			return;
		}
		if(p1 != p2) {
			layer.msg('The username entered twice does not match', {icon: 2});
			return;
		}
		$.post("/config/set_name", "name1=" + encodeURIComponent(p1) + "&name2=" + encodeURIComponent(p2), function(b) {
			if(b.status) {
				layer.closeAll();
				layer.msg(b.msg, {icon: 1});
				$("input[name='username_']").val(p1)
			} else {
				layer.msg(b.msg, {icon: 2});
			}
		},'json');
		return
	}
	layer.open({
		type: 1,
		area: "290px",
		title: 'Modify panel username',
		closeBtn: 2,
		shift: 5,
		shadeClose: false,
		content: "<div class='bt-form pd20 pb70'>\
			<div class='line'><span class='tname'>Username</span>\
				<div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='New username' style='width:100%'/></div>\
			</div>\
			<div class='line'>\
				<span class='tname'>Re-Username</span>\
				<div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='Repear username' style='width:100%'/></div>\
			</div>\
			<div class='bt-form-submit-btn'>\
				<button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">Close</button>\
				<button type='button' class='btn btn-success btn-sm' onclick=\"setUserName(1)\">Submit</button>\
			</div>\
		</div>"
	})
}


function syncDate(){
	var loadT = layer.msg('Synchronizing time...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/sync_date','',function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
		setTimeout(function(){window.location.reload();},1500);
	},'json');
}


function setIPv6() {
    var loadT = layer.msg('Configuring, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/config/set_ipv6_status', {}, function (rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, {icon:rdata.status?1:2});
        setTimeout(function(){window.location.reload();},1500);
    },'json');
}


//Setup Panel SSL
function setPanelSSL(){
	var status = $("#sshswitch").prop("checked")==true?1:0;
	var msg = $("#panelSSL").attr('checked')?'After disabling SSL, the panel must be accessed using the http protocol, continue?':'<a style="font-weight: bolder;font-size: 16px;">Danger! Don\'t turn on this feature if you don\'t understand it!</a>\
	<li style="margin-top: 12px;color:red;">You must use and understand this feature before deciding whether to enable it!</li>\
	<li>Panel SSL is a self-signed certificate and is not trusted by browsers. It is normal to display insecure</li>\
	<li>After opening, the panel cannot be accessed. You can click the link below for the solution.</li>\
	<p style="margin-top: 10px;">\
		<input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: 3px 5px 0px;" for="checkSSL">Know the details and be willing to take risks</label>\
		<a target="_blank" class="btlink" href="http://slemp.basoro.id/docs/remove-ssl" style="float: right;">Learn more</a>\
	</p>';
	layer.confirm(msg,{title:'Setup Panel SSL',closeBtn:2,icon:3,area:'550px',cancel:function(){
		if(status == 0){
			$("#panelSSL").prop("checked",false);
		}
		else{
			$("#panelSSL").prop("checked",true);
		}
	}},function(){
		if(window.location.protocol.indexOf('https') == -1){
			if(!$("#checkSSL").prop('checked')){
				layer.msg(lan.config.ssl_ps,{icon:2});
				return false;
			}
		}
		var loadT = layer.msg('Installing and setting up the SSL components, this will take a few minutes...',{icon:16,time:0,shade: [0.3, '#000']});
		$.post('/config/set_panel_ssl','',function(rdata){
			layer.close(loadT);
			layer.msg(rdata.msg,{icon:rdata.status?1:5});
			if(rdata.status === true){
				$.post('/system/restart','',function (rdata) {
                    layer.close(loadT);
                    layer.msg(rdata.msg);
                    setTimeout(function(){
						window.location.href = ((window.location.protocol.indexOf('https') != -1)?'http://':'https://') + window.location.host + window.location.pathname;
					},3000);
                },'json');
			}
		},'json');
	},function(){
		if(status == 0){
			$("#panelSSL").prop("checked",false);
		}
		else{
			$("#panelSSL").prop("checked",true);
		}
	});
}


function getPanelSSL(){
	var loadT = layer.msg('Getting certificate information...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/get_panel_ssl',{},function(cert){
		layer.close(loadT);
		var certBody = '<div class="tab-con">\
			<div class="myKeyCon ptb15">\
				<div class="ssl-con-key pull-left mr20">SSL Key (KEY)<br>\
					<textarea id="key" class="bt-input-text">'+cert.privateKey+'</textarea>\
				</div>\
				<div class="ssl-con-key pull-left">Certificate(PEM Format)<br>\
					<textarea id="csr" class="bt-input-text">'+cert.certPem+'</textarea>\
				</div>\
				<div class="ssl-btn pull-left mtb15" style="width:100%">\
					<button class="btn btn-success btn-sm" onclick="savePanelSSL()">Save</button>\
				</div>\
			</div>\
			<ul class="help-info-text c7 pull-left">\
				<li>Paste your *.key and *.pem content and save it <a href="http://slemp.basoro.id/docs/ssl-other" class="btlink" target="_blank">[Help]</a>。</li>\
				<li>If the browser prompts that the certificate chain is incomplete, please check whether the PEM certificate is correctly spliced</li><li>PEM format certificate = domain name certificate.crt + root certificate (root_bundle).crt</li>\
			</ul>\
		</div>'
		layer.open({
			type: 1,
			area: "600px",
			title: 'Custom Panel Certificate',
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content:certBody
		});
	},'json');
}


function savePanelSSL(){
	var data = {
		privateKey:$("#key").val(),
		certPem:$("#csr").val()
	}
	var loadT = layer.msg('Installing and setting up the SSL components, this will take a few minutes...',{icon:16,time:0,shade: [0.3, '#000']});
	$.post('/config/save_panel_ssl',data,function(rdata){
		layer.close(loadT);
		if(rdata.status){
			layer.closeAll();
		}
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	},'json');
}
