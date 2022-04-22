//Reset plugin popover width
function resetPluginWinWidth(width){
    $("div[id^='layui-layer'][class*='layui-layer-page']").width(width);
}

//Software management window
function softMain(name, version) {
    var loadT = layer.msg("Processing, please wait...", { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.get('/plugins/setting?name='+name, function(rdata) {
        layer.close(loadT);
        layer.open({
            type: 1,
            area: '1000px',
            title: name + '-' + version + "manage",
            closeBtn: 2,
            shift: 0,
            content: rdata
        });
        $(".bt-w-menu p").click(function() {
            $(this).addClass("bgw").siblings().removeClass("bgw");
        });

        //version to
        $(".plugin_version").attr('version',version).hide();
    });
}

//Get the software list
function getSList(isdisplay) {
    if (isdisplay !== true) {
        var loadT = layer.msg('Fetching list...', { icon: 16, time: 0, shade: [0.3, '#000'] })
    }
    if (!isdisplay || isdisplay === true)
        isdisplay = getCookie('p' + getCookie('softType'));
    if (isdisplay == true || isdisplay == 'true') isdisplay = 1;

    var search = $("#SearchValue").val();
    if (search != '') {
        search = '&search=' + search;
    }
    var type = '';
    var istype = getCookie('softType');
    if (istype == 'undefined' || istype == 'null' || !istype) {
        istype = '0';
    }

    type = '&type=' + istype;
    var page = '';
    if (isdisplay) {
        page = '&p=' + isdisplay;
        setCookie('p' + getCookie('softType'), isdisplay);
    }

    var condition = (search + type + page).slice(1);
    $.get('/plugins/list?' + condition, '', function(rdata) {
        layer.close(loadT);
        var tBody = '';
        var sBody = '';
        var pBody = '';

        for (var i = 0; i < rdata.type.length; i++) {
            var c = '';
            if (istype == rdata.type[i].type) {
                c = 'class="on"';
            }
            tBody += '<span typeid="' + rdata.type[i].type + '" ' + c + '>' + rdata.type[i].title + '</span>';
        }

        $(".softtype").html(tBody);
        $("#softPage").html(rdata.list);
        $("#softPage .Pcount").css({ "position": "absolute", "left": "0" })

        $(".task").text(rdata.data[rdata.length - 1]);
        for (var i = 0; i < rdata.data.length; i++) {
            var plugin = rdata.data[i];
            var len = plugin.versions.length;
            var version_info = '';
            var version = '';
            var softPath = '';
            var titleClick = '';
            var state = '';
            var indexshow = '';
            var checked = '';

            checked = plugin.display ? 'checked' : '';

            if (typeof plugin.versions == "string"){
                version_info += plugin.versions + '|';
            } else {
                for (var j = 0; j < len; j++) {
                    version_info += plugin.versions[j] + '|';
                }
            }
            if (version_info != '') {
                version_info = version_info.substring(0, version_info.length - 1);
            }


            var handle = '<a class="btlink" onclick="addVersion(\'' + plugin.name + '\',\'' + version_info + '\',\'' + plugin.tip + '\',this,\'' + plugin.title + '\')">Install</a>';


            if (plugin.setup == true) {

                var mupdate = '';//(plugin.versions[n] == plugin.updates[n]) '' : '<a class="btlink" onclick="SoftUpdate(\'' + plugin.name + '\',\'' + plugin.versions[n].version + '\',\'' + plugin.updates[n] + '\')">Renew</a> | ';
                // if (plugin.versions[n] == '') mupdate = '';
                handle = mupdate + '<a class="btlink" onclick="softMain(\'' + plugin.name + '\',\'' + plugin.setup_version + '\')">Setting</a> | <a class="btlink" onclick="uninstallVersion(\'' + plugin.name + '\',\'' + plugin.setup_version + '\')">Uninstall</a>';
                titleClick = 'onclick="softMain(\'' + plugin.name + '\',\'' + version_info + '\')" style="cursor:pointer"';

                softPath = '<span class="glyphicon glyphicon-folder-open" title="' + plugin.path + '" onclick="openPath(\'' + plugin.path + '\')"></span>';
                if (plugin.coexist){
                    indexshow = '<div class="index-item"><input class="btswitch btswitch-ios" id="index_' + plugin.name  + plugin.versions + '" type="checkbox" ' + checked + '><label class="btswitch-btn" for="index_' + plugin.name + plugin.versions + '" onclick="toIndexDisplay(\'' + plugin.name + '\',\'' + plugin.versions + '\',\'' + plugin.coexist +'\')"></label></div>';
                } else {
                    indexshow = '<div class="index-item"><input class="btswitch btswitch-ios" id="index_' + plugin.name + '" type="checkbox" ' + checked + '><label class="btswitch-btn" for="index_' + plugin.name + '" onclick="toIndexDisplay(\'' + plugin.name + '\',\'' + plugin.setup_version + '\')"></label></div>';
                }

                if (plugin.status == true) {
                    state = '<span style="color:#20a53a" class="glyphicon glyphicon-play"></span>'
                } else {
                    state = '<span style="color:red" class="glyphicon glyphicon-pause"></span>'
                }
            }

            if (plugin.task == '-2') {
                handle = '<a style="color:green;" href="javascript:task();">Uninstalling...</a>';
            } else if (plugin.task == '-1') {
                handle = '<a style="color:green;" href="javascript:task();">Installing...</a>';
            } else if (plugin.task == '0') {
                handle = '<a style="color:#C0C0C0;" href="javascript:task();">Waiting...</a>';
            }

            var plugin_title = plugin.title;
            if (plugin.setup && !plugin.coexist){
                plugin_title = plugin.title + ' ' + plugin.setup_version;
            }


            sBody += '<tr>' +
                '<td>' + plugin_title + '</td>' +
                '<td class="visible-lg visible-md visible-sm">' + plugin.ps + '</td>' +
                //'<td>' + softPath + '</td>' +
                '<td>' + state + '</td>' +
                //'<td>' + indexshow + '</td>' +
                '<td style="text-align: right;">' + handle + '</td>' +
                '</tr>';

            // sBody += '<tr>' +
            //     '<td><span ' + titleClick +
            //     '><img onclick="asyncLoadImage(this,\'/plugins/file?name='+plugin.name+'&f=ico.png\')"src="/plugins/file?name=' + plugin.name +
            //     '&f=ico.png' + '">' + plugin_title + '</span></td>' +
            //     '<td>' + plugin.ps + '</td>' +
            //     '<td>' + softPath + '</td>' +
            //     '<td>' + state + '</td>' +
            //     '<td>' + indexshow + '</td>' +
            //     '<td style="text-align: right;">' + handle + '</td>' +
            //     '</tr>';
        }

        sBody += pBody;
        $("#softList").html(sBody);
        $(".menu-sub span").click(function() {
            setCookie('softType', $(this).attr('typeid'));
            $(this).addClass("on").siblings().removeClass("on");
            getSList();
        });

        loadImage();
    },'json');
}

function addVersion(name, ver, type, obj, title) {
    var option = '';
    var titlename = name;
    if (ver.indexOf('|') >= 0){
        var veropt = ver.split("|");
        var SelectVersion = '';
        for (var i = 0; i < veropt.length; i++) {
            SelectVersion += '<option>' + name + ' ' + veropt[i] + '</option>';
        }
        option = "<select id='SelectVersion' class='bt-input-text' style='margin-left:30px'>" + SelectVersion + "</select>";
    } else {
        option = '<span id="SelectVersion">' + name + ' ' + ver + '</span>';
    }

    layer.open({
        type: 1,
        title: titlename + "Software Installation",
        area: '350px',
        closeBtn: 2,
        shadeClose: true,
        content: "<div class='bt-form pd20 pb70 c6'>\
			<div class='version line'>Installed version：" + option + "</div>\
	    	<div class='bt-form-submit-btn'>\
				<button type='button' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>Close</button>\
		        <button type='button' id='bi-btn' class='btn btn-success btn-sm btn-title bi-btn'>Submit</button>\
	        </div>\
	    </div>"
    });

    $('.fangshi input').click(function() {
        $(this).attr('checked', 'checked').parent().siblings().find("input").removeAttr('checked');
    });
    $("#bi-btn").click(function() {

        var info = $("#SelectVersion").val().toLowerCase();
        if (info == ''){
            info = $("#SelectVersion").text().toLowerCase();
        }
        var name = info.split(" ")[0];
        var version = info.split(" ")[1];
        var type = $('.fangshi input').prop("checked") ? '1' : '0';
        var data = "name=" + name + "&version=" + version + "&type=" + type;

        var loadT = layer.msg('Adding to installer...', { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post("/plugins/install", data, function(rdata) {
            layer.closeAll();
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
            getSList();
        },'json');
    });
    installTips();
    fly("bi-btn");
}

//Uninstall software
function uninstallVersion(name, version) {
    layer.confirm(msgTpl('You really want to uninstall [{1}-{2}]?', [name, version]), { icon: 3, closeBtn: 2 }, function() {
        var data = 'name=' + name + '&version=' + version;
        var loadT = layer.msg('Processing, please wait...', { icon: 16, time: 0, shade: [0.3, '#000'] });
        $.post('/plugins/uninstall', data, function(rdata) {
            layer.close(loadT)
            getSList();
            layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
        },'json');
    });
}


//Home display
function toIndexDisplay(name, version, coexist) {

    var status = $("#index_" + name).prop("checked") ? "0" : "1";
    if (coexist == "true") {
        var verinfo = version.replace(/\./, "");
        status = $("#index_" + name + verinfo).prop("checked") ? "0" : "1";
    }

    var data = "name=" + name + "&status=" + status + "&version=" + version;
    $.post("/plugins/set_index", data, function(rdata) {
        if (rdata.status) {
            layer.msg(rdata.msg, { icon: 1 })
        } else {
            layer.msg(rdata.msg, { icon: 2 })
        }
    },'json');
}

function indexListHtml(callback){
    var loadT = layer.msg('Fetching list...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.get('/plugins/index_list', function(rdata) {
        layer.close(loadT);
        $("#indexsoft").html('');
        var con = '';
        for (var i = 0; i < rdata.length; i++) {
            var plugin = rdata[i];
            var len = plugin.versions.length;
            var version_info = '';

            if (typeof plugin.versions == "string"){
                version_info += plugin.versions + '|';
            } else {
                for (var j = 0; j < len; j++) {
                    version_info += plugin.versions[j] + '|';
                }
            }
            if (version_info != '') {
                version_info = version_info.substring(0, version_info.length - 1);
            }

            if (plugin.status == true) {
                    state = '<span style="color:#20a53a" class="glyphicon glyphicon-play"></span>'
                } else {
                    state = '<span style="color:red" class="glyphicon glyphicon-pause"></span>'
            }

            var name = plugin.title + ' ' + plugin.setup_version + '  ';
            var data_id = plugin.name + '-' + plugin.setup_version;
            if (plugin.coexist){
                name = plugin.title + '  ';
                data_id = plugin.name + '-' + plugin.versions;
            }

            // con += '<div class="col-sm-3 col-md-3 col-lg-3" data-id="' + data_id + '">\
            //     <span class="spanmove"></span>\
            //     <div onclick="softMain(\'' + plugin.name + '\',\'' + plugin.setup_version + '\')">\
            //     <div class="image"><img src="/static/img/loading.gif" data-src="/plugins/file?name=' + plugin.name + '&f=ico.png"></div>\
            //     <div class="sname">' +  name + state + '</div>\
            //     </div>\
            // </div>';

            con += '<div class="col-sm-3 col-md-3 col-lg-3" data-id="' + data_id + '">\
                <span class="spanmove"></span>\
                <div onclick="softMain(\'' + plugin.name + '\',\'' + plugin.setup_version + '\')">\
                <div class="image"><img src="/plugins/file?name=' + plugin.name + '&f=ico.png"></div>\
                <div class="sname">' +  name + state + '</div>\
                </div>\
            </div>';

            // loadImage();
        }

        $("#indexsoft").html(con);
        //software location move
        var softboxlen = $("#indexsoft > div").length;
        var softboxsum = 12;
        var softboxcon = '';
        var softboxn = softboxlen;
        if (softboxlen <= softboxsum) {
            for (var i = 0; i < softboxsum - softboxlen; i++) {
                // softboxn += 1000;
                softboxcon += '<div class="col-sm-3 col-md-3 col-lg-3 no-bg" data-id=""></div>';
            }
            $("#indexsoft").append(softboxcon);
        }

        if (typeof callback=='function'){
            callback();
        }
    },'json');
}


//Home software list
function indexSoft() {
    indexListHtml(function(){
        $("#indexsoft").dragsort({ dragSelector: ".spanmove", dragBetween: true, dragEnd: saveOrder, placeHolderTemplate: "<div class='col-sm-3 col-md-3 col-lg-3 dashed-border'></div>" });
    });

    function saveOrder() {
        var data = $("#indexsoft > div").map(function() { return $(this).attr("data-id"); }).get();
        tmp = [];
        for(i in data){
            // console.log(data[i]);
            if (data[i] != ''){
                tmp.push($.trim(data[i]));
            }
        }
        var ssort = tmp.join("|");
        $("input[name=list1SortOrder]").val(ssort);
        $.post("/plugins/index_sort", 'ssort=' + ssort, function(rdata) {
            if (!rdata.status){
                showMsg('Setup failed:'+ rdata.msg, function(){
                    indexListHtml();
                }, { icon: 16, time: 0, shade: [0.3, '#000'] });
            }
        },'json');
    };
}


function importPluginOpen(){
    $("#update_zip").on("change", function () {
        var files = $("#update_zip")[0].files;
        if (files.length == 0) {
            return;
        }
        importPlugin(files[0]);
        $("#update_zip").val('')
    });
    $("#update_zip").click();
}


function importPlugin(file){
    var formData = new FormData();
    formData.append("plugin_zip", file);
    $.ajax({
        url: "/plugins/update_zip",
        type: "POST",
        data: formData,
        processData: false,
        dataType:'json',
        contentType: false,
        success: function (data) {
            if (data.status === false) {
                layer.msg(data.msg, { icon: 2 });
                return;
            }
            var loadT = layer.open({
                type: 1,
                area: "500px",
                title: "Install third-party plugin packages",
                closeBtn: 2,
                shift: 5,
                shadeClose: false,
                content: '<style>\
                    .install_three_plugin{padding:25px;padding-bottom:70px}\
                    .plugin_user_info p { font-size: 14px;}\
                    .plugin_user_info {padding: 15px 30px;line-height: 26px;background: #f5f6fa;border-radius: 5px;border: 1px solid #efefef;}\
                    .btn-content{text-align: center;margin-top: 25px;}\
                </style>\
                <div class="bt-form c7  install_three_plugin pb70">\
                    <div class="plugin_user_info">\
                        <p><b>Name：</b>'+ data.title + '</p>\
                        <p><b>Version：</b>' + data.versions +'</p>\
                        <p><b>Describe：</b>' + data.ps + '</p>\
                        <p><b>Size：</b>' + toSize(data.size) + '</p>\
                        <p><b>Author：</b>' + data.author + '</p>\
                        <p><b>Source：</b><a class="btlink" href="'+data.home+'" target="_blank">' + data.home + '</a></p>\
                    </div>\
                    <ul class="help-info-text c7">\
                        <li style="color:red;">This is a plugin developed by a third party，unable to verify its reliability!</li>\
                        <li>The installation process may take a few minutes, please be patient!</li>\
                        <li>If this plugin already exists, it will be replaced!</li>\
                    </ul>\
                    <div class="bt-form-submit-btn"><button type="button" class="btn btn-sm btn-danger mr5" onclick="layer.closeAll()">Cancel</button><button type="button" class="btn btn-sm btn-success" onclick="importPluginInstall(\''+ data.name + '\',\'' + data.tmp_path +'\')">OK to install</button></div>\
                </div>'
            });

        },error: function (responseStr) {
            layer.msg('Upload failed 2!:' + responseStr, { icon: 2 });
        }
    });
}


function importPluginInstall(plugin_name, tmp_path) {
    layer.msg('Installing, this may take a few minutes...', { icon: 16, time: 0, shade: [0.3, '#000'] });
    $.post('/plugins/input_zip', { plugin_name: plugin_name, tmp_path: tmp_path }, function (rdata) {
        layer.closeAll()
        if (rdata.status) {
            getSList(true);
        }
        setTimeout(function () { layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 }) }, 1000);
    },'json');
}

$(function() {
    if (window.document.location.pathname == '/soft/') {
        setInterval(function() { getSList(); }, 8000);
    }
});
