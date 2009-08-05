/**
 * Natter 5.0
 * Copyright 1999-2009 Charles Capps
 **/



/*******************************************************************************
 * Frontend -- Chat Form
 **/

// This script used to be inline with the chat form, and therefore could pull in
// configuration values without needing to think about it.
function get_caption_field_default_value() {
	if(caption_field_default_value)
		return caption_field_default_value;
	return 'E-Mail';
} // end get_caption_field_default_value


// Multichat permits one posting form to switch between multiple sets of nifty data.
multichat = {
	_base_struct: {
		username: 'Name',
		color: 'white',
		hex_color: '#ffffff',
		mcolor: 'Message Color',
		hex_mcolor: '#ffffff',
		caption: null,
		url: 'URL'
	},
// What's our name data look like?
	name_data: [
		{}
	],
// Which tab is active?
	active: 0,


// Init the module
	init: function() {
		multichat._base_struct.caption = get_caption_field_default_value();
		multichat.initNameData(0);
	},

// Init a name data structure
	initNameData: function(index) {
		var clone = {};
		$.each(multichat._base_struct, function(k, v) { clone[k] = v });
		multichat.name_data[index] = clone;
	},

// Post a message
	post: function() {
		var form_data = $('#frm').serializeArray();
		form_data.subm = 'Send';
		$.post(
			chat_script_name,
			form_data,
			function(json_data, textStatus){
			// Update the post form.
				multichat.updateForm(json_data, false, true);
			// Now turn the submit button back on.
				$('#subm').removeAttr('disabled');
				$('#subm').removeClass('disabled');
			// And refresh the chat frame
				setTimeout(refresh_chat, 250);
			// And refocus the posting form.
				$('#message').focus();
			},
			'json'
		);
	},

// Update the post form
	updateForm: function(data, skip_data_update, clobber_message) {
		$.each(data, function(index, value){
			if(!clobber_message && index == 'message') return;
		// The caption ends to get rather, uh, over-encoded.
			if(index == 'caption') {
			// Create a temporary textarea and use to perform HTML entity decoding.
				value = $('<textarea/>').html(value).val();
			}  // end if
			var el = $('#' + index);
			if(el) {
				el.attr('value', value);
			} // end if
		});
	// Update the internal representation of the username data
		if(!skip_data_update)
			multichat.updateName(multichat.active, data);
	// Show the user's name, hiding the text box until clicked.
		$('#multichat_name').html('<font color="' + data.hex_color + '" class="name"><b>' + data.username + '</b></font>');
		if(data.username == '' || data.username == 'Name') {
			$('#multichat_name').hide();
			$('#username').show();
		} else {
			$('#multichat_name').show();
			$('#username').hide();
		} // end if
	// Now hide the old name change link
		if($('#namechange_link'))
			$('#namechange_link').hide();
	},

// Update the name data in the tab list
	updateName: function(name_index, data) {
		multichat.name_data[ name_index ] = data;
		var name = data.username;
		if(name == '' || name == 'Name') name = 'lurker';
		$('#name-' + name_index).html('<font color="' + data.hex_color + '" class="name"><b>' + name + '</b></font><span class="yoink">x</span>');
	},

// Add a new name to the tab list
	addName: function() {
		var new_name_id = multichat.name_data.length;
		multichat.initNameData(new_name_id);
		$('#multichat-table-end').before('<td id="name-' + new_name_id + '"><font color="white" class="name"><b>lurker</b></font><span class="yoink">x</span></td>');
		multichat.selectName(new_name_id);
		$('#message').blur();
		$('#username').focus();
	},

// Select a name tab
	selectName: function(index) {
		if(index != parseInt(index)) return;
		if(!multichat.name_data) return;
	// Play class switcheroo
		$('#name-' + multichat.active).removeClass('picked');
		multichat.active = index;
		$('#name-' + multichat.active).addClass('picked');
	// Update the form with the name info
		multichat.updateForm(multichat.name_data[ multichat.active ], true, false);
		$('#message').focus();
	},

// Close a name tab
	closeName: function(index) {
		if(multichat.active == index) {
			var names = multichat.getNameList();
		// Can't close the last name.
			if(names.count < 2) {
				return;
			} // end if
			var found_index = null;
			var first_index = null;
			for(var k in names) {
				if(k == 'count') continue;
				if(k == index) continue;
			// Keep track of the first still active name
				if(first_index == null)
					first_index = k;
			// Try to find the name immediately to the left of the closed name
				if(found_index > index)
					break;
				found_index = k;
			} // end foreach
		// If we didn't find one to the left, default to the first.
			if(found_index == null)
				found_index = first_index;
			multichat.selectName(found_index);
		} // end if
	// Yoink the table cell
		$('#name-' + index).hide();
		multichat.name_data[index].disabled = 1;
	},

// Get a list of all active names
	getNameList: function() {
		var names = {};
		var count = 0;
		$.each(multichat.name_data, function(k, v) {
			if(!v.disabled) {
				names[k] = v;
				count++;
			}
		});
		names.count = count;
		return names;
	}
};




