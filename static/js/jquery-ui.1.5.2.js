/*
 * jQuery UI @VERSION
 *
 * Copyright (c) 2008 Paul Bakaus (ui.jquery.com)
 * Dual licensed under the MIT (MIT-LICENSE.txt)
 * and GPL (GPL-LICENSE.txt) licenses.
 *
 * http://docs.jquery.com/UI
 */
;(function($) {

$.ui = {
	plugin: {
		add: function(module, option, set) {
			var proto = $.ui[module].prototype;
			for(var i in set) {
				proto.plugins[i] = proto.plugins[i] || [];
				proto.plugins[i].push([option, set[i]]);
			}
		},
		call: function(instance, name, args) {
			var set = instance.plugins[name];
			if(!set) { return; }
			
			for (var i = 0; i < set.length; i++) {
				if (instance.options[set[i][0]]) {
					set[i][1].apply(instance.element, args);
				}
			}
		}	
	},
	cssCache: {},
	css: function(name) {
		if ($.ui.cssCache[name]) { return $.ui.cssCache[name]; }
		var tmp = $('<div class="ui-gen">').addClass(name).css({position:'absolute', top:'-5000px', left:'-5000px', display:'block'}).appendTo('body');
		
		//if (!$.browser.safari)
			//tmp.appendTo('body'); 
		
		//Opera and Safari set width and height to 0px instead of auto
		//Safari returns rgba(0,0,0,0) when bgcolor is not set
		$.ui.cssCache[name] = !!(
			(!(/auto|default/).test(tmp.css('cursor')) || (/^[1-9]/).test(tmp.css('height')) || (/^[1-9]/).test(tmp.css('width')) || 
			!(/none/).test(tmp.css('backgroundImage')) || !(/transparent|rgba\(0, 0, 0, 0\)/).test(tmp.css('backgroundColor')))
		);
		try { $('body').get(0).removeChild(tmp.get(0));	} catch(e){}
		return $.ui.cssCache[name];
	},
	disableSelection: function(el) {
		$(el).attr('unselectable', 'on').css('MozUserSelect', 'none');
	},
	enableSelection: function(el) {
		$(el).attr('unselectable', 'off').css('MozUserSelect', '');
	},
	hasScroll: function(e, a) {
		var scroll = /top/.test(a||"top") ? 'scrollTop' : 'scrollLeft', has = false;
		if (e[scroll] > 0) return true; e[scroll] = 1;
		has = e[scroll] > 0 ? true : false; e[scroll] = 0;
		return has;
	}
};


/** jQuery core modifications and additions **/

var _remove = $.fn.remove;
$.fn.remove = function() {
	$("*", this).add(this).triggerHandler("remove");
	return _remove.apply(this, arguments );
};

// $.widget is a factory to create jQuery plugins
// taking some boilerplate code out of the plugin code
// created by Scott González and Jörn Zaefferer
function getter(namespace, plugin, method) {
	var methods = $[namespace][plugin].getter || [];
	methods = (typeof methods == "string" ? methods.split(/,?\s+/) : methods);
	return ($.inArray(method, methods) != -1);
}

$.widget = function(name, prototype) {
	var namespace = name.split(".")[0];
	name = name.split(".")[1];
	
	// create plugin method
	$.fn[name] = function(options) {
		var isMethodCall = (typeof options == 'string'),
			args = Array.prototype.slice.call(arguments, 1);
		
		if (isMethodCall && getter(namespace, name, options)) {
			var instance = $.data(this[0], name);
			return (instance ? instance[options].apply(instance, args)
				: undefined);
		}
		
		return this.each(function() {
			var instance = $.data(this, name);
			if (isMethodCall && instance && $.isFunction(instance[options])) {
				instance[options].apply(instance, args);
			} else if (!isMethodCall) {
				$.data(this, name, new $[namespace][name](this, options));
			}
		});
	};
	
	// create widget constructor
	$[namespace][name] = function(element, options) {
		var self = this;
		
		this.widgetName = name;
		this.widgetBaseClass = namespace + '-' + name;
		
		this.options = $.extend({}, $.widget.defaults, $[namespace][name].defaults, options);
		this.element = $(element)
			.bind('setData.' + name, function(e, key, value) {
				return self.setData(key, value);
			})
			.bind('getData.' + name, function(e, key) {
				return self.getData(key);
			})
			.bind('remove', function() {
				return self.destroy();
			});
		this.init();
	};
	
	// add widget prototype
	$[namespace][name].prototype = $.extend({}, $.widget.prototype, prototype);
};

$.widget.prototype = {
	init: function() {},
	destroy: function() {
		this.element.removeData(this.widgetName);
	},
	
	getData: function(key) {
		return this.options[key];
	},
	setData: function(key, value) {
		this.options[key] = value;
		
		if (key == 'disabled') {
			this.element[value ? 'addClass' : 'removeClass'](
				this.widgetBaseClass + '-disabled');
		}
	},
	
	enable: function() {
		this.setData('disabled', false);
	},
	disable: function() {
		this.setData('disabled', true);
	}
};

$.widget.defaults = {
	disabled: false
};


/** Mouse Interaction Plugin **/

$.ui.mouse = {
	mouseInit: function() {
		var self = this;
	
		this.element.bind('mousedown.'+this.widgetName, function(e) {
			return self.mouseDown(e);
		});
		
		// Prevent text selection in IE
		if ($.browser.msie) {
			this._mouseUnselectable = this.element.attr('unselectable');
			this.element.attr('unselectable', 'on');
		}
		
		this.started = false;
	},
	
	// TODO: make sure destroying one instance of mouse doesn't mess with
	// other instances of mouse
	mouseDestroy: function() {
		this.element.unbind('.'+this.widgetName);
		
		// Restore text selection in IE
		($.browser.msie
			&& this.element.attr('unselectable', this._mouseUnselectable));
	},
	
	mouseDown: function(e) {
		// we may have missed mouseup (out of window)
		(this._mouseStarted && this.mouseUp(e));
		
		this._mouseDownEvent = e;
		
		var self = this,
			btnIsLeft = (e.which == 1),
			elIsCancel = (typeof this.options.cancel == "string" ? $(e.target).parents().add(e.target).filter(this.options.cancel).length : false);
		if (!btnIsLeft || elIsCancel || !this.mouseCapture(e)) {
			return true;
		}
		
		this._mouseDelayMet = !this.options.delay;
		if (!this._mouseDelayMet) {
			this._mouseDelayTimer = setTimeout(function() {
				self._mouseDelayMet = true;
			}, this.options.delay);
		}
		
		if (this.mouseDistanceMet(e) && this.mouseDelayMet(e)) {
			this._mouseStarted = (this.mouseStart(e) !== false);
			if (!this._mouseStarted) {
				e.preventDefault();
				return true;
			}
		}
		
		// these delegates are required to keep context
		this._mouseMoveDelegate = function(e) {
			return self.mouseMove(e);
		};
		this._mouseUpDelegate = function(e) {
			return self.mouseUp(e);
		};
		$(document)
			.bind('mousemove.'+this.widgetName, this._mouseMoveDelegate)
			.bind('mouseup.'+this.widgetName, this._mouseUpDelegate);
		
		return false;
	},
	
	mouseMove: function(e) {
		// IE mouseup check - mouseup happened when mouse was out of window
		if ($.browser.msie && !e.button) {
			return this.mouseUp(e);
		}
		
		if (this._mouseStarted) {
			this.mouseDrag(e);
			return false;
		}
		
		if (this.mouseDistanceMet(e) && this.mouseDelayMet(e)) {
			this._mouseStarted =
				(this.mouseStart(this._mouseDownEvent, e) !== false);
			(this._mouseStarted ? this.mouseDrag(e) : this.mouseUp(e));
		}
		
		return !this._mouseStarted;
	},
	
	mouseUp: function(e) {
		$(document)
			.unbind('mousemove.'+this.widgetName, this._mouseMoveDelegate)
			.unbind('mouseup.'+this.widgetName, this._mouseUpDelegate);
		
		if (this._mouseStarted) {
			this._mouseStarted = false;
			this.mouseStop(e);
		}
		
		return false;
	},
	
	mouseDistanceMet: function(e) {
		return (Math.max(
				Math.abs(this._mouseDownEvent.pageX - e.pageX),
				Math.abs(this._mouseDownEvent.pageY - e.pageY)
			) >= this.options.distance
		);
	},
	
	mouseDelayMet: function(e) {
		return this._mouseDelayMet;
	},
	
	// These are placeholder methods, to be overriden by extending plugin
	mouseStart: function(e) {},
	mouseDrag: function(e) {},
	mouseStop: function(e) {},
	mouseCapture: function(e) { return true; }
};

$.ui.mouse.defaults = {
	cancel: null,
	distance: 1,
	delay: 0
};

})(jQuery);
/*
 * jQuery UI Accordion
 * 
 * Copyright (c) 2007, 2008 Jörn Zaefferer
 * Dual licensed under the MIT (MIT-LICENSE.txt)
 * and GPL (GPL-LICENSE.txt) licenses.
 *
 * http://docs.jquery.com/UI/Accordion
 *
 * Depends:
 *	ui.core.js
 */
