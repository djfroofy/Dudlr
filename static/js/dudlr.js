/*
 * jquery.mnervDoodle.js
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
            this.active = true;
        },

        keyup: function(e) {
            if (e.keyCode == 70) {
                this.fillmode += 1;
                this.fillmode = this.fillmode % this.fillmodes.length;
                console.log('fill mode : ' + this.fillmode);
                // XXX - need to make callback
                $('#fill-mode').text(this.fillmodeLabels[this.fillmode]);
                if (this.fillmode) {
                    console.log('setting fillstyle to : ' + this.fillmodes[this.fillmode]);
                    this.cvs.ctx.fillStyle = this.fillmodes[this.fillmode];
                }
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
            } else {
                cvs.lasty = cvs.lastx = -1;
            }            

        }, 

        mouseup: function(e) {
            var ctx = this.cvs.ctx;
            ctx.lineTo(this.startx, this.starty);
            if (this.fillmode) ctx.fill();
            this.active = false;
        }
    }


    _registered = [];

    $.dudlrCanvases = function() {
        return _registered;
    };

    $.fn.dudlrCanvas = function() {
        console.log("this [1] : " + this);
        return this.each(function() {
            console.log("this : " + this);
            _registered[_registered.length] = new DudlrCanvas(this);
        });
    };

})(jQuery); 




