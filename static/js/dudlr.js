/*
 * dudlr.js
 *
 * Functions for capturing and recording modifications to a canvas element,
 * to enable a scratchpad UI for recording doodles.
 *
 * author: Drew Smathers <drew dot smathers at gmail dot com>
 */

(function($) {
    if (typeof(console) == 'undefined' || !console) {
        console = {
            log : function () {},
            debug : function () {},
            warn : function () {},
            error : function () {}};
    }

    var DudlrCanvas = function(domelement) {
        console.log("Initalizing DudlrCanvas ... " + domelement);
        return this.__init__(domelement);
    };

    var noop = function () {};


    DudlrCanvas.prototype = {
        __init__: function(domelement) {
            var o = this;
            console.log("__init__ called : " + domelement);
            this.mousex = this.mousey = 0;
            this.lastx = this.lasty = -1;
            this.id = null;
            this._handler = noop;
            //this.cvs_elm = $("#" + getopt(opts, "canvas_id", "canevaz"));
            this.recorder = new DudlrStrokeRecorder();
            this.cvs_elm = $(domelement);
            this.ctx = this.cvs_elm[0].getContext('2d');
            this.ctx.fillStyle = "rgba(255,255,255,1)";
            this.ctx.fillRect(0, 0, this.cvs_elm[0].width, this.cvs_elm[0].height);
            this.ctx.fillStyle = "rgba(0,0,0,0.5)";
            this.widget = new PenWidget(this, {});
            this.setUpWidget(this.widget);
            $().mousemove(function(e){o._trackMouse(e)});
            var ctx  = this.ctx;
        },

        _trackMouse: function(e) {
            this.mousex = e.pageX - this.cvs_elm.offset().left;
            this.mousey = e.pageY - this.cvs_elm.offset().top;
            this.lastx = this.mousex;
            this.lasty = this.mousey;
        },

        save: function(upload, format) {
            var fmt = format
            var w = this.cvs_elm[0].width;
            var h = this.cvs_elm[0].height;
            var pixels = this.ctx.getImageData(0,0,w,h).data;
            if (!fmt) {
                fmt = 'L';
            }
            var fs = {
                L: this._savePixelData_L 
            };
            fs[format](upload, format, pixels, w, h);
        },

        _savePixelData_L: function(upload, format, pixels, w, h) {
            var data = [];
            for (var i = 0; i < (w * h * 4); i++) {
                if (i % 4 == 0) {
                    data.push(pixels[i]);
                }
            }
            upload(format, data, w, h);
        },

        setUpWidget: function(widget) {

            var close = function (widget, f) {
                return function(e) { widget[f](e) };
            };

            widget.init();
            var events = [ "mousemove", "mousedown", "mouseup", "keydown", "keyup" ];
            for (var i = 0; i < events.length; i++) {
                if (typeof(widget[events[i]]) == 'function') {
                    $().bind(events[i], close(widget, events[i]));
                }
            }
        },

        tearDownWidget: function(widget) {
            widget.destroy();
            var events = [ "mousemove", "mousedown", "mouseup", "keydown", "keyup" ];
            for (var i = 0; i < events.length; i++) {
                if (typeof(widget[events[i]]) == 'function') {
                    $().unbind(events[i], widget[events[i]]);
                }
            }
        }
        
    };

    var FILL_MODES = [
        'none',
        'rgba(0,0,0,0.5)',
        'rgba(0,0,0,1)',
        'rgba(255,255,255,0.5)',
        'rgba(255,255,255,1)'
    ];

    var PenWidget = function(cvs, opts) {
        this.__init__(cvs, opts);
    };

    PenWidget.prototype = {
        __init__: function(cvs, opts) {
            this.opts = opts;
            this.cvs = cvs;
            this.active = false;
            this.fillmode = 0;
            this.fillmodes = [
                'none',
                'rgba(0,0,0,0.5)',
                'rgba(0,0,0,1)',
                'rgba(255,255,255,0.5)',
                'rgba(255,255,255,1)'
            ];
            this.fillmodeLabels = [
                'none', 'black (50% transparent)', 'black', 
                'white (50% transparent)', 'white'
                ];
            this.robot = null;
        },

        init: function() {
            var o =  this;
            this.startx = this.starty = 0;
        },

        mousedown: function(e) {
            var cvs = this.cvs;
            var ctx = cvs.ctx;
            ctx.beginPath();
            var x = cvs.mousex;// - cvs.offx;
            var y = cvs.mousey;// - cvs.offy;
            this.startx = x;
            this.starty = y;
            ctx.moveTo(x, y);
            ctx.lineTo(x+1, y+1);
            ctx.stroke();
            this.cvs.recorder.moveTo(x, y);
            this.active = true;
        },

        keyup: function(e) {
            if (e.keyCode == 70) {
                this.fillmode += 1;
                this.fillmode = this.fillmode % this.fillmodes.length;
                this.cvs.recorder.fillStyle(this.fillmode);
                console.log('fill mode : ' + this.fillmode);
                // XXX - need to make callback
                $('#fill-mode').text(this.fillmodeLabels[this.fillmode]);
                if (this.fillmode) {
                    console.log('setting fillstyle to : ' + this.fillmodes[this.fillmode]);
                    this.cvs.ctx.fillStyle = this.fillmodes[this.fillmode];
                }
            } else if (e.keyCode == 82) {
                if (!this.robot) {
                    $('body').append('<canvas class="robot" width="500" height="250"></canvas>');
                    $('canvas.robot').dudlrRobot(this.cvs.recorder.recorded);
                    this.robot = $.dudlrRobots()[0];
                }
                this.robot.handDraw(10);
            }
        },

        mousemove: function(e) {
            if (!this.active) return false;
            var cvs = this.cvs;
            var ctx = cvs.ctx;
            var x = cvs.mousex;// - cvs.offx;
            var y = cvs.mousey;// - cvs.offy;
            if (x >= 0 && x <= 500 && y > 0 && y <= 250) {
                var lx = cvs.lastx;
                var ly = cvs.lasty;
                ctx.lineTo(x, y);
                ctx.stroke();
                this.cvs.recorder.lineTo(x, y);
            } else {
                cvs.lasty = cvs.lastx = -1;
            }            

        }, 

        mouseup: function(e) {
            var ctx = this.cvs.ctx;
            if (this.fillmode) {
                ctx.lineTo(this.startx, this.starty);
                this.cvs.recorder.lineTo(this.startx, this.starty);
                ctx.fill();
                this.cvs.recorder.fill();
            }
            this.active = false;
        }
    };
    
    DudlrStrokeRecorder = function () {
        return this.__init__();
    };

    DudlrStrokeRecorder.prototype = {
        __init__: function() {
            this.stack = [];
            this.recorded = "";
            this.last_command = null;
        },
        lineTo: function(x, y) {
            if (!this._inbounds(x, y)) {
                return;
            }
            //var stack = this.stack;
            this._popStack();
            if (this.last_command != 'l') {
                this.last_command = 'l';
                //stack.push('l');
                this.recorded += 'l';
            }
            //stack.push(x);
            //stack.push(y);
            this.recorded += this._pad(x) + this._pad(y);
        },
        moveTo: function(x, y) {
            if (!this._inbounds(x, y)) {
                return;
            }
            this._popStack();
            this.recorded += 'm' + this._pad(x) + this._pad(y);
            this.last_command = 'm';
        },
        fillStyle: function(mode) {
            this.stack.push('s' + mode);
            this.last_command = 's';
        },
        fill: function() {
            this.last_command = 'f';
            this.recorded += 'f';
        },
        _popStack: function() {
            if (this.stack.length) {
                this.recorded += this.stack[this.stack.length - 1];
                this.stack = [];
            }
        },
        _pad: function(n) {
            var x = n;
            if (x < 0) {
                x = 0;
            }
            if (x < 10) {
                return '00' + n;
            } else if (x < 100) {
                return '0' + n;
            } else {
                return '' + n;
            }
        },
        _inbounds: function(x, y) {
            return (x >= 0 && x <= 500 && y >= 0 && y <= 250);
        }
    };


    var DudlrRobot = function(domelement, recording) {
        return this.__init__(domelement, recording);
    };

    DudlrRobot.prototype = {

        __init__: function(domelement, recording) {
            this.recording = recording;
            this.domelement = domelement;
            this.cvs_elm = $(domelement);
            this._timer = false;
            this.idx = 0;
            this.ctx = this.cvs_elm[0].getContext('2d');
            this.ctx.fillStyle = "rgba(255,255,255,1)";
            this.ctx.fillRect(0, 0, this.cvs_elm[0].width, this.cvs_elm[0].height);
            this.ctx.fillStyle = "rgba(0,0,0,0.5)";
        },

        run: function() {
            this.idx = 0;
            while (this.idx < this.recording.length) {
                this._push();  
            } 
        },

        handDraw: function(interval) {
            var o = this;
            this._timer = window.setInterval(function() { o._push(); }, interval);
        },

        _push: function() {
            if (this.recording[this.idx] == 'm') {
                this.idx++;
                var x = 1 * (this.recording[this.idx++] + this.recording[this.idx++] + this.recording[this.idx++]);
                var y = 1 * (this.recording[this.idx++] + this.recording[this.idx++] + this.recording[this.idx++]);
                this.ctx.beginPath();
                this.ctx.moveTo(x, y);
                this.ctx.lineTo(x+1, y+1);
                this.ctx.stroke();
            } else if (this.recording[this.idx] == 'l') {
                this.idx++;
            } else if (this.recording[this.idx] == 's') {
                this.idx++;
                this.ctx.fillStyle = FILL_MODES[1 * this.recording[this.idx++]]; 
            } else if (this.recording[this.idx] == 'f') {
                this.idx++;
                this.ctx.fill();
            } else {
                var x = 1 * (this.recording[this.idx++] + this.recording[this.idx++] + this.recording[this.idx++]);
                var y = 1 * (this.recording[this.idx++] + this.recording[this.idx++] + this.recording[this.idx++]);
                this.ctx.lineTo(x, y);
                this.ctx.stroke();
            }
            if (this._timer && this.idx >= this.recording.length) {
                window.clearInterval(this._timer);
                this._timer = false;
            }
        }
    };

    _registered = [];

    $.dudlrCanvases = function() {
        return _registered;
    };

    $.fn.dudlrCanvas = function() {
        console.log("this [1] : " + this);
        return this.each(function() {
            console.log("this : " + this);
            _registered.push(new DudlrCanvas(this));
        });
    };

    _registeredBots = [];

    $.dudlrRobots = function() {
        return _registeredBots;
    };

    $.fn.dudlrRobot = function(data) {
        var last = null;
        this.each(function() {
            console.log("this : " + this);
            last = new DudlrRobot(this, data);
            _registeredBots.push(last);
        });
        return last;
    };

})(jQuery); 