// Do the ondomready init for multichat
function chat_form_init_multichat() {
	multichat.init();
// Attach behavior to the add button
	$('#multichat-adder').click(function(){
		multichat.addName();
	});
// Attach behavior to the name change tab
	$('#multichat-name-pick-list td').live('click', function(event){
	// Determine the table cell
		var el = event.target;
		if(el.nodeName != 'TD') el = ($(event.target).parents('td'))[0];
	// Extract the id attribute
		if(!el.id) return null;
		var name_id = el.id.split(/\-/);
		if(!name_id || !name_id.length || name_id.length != 2) return null;
	// Call the select
		multichat.selectName(name_id[1]);
	// Stop bubbling.
		event.stopImmediatePropagation();
		event.stopPropagation();
		return false;
	});
// Attach behavior to the close tab link
	$('#multichat-name-pick-list td span.yoink').live('click', function(event){
	// Determine the table cell
		var el = event.target;
		if(el.nodeName != 'TD') el = ($(event.target).parents('td'))[0];
	// Extract the id attribute
		if(!el.id) return null;
		var name_id = el.id.split(/\-/);
		if(!name_id || !name_id.length || name_id.length != 2) return null;
	// Call the delete
		multichat.closeName(name_id[1]);
	// Stop bubbling.
		event.stopImmediatePropagation();
		event.stopPropagation();
		return false;
	});
// Finally, set up an ajax listener that looks for the X-JSON header
// and will throw error messages that are returned from the server
	$.ajaxSetup({
		complete: function(request, status) {
		// Did we get the header?
			var oops = request.getResponseHeader('X-JSON');
			if(!oops) return;
		// Yeeeup.  How bad is it?  We can only process standardHTML messages.
			var data = eval('(' + oops + ')');
			if(!data.standardhtml) return;
		// Yeah, it's bad.  This is a world-ender.  Rewrite the world.
			if(data.html) {
				data.header = '';
				data.body = data.html;
				data.footer = '';
			} // end if
			$('div.header').attr('id', 'old_header').hide().after('<div class="header">' + data.header + '</div>');
			$('div.body').attr('id', 'old_body').hide().after('<div class="body">' + data.body + '</div>');
			$('div.footer').attr('id', 'old_footer').hide().after('<div class="footer">' + data.footer + '</div>');
		}
	});
} // end chat_form_multichat_init