(function($) {

$.widget("ui.accordion", {
	init: function() {
		var options = this.options;
		
		if ( options.navigation ) {
			var current = this.element.find("a").filter(options.navigationFilter);
			if ( current.length ) {
				if ( current.filter(options.header).length ) {
					options.active = current;
				} else {
					options.active = current.parent().parent().prev();
					current.addClass("current");
				}
			}
		}
		
		// calculate active if not specified, using the first header
		options.headers = this.element.find(options.header);
		options.active = findActive(options.headers, options.active);
		
		// IE7-/Win - Extra vertical space in Lists fixed
		if ($.browser.msie) {
			this.element.find('a').css('zoom', '1');
		}
		
		if (!this.element.hasClass("ui-accordion")) {
			this.element.addClass("ui-accordion");
			$("<span class='ui-accordion-left'/>").insertBefore(options.headers);
			$("<span class='ui-accordion-right'/>").appendTo(options.headers);
			options.headers.addClass("ui-accordion-header").attr("tabindex", "0");
		}
		
		var maxHeight;
		if ( options.fillSpace ) {
			maxHeight = this.element.parent().height();
			options.headers.each(function() {
				maxHeight -= $(this).outerHeight();
			});
			var maxPadding = 0;
			options.headers.next().each(function() {
				maxPadding = Math.max(maxPadding, $(this).innerHeight() - $(this).height());
			}).height(maxHeight - maxPadding);
		} else if ( options.autoHeight ) {
			maxHeight = 0;
			options.headers.next().each(function() {
				maxHeight = Math.max(maxHeight, $(this).outerHeight());
			}).height(maxHeight);
		}
	
		options.headers
			.not(options.active || "")
			.next()
			.hide();
		options.active.parent().andSelf().addClass(options.selectedClass);
		
		if (options.event) {
			this.element.bind((options.event) + ".accordion", clickHandler);
		}
	},
	activate: function(index) {
		// call clickHandler with custom event
		clickHandler.call(this.element[0], {
			target: findActive( this.options.headers, index )[0]
		});
	},
	destroy: function() {
		this.options.headers.next().css("display", "");
		if ( this.options.fillSpace || this.options.autoHeight ) {
			this.options.headers.next().css("height", "");
		}
		$.removeData(this.element[0], "accordion");
		this.element.removeClass("ui-accordion").unbind(".accordion");
	}
});

function scopeCallback(callback, scope) {
	return function() {
		return callback.apply(scope, arguments);
	};
};

function completed(cancel) {
	// if removed while animated data can be empty
	if (!$.data(this, "accordion")) {
		return;
	}
	
	var instance = $.data(this, "accordion");
	var options = instance.options;
	options.running = cancel ? 0 : --options.running;
	if ( options.running ) {
		return;
	}
	if ( options.clearStyle ) {
		options.toShow.add(options.toHide).css({
			height: "",
			overflow: ""
		});
	}
	$(this).triggerHandler("accordionchange", [$.event.fix({type: 'accordionchange', target: instance.element[0]}), options.data], options.change);
}

function toggle(toShow, toHide, data, clickedActive, down) {
	var options = $.data(this, "accordion").options;
	options.toShow = toShow;
	options.toHide = toHide;
	options.data = data;
	var complete = scopeCallback(completed, this);
	
	// count elements to animate
	options.running = toHide.size() === 0 ? toShow.size() : toHide.size();
	
	if ( options.animated ) {
		if ( !options.alwaysOpen && clickedActive ) {
			$.ui.accordion.animations[options.animated]({
				toShow: jQuery([]),
				toHide: toHide,
				complete: complete,
				down: down,
				autoHeight: options.autoHeight
			});
		} else {
			$.ui.accordion.animations[options.animated]({
				toShow: toShow,
				toHide: toHide,
				complete: complete,
				down: down,
				autoHeight: options.autoHeight
			});
		}
	} else {
		if ( !options.alwaysOpen && clickedActive ) {
			toShow.toggle();
		} else {
			toHide.hide();
			toShow.show();
		}
		complete(true);
	}
}

function clickHandler(event) {
	var options = $.data(this, "accordion").options;
	if (options.disabled) {
		return false;
	}
	
	// called only when using activate(false) to close all parts programmatically
	if ( !event.target && !options.alwaysOpen ) {
		options.active.parent().andSelf().toggleClass(options.selectedClass);
		var toHide = options.active.next(),
			data = {
				options: options,
				newHeader: jQuery([]),
				oldHeader: options.active,
				newContent: jQuery([]),
				oldContent: toHide
			},
			toShow = (options.active = $([]));
		toggle.call(this, toShow, toHide, data );
		return false;
	}
	// get the click target
	var clicked = $(event.target);
	
	// due to the event delegation model, we have to check if one
	// of the parent elements is our actual header, and find that
	// otherwise stick with the initial target
	clicked = $( clicked.parents(options.header)[0] || clicked );
	
	var clickedActive = clicked[0] == options.active[0];
	
	// if animations are still active, or the active header is the target, ignore click
	if (options.running || (options.alwaysOpen && clickedActive)) {
		return false;
	}
	if (!clicked.is(options.header)) {
		return;
	}
	
	// switch classes
	options.active.parent().andSelf().toggleClass(options.selectedClass);
	if ( !clickedActive ) {
		clicked.parent().andSelf().addClass(options.selectedClass);
	}
	
	// find elements to show and hide
	var toShow = clicked.next(),
		toHide = options.active.next(),
		//data = [clicked, options.active, toShow, toHide],
		data = {
			options: options,
			newHeader: clicked,
			oldHeader: options.active,
			newContent: toShow,
			oldContent: toHide
		},
		down = options.headers.index( options.active[0] ) > options.headers.index( clicked[0] );
	
	options.active = clickedActive ? $([]) : clicked;
	toggle.call(this, toShow, toHide, data, clickedActive, down );

	return false;
};

function findActive(headers, selector) {
	return selector != undefined
		? typeof selector == "number"
			? headers.filter(":eq(" + selector + ")")
			: headers.not(headers.not(selector))
		: selector === false
			? $([])
			: headers.filter(":eq(0)");
}

$.extend($.ui.accordion, {
	defaults: {
		selectedClass: "selected",
		alwaysOpen: true,
		animated: 'slide',
		event: "click",
		header: "a",
		autoHeight: true,
		running: 0,
		navigationFilter: function() {
			return this.href.toLowerCase() == location.href.toLowerCase();
		}
	},
	animations: {
		slide: function(options, additions) {
			options = $.extend({
				easing: "swing",
				duration: 300
			}, options, additions);
			if ( !options.toHide.size() ) {
				options.toShow.animate({height: "show"}, options);
				return;
			}
			var hideHeight = options.toHide.height(),
				showHeight = options.toShow.height(),
				difference = showHeight / hideHeight;
			options.toShow.css({ height: 0, overflow: 'hidden' }).show();
			options.toHide.filter(":hidden").each(options.complete).end().filter(":visible").animate({height:"hide"},{
				step: function(now) {
					var current = (hideHeight - now) * difference;
					if ($.browser.msie || $.browser.opera) {
						current = Math.ceil(current);
					}
					options.toShow.height( current );
				},
				duration: options.duration,
				easing: options.easing,
				complete: function() {
					if ( !options.autoHeight ) {
						options.toShow.css("height", "auto");
					}
					options.complete();
				}
			});
		},
		bounceslide: function(options) {
			this.slide(options, {
				easing: options.down ? "bounceout" : "swing",
				duration: options.down ? 1000 : 200
			});
		},
		easeslide: function(options) {
			this.slide(options, {
				easing: "easeinout",
				duration: 700
			});
		}
	}
});

// deprecated, use accordion("activate", index) instead
$.fn.activate = function(index) {
	return this.accordion("activate", index);
};

})(jQuery);
