
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
};

$.post = function(url, args, callback, dataType) {
    if(! dataType)
        dataType = "json";

    if(typeof args == "object"){
        args._xsrf = getCookie("_xsrf");
        data = $.param(args);
    } else{
        data = args;
    }

    $.ajax({
        url: url,
        data: data,
        dataType: dataType,
        type: "POST",
        success: function(response) {
            callback(response);
        }
    });
};

function Timer(seconds, eid, func){

	this.seconds = seconds;
    this.elementId = eid;
    this.func = func;

    this.start = function(){
        that.countDown();
        that.timer = setInterval(that.countDown, 1000);
    };

    this.timeout = function(){
        if(that.func)
            that.func();
    };

    var that = this;
    this.countDown = function(){
        $("#"+that.elementId+" span.countdown").html(that.seconds);
        if(that.seconds == 0){
            that.stop();
            that.timeout();
        } else {
            that.seconds--;
        }
    };

    this.stop = function(){
        clearInterval(that.timer);
    };

    this.set = function(seconds){
        that.stop();
        that.seconds = seconds;
        that.start();
    };

    this.hide = function(){
        $("#"+that.elementId).hide();
    };

    this.show = function(){
        $("#"+that.elementId).show();
    };

    this.close = function(){
    	that.stop();
    	that.hide();
    };
}