// Do the ondomready init for the chat form
function chat_form_init() {
// Set up hover compat for stupid browsers
	$('.textbox, .textarea')
		.focus(function(event){
			$(event.target).addClass('focus');
			$(event.target).select();
		})
		.blur(function(event){
			$(event.target).removeClass('focus');
		})
		.mouseover(function(event){
			$(event.target).addClass('hover');
		})
		.mouseout(function(event){
			$(event.target).removeClass('hover');
		});
// Submit button gets disabled on click, and the form submitted manually.
	$('#subm').click(function(event){
		var el = $(event.target);
		var is_disabled = el.attr('disabled') ? 1 : 0;
		el.attr('disabled', 'disabled');
		el.addClass('disabled');
		if(!is_disabled && multichat_enabled) {
			multichat.post();
		} else if(!is_disabled) {
			$('#frm').submit();
		} // end if
		event.preventDefault();
		event.stopPropagation();
		return false;
	});
// Update button is scripty
	$('#upd').click(refresh_chat);
// Now focus the message field
	var msg = $('#message');
	if(msg)
		msg.focus();
// Attach hiding and showing the ajax loading box to the loading box...
	$().ajaxStart(ajax_loader_start);
	$().ajaxComplete(ajax_loader_end);
// And force a refresh of the messages window
	refresh_chat();
// Relocate the ajax loading box
	var subm_tl = $('#subm').offset();
	$('#ajaxloader').css({ top: subm_tl.top + 'px', left: (subm_tl.left - 25) + 'px', position: 'absolute' });
// Hide the name change link and show the name form, when clicked
	$('#multichat_name').click(function(event){
		$('#multichat_name').hide();
		$('#username').show();
	});
} // end chat_form_init




/*******************************************************************************
 * Frontend -- Messages Frame
 **/

// Do the ondomready for the ajax messages frame
function messages_refresh() {
// Reset any active timeout.
	clearTimeout(timeout);
	$.getJSON(
		script_name,
		{
			'action': 'messages',
			'newer_than': newest_id
		},
		function(data, status) {
			if((status == 'notmodified') || (status == 'success')) {
				var new_message_count = data[0];
				var newest_message_id = data[1];
				var new_messages = data[2];
				if(new_message_count > 0) {
				// Slide in messages every 750ms, taking 500 to slide.
					var delay = 0;
					var fade = 500;
					var step = 250;
					for(var i in new_messages) {
						delay += step;
						setTimeout(function(html, message_id, fade){
							$('#message_container').prepend(html);
							$('#message-' + message_id).hide().slideDown(fade);
						}, delay, new_messages[i].html, new_messages[i].message_id, fade);
						delay += fade;
					} // end for
				// Now, prune excess messages, once the last message has been added.
					setTimeout(function() {
						$('#message_container div.messageline:gt(' + (max_messages - 1) + ')').slideUp(fade, function(){ $(this).remove(); });
					}, delay);
				} // end if
			} else {
			} // end if
			timeout = setTimeout(messages_refresh, 8000);
			newest_id = newest_message_id;
		}
	);
} // end messages_refresh



/*******************************************************************************
 * Backend -- Control Panel -- Style Page
 **/

// Change the color box when requested
	function colorchange_callback(event) {
		var element = $(event.target);
		var idsplit = element.attr('id').split('-');
		if(!idsplit || !idsplit[1])
			return;
		$('#colorpicker-' + idsplit[1]).css({ backgroundColor: element.val() });
	} // end colorchange_callback

// Open the color picker when color boxes are clicked
	function colorbox_callback(event) {
		var element = $(event.target);
		var idsplit = element.attr('id').split('-');
		if(!idsplit || !idsplit[1])
			return;
		var color_name = idsplit[1];
		var color_hex = $('#color-' + color_name).attr('value');
		// console.debug(color_hex);
		$('#color_value').jqcp_setColor(color_hex);
		$('#color-current').attr('value', color_name);
		$('#lol-color-dialog').dialog('open');
	} // end colorbox_callback

