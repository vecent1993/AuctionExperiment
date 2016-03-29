function sideInfo(text){
    if(text == "")
        $(".sidebar .alert").hide();
    else
        $(".sidebar .alert").show();
    $(".sidebar .alert").removeClass("alert-warning");
    $(".sidebar .alert").addClass("alert-info");
    $(".sidebar .alert").html(text);
}

function sideWarn(text){
    if(text == "")
        $(".sidebar .alert").hide();
    else
        $(".sidebar .alert").show();
    $(".sidebar .alert").removeClass("alert-info");
    $(".sidebar .alert").addClass("alert-warning");
    $(".sidebar .alert").html(text);
}

function WS(url){
    this.url = url;
    this._ws = new WebSocket(url);
    var that = this;
    this.waitForConnection = function(callback, interval) {
        if (that._ws.readyState === 1) {
            callback();
        } else {
            setTimeout(function () {
                that.waitForConnection(callback, interval);
            }, interval);
        }
    };
    this.sendCmd = function(cmd, data, callback){
        that.waitForConnection(function (){
            that._ws.send( JSON.stringify({cmd: cmd, data: data}) );
            if (typeof callback !== 'undefined')
                callback();
        }, 5);
    };
    this._ws.onmessage = function (evt) {
        msg = JSON.parse(evt.data);
        if( that[msg.cmd] ){
            that[msg.cmd](msg.data, evt);
        }
    };
    this.replace = function(data, evt){
        sideInfo("");
        $("#main").html(data);
    };

    this.refresh = function(data, evt) {
        that.sendCmd('get');
    };

    this.redirect = function(data, evt){
        document.location.href = data;
    };

    this.error = function(data, evt){
        var errorDIV = $(".error").clone(true);
        errorDIV.find(".error-detail").html(data);
        $("#main").html("");
        $("#main").append(errorDIV);
        errorDIV.show();
    }
}