// ondomready for the control panel style page
	function cp_style_init(){
	// Color box changing
		$('input.colorbox').focus(colorchange_callback);
		$('input.colorbox').blur(colorchange_callback);
		$('div.colorpicker-cell').click(colorbox_callback);
	// The widget
		$('#color_picker').jqcp();
		$('#color_value').jqcp_setObject();
	// The dialog
		$('#lol-color-dialog').dialog({
			autoOpen: false,
			height: 335,
			width: 300,
			resizable: false,
			title: "Pick a Color",
			buttons: {
				"Select This Color": function() {
					var color_name = $('#color-current').attr('value');
					$('#color-' + color_name).attr('value', $('#color_value').attr('value'));
					$(this).dialog('close');
					$('#color-' + color_name).blur();
				},
				"Cancel": function() { $(this).dialog('close'); }
			}
		});
	}



/*******************************************************************************
 * Frontend -- Guard Frame
 **/

	function guard_pane_init(){
		$('tr.bantoprow, tr.banbotrow')
		// Twiddle borders on hover
			.mouseover(function(event){
			// Who are we pointing at?  Note we use currentTarget here, not target.
			// currentTarget is the element that fired the event, target is the one
			// that is *active* in the event, i.e. a child.
				var tr = $(event.currentTarget);
			// Extract the line number
				var match = tr.attr('id').match(/\-(\d+)/);
				if(!match || !match[1])
					return;
			// Now use that to turn the cells on.
				$('#radio-' + match[1]).addClass('active');
				$('#name-' + match[1]).addClass('active');
				$('#data-' + match[1]).addClass('active');
			})
		// Twiddle hovers on unhover
			.mouseout(function(event){
				var tr = $(event.currentTarget);
			// Extract the line number
				var match = tr.attr('id').match(/\-(\d+)/);
				if(!match || !match[1])
					return;
			// Now use that to turn the cells on.
				$('#radio-' + match[1]).removeClass('active');
				$('#name-' + match[1]).removeClass('active');
				$('#data-' + match[1]).removeClass('active');
			})
		// Clicking any of the cells will trigger selection of the checkbox.
			.click(function(event){
				var tr = $(event.currentTarget);
			// Extract the line number
				var match = tr.attr('id').match(/\-(\d+)/);
				if(!match || !match[1])
					return;
				var line_id = match[1];
			// Check it
				$('#iden-' + line_id).attr('checked', 'checked');
			// Now update the ban info at the bottom
				update_summary(line_id);
			});
		// The method dropdown changes the IP information...
			$('#meethod').change(function(){ update_summary(); });
		// The big red button needs extra special magic
			$('#bankickbtn').click(function(event){
				var reason = $('#reason').attr('value');
				if(!reason || !reason.length) {
					alert("You must provide a reason for this kick or ban.");
					event.preventDefault();
					event.stopPropagation();
					return false;
				} // end if
				return null;
			});
		// The refresh button
			$('#banrefreshbtn, #banrefreshbtn_top').click(function(event){
				location.href = guard_script_url + '?action=list_users';
			});
	}


	function update_summary(line_id) {
	// If we didn't get a line id, try to determine it...
		if(!line_id) {
			var match = $('input[name=iden]:checked').attr('id').match(/\-(\d+)/);
			if(!match || !match[1])
				return null;
			line_id = match[1];
		} // end if
	// Extract data from the radio button
		var radio = $('#iden-' + line_id);
		var mrf = radio.attr('value');
		var match = mrf.match(/^([a-zA-Z0-9]+)\|\^\|([\d\.]+)$/);
		if(!match || match.length != 3)
			return null;
	// Update the one form value we care about, and display IP info if needed
		var ban_type = $('#meethod').attr('value');
		var data;
		if(ban_type == 'byid') {
		// This will be a session ban
			data = match[1];
			$('#pubip').css({ visibility: 'hidden' });
			$('#pubip-label').css({ visibility: 'hidden' });
		} else {
		// This will be an IP-based ban.
			data = match[2];
			$('#pubip').html(data);
			$('#pubip').css({ visibility: 'visible' });
			$('#pubip-label').css({ visibility: 'visible' });
		} // end if
		$('#summy').attr('value', data);
		return data;
	} // end update_summary




