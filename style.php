<?php
// Natter 4.9
// Copyright 1999-2009 Charles Capps
//
// This software is covered by a license agreement.
// If you do not have a license for this software, please
// contact <capps@solareclipse.net> immediately.
//
// Using this software without a valid license is a violation
// of the author's rights and is often illegal.
//
// Distribution of this script is stricly prohibited.
//
// Questions?  Comments?  <capps@solareclipse.net>
//

// This code was designed when Netscape 4 was a dominant browser, and CSS support
// in other browsers sucked.  Pardon the mess.  Refactoring can only do so much.

	error_reporting(0);
	ini_set('display_errors', false);
	ob_start();

// The defined styles have these elements in common
	$base_style = array(
		'BGColor' 			=> '#000000',
		'BGLightColor'		=> '#101010',
		'BorderColor' 		=> '#a0a0a0',
		'BanColor' 			=> '#808080',
		'BanHiliteColor'	=> '#a0a0f0',
		'BanDarkColor'		=> '#101010',
		'BanLiftColor'		=> '#f0a0a0',
		'PoweredByColor'	=> '#303040',
		'MultiChatBorder'	=> '#444444',
	);
// Blue variant, for TwC
	$blue_style = array_merge(array(
		'TextColor' 		=> '#ddddee',
		'DarkTextColor' 	=> '#505060',
		'TimeColor' 		=> '#a0a0b0',
		'HRColor' 			=> '#4d78b9',
		'HRColor2' 			=> '#0066b3',
		'AjaxLoader'		=> 'ajax_blue.gif',
	), $base_style);
// Orange variant, for Phoenix
	$orange_style = array_merge(array(
		'TextColor' 		=> '#dddddd',
		'DarkTextColor' 	=> '#505050',
		'TimeColor' 		=> '#a0a0a0',
		'HRColor' 			=> '#fc9833',
		'HRColor2' 			=> '#fca853',
		'AjaxLoader'		=> 'ajax_orange.gif',
	), $base_style);
// Bronze variant, for MU
	$bronze_style = array_merge(array(
		'TextColor' 		=> '#dddddd',
		'DarkTextColor' 	=> '#505060',
		'TimeColor' 		=> '#a0a0a0',
		'HRColor' 			=> '#ABA457',
		'HRColor2' 			=> '#ABA457',
		'AjaxLoader'		=> 'ajax_bronze.gif',
	), $base_style);
// And we'll pick...
	$styles = array(
		'blue' => $blue_style,
		'orange' => $orange_style,
		'bronze' => $bronze_style
	);
// ... which one, exactly?
	if(!isset($_GET['style']))
		$_GET['style'] = 'bronze';
	if(!isset($styles[ $_GET['style'] ]))
		$_GET['style'] = 'bronze';
// ... this one!
	$style = $styles[ $_GET['style'] ];

	$css = <<<THESTYLESHEET
/* STYLE = {$_GET['style']} */
	body  {
		background: {$style['BGColor']};
		font-family: Verdana, Helvetica, Arial, sans-serif;
		color: {$style['TextColor']};
		font-size: 80%;
		margin: 5px;
		padding: 0px;
		border: 0px;
	}

	.header { font-size: 175%; font-weight: bold; text-align: center; color: {$style['HRColor']}; }
	.body { text-align: center; font-size: 100%; color: {$style['TextColor']}; font-family: Verdana, Helvetica, Arial, sans-serif; }
	.footer { font-size: 100%; text-align: center; font-style: oblique }
	.copy { font-size: 10px; color: {$style['PoweredByColor']}; text-align: center }
	.timeline { font-size: 10px; color: {$style['TimeColor']}; text-align: left }
	.name { font-size: 125%; font-family: Times New Roman, Times Roman, Times, serif }
	hr { background-color: {$style['HRColor']}; color: {$style['HRColor']}; border: 0px; }


/* Fucking IE needs a fucking hack because it doesn't understand transparent borders. */
	*html a:link, *html a:visited { border-color: {$style['BGColor']};  }

/* Links */
	a:link, a:visited { color: white; border: 1px solid transparent; padding: 1px }
	a:link:hover, a:visited:hover { border: 1px solid {$style['TextColor']}; text-decoration: none; background-color: {$style['DarkTextColor']}}
	a:link.namer { background-color: black; border: 0px; text-decoration: none }
	a:link:hover.namer { background-color: black; border: 0px; text-decoration: none }
	a:visited.namer { background-color: black; border: 0px; text-decoration: none }

/* The powered-by link is hidden */
	.copy a, .copy a:link, .copy a:visited, .copy a:active, .copy a:hover {
		color: {$style['PoweredByColor']};
		border: 0px;
		padding: 0px;
		background-color: {$style['BGColor']};
		text-decoration: none;
	}
	.copy a:hover {
		text-decoration: underline;
	}

/* Pre tags tend to get a little funky... */
	pre { font-family: Courier New, Courier, fixed; font-size: 125%; }

/* Message lines in the chat */
	.messageline { padding: 0px 0px 6px 10px; font-size: 100%; font-family: Verdana, Arial, Helvetica, sans-serif  }
	.thename { font-size: 150%; font-family: Times New Roman, Times Roman, Times, serif; font-weight: bold  }
	.thecaption { font-size: 90%; font-family: Verdana, Arial, Helvetica, sans-serif }
	.thelinks { font-size: 140%; font-family: Wingdings }
	.thetime { font-size: 80%; font-family: Verdana, Arial, Helvetica, sans-serif }
	.themessage { font-size: 100%; font-family: Verdana, Arial, Helvetica, sans-serif }
/* Links in the message line */
	a.url, a.email {
		border: 0px;
		margin: 0px;
		padding: 0px;
		margin-left: 2px;
		margin-right: 2px;
		text-decoration: none;
		background-repeat: no-repeat;
		background-position: top left;
		display: -moz-inline-block;
		display: inline-block;
	}
	a.url {
		font-size: 10px;
		height: 13px;
		width: 10px;
		background-image: url(wingdings-letter.png);
	}
	a.email {
		font-size: 10px;
		height: 13px;
		width: 17px;
		background-image: url(wingdings-envelope.png);
	}
	a:hover.url, a:hover.email {
		border: 0px;
		background-color: white !important;
	}

/* New user welcome */
	.messageline.welcome { color: {$style['DarkTextColor']}; }
	.messageline.welcome .star { color: {$style['TextColor']}; }

/* Posting form */
	.button, .textbox, .textarea, input[type=submit], input[type=button], input[type=text], select, textarea {
		background-color : {$style['BGColor']};
		border: 1px solid {$style['BorderColor']};
		font-size : 11px;
		color: {$style['TextColor']};
		font-family : verdana, arial, sans-serif;
	}
	.button {
		cursor: hand;
		cursor: pointer;
	}
	.textbox {
		width: 145px;
	}
	.textarea {
		width: 520px;
		height: 35px;
	}
	.namer {
		cursor: hand;
		cursor: pointer;
	}

/* Hover magic for browsers that don't understand non-anchor based hover/focus is provided via jQuery */
	.textbox:hover, .textarea:hover, .button:hover, .textbox:hover, .textarea:hover, .button:hover,
	input[type=submit]:hover, input[type=button]:hover, input[type=text]:hover, select:hover, textarea:hover {
		border-color: {$style['HRColor']};
	}
	.textbox:focus, .textarea:focus, .button:focus, .textbox.focus, .textarea.focus, .button.focus,
	input[type=submit]:focus, input[type=button]:focus, input[type=text]:focus, select:focus, textarea:focus,
	.textbox:active, .textarea:active, .button:active,
	input[type=submit]:active, input[type=button]:active, input[type=text]:active, select:active, textarea:active {
		border-color: {$style['HRColor2']};
		background-color: {$style['BGLightColor']};
	}
	input.disabled, input[disabled], button.disabled, button[disabled] {
		color: {$style['DarkTextColor']} !important;
		border-color: {$style['DarkTextColor']} !important;
		background-color: {$style['BGLightColor']} !important;
	}

/* Ajax loader */
	#ajaxloader {
		height: 18px;
		width: 20px;
		position: absolute;
	}
	#ajaxloader.loading {
		background-image: url({$style[AjaxLoader]});
		background-attachment: scroll;
		background-position: center center;
		background-repeat: no-repeat;
	}

/* Multichat bits */
	#multichat-name-pick-list {
		border-collapse: separate;
		margin: 0px;
		margin-bottom: 3px;
		padding: 0px;
		border: 0px;
	}
	#multichat-name-pick-list td {
		font-size: 90%;
		padding: 1px;
		padding-left: 5px;
		padding-right: 5px;
		text-align: center;
		border: 1px solid {$style['MultiChatBorder']};
		border-top: 0px;
		border-left: 0px;
		border-right: 0px;
	}
	#multichat-name-pick-list td.picked {
		border: 1px solid {$style['MultiChatBorder']};
		border-bottom: 0px;
	}
	#multichat-name-pick-list td.picked span.yoink {
		display: inline;
		color: red;
		margin-left: 5px;
		cursor: hand;
		cursor: pointer;
	}
	#multichat-name-pick-list td.picked span.yoink:hover {
		text-decoration: underline;
	}
	#multichat-name-pick-list td span.yoink {
		display: none;
	}
	#multichat-name-pick-list td.adder {
		border-bottom: 0px;
		border-left: 1px solid {$style['MultiChatBorder']};
		border-top: 1px solid {$style['MultiChatBorder']};
		text-align: center;
		font-weight: bold;
		cursor: hand;
		cursor: pointer;
	}
	#multichat-name-pick-list td .name {
		font-size: 110%;
		font-weight: normal;
		cursor: hand;
		cursor: pointer;
	}
	#multichat-name-pick-list td.picked .name {
		font-size: 115%;
		font-weight: bold;
		cursor: hand;
		cursor: pointer;
	}

/* Guard page: main table cell magic */
	#bantable {
		border: 2px solid {$style['BanColor']};
		width: 172px;
		margin: 0px;
		padding: 0px;
		border-collapse: separate;
	}
	#bantable tr.bantoprow, #bantable tr.banbotrow {
		cursor: pointer;
		cursor: hand;
	}
	#bantable tr.bantoprow td, #bantable tr.banbotrow td {
		border: 2px solid {$style['BGColor']};
	}
	#bantable td.banbtncell {
		border-right: 0px !important;
	}
	#bantable td.bannamecell {
		border-bottom: 0px !important;
		border-left: 0px !important;
	}
	#bantable td.banipcell {
		border-top: 0px !important;
		border-left: 0px !important;
	}
	#bantable td.banipcell small {
		color: {$style['TextColor']};
	}
/* Guard page: main table cell magic part 2 */
	#bantable td.banbtncell.active,
	#bantable td.bannamecell.active,
	#bantable td.banipcell.active {
		border-color: {$style['BanColor']};
		background-color: {$style['BanDarkColor']};
	}
/* Guard page: Make it all fit... */
	#banopttable {
		width: 174px;
	}
	#banopttable td {
		font-size: 10px;
	}
	#banopttable .textbox {
		width: 122px;
	}
	#banrefreshbtn, #banrefreshbtn_top, #bankickbtn {
		width: 172px;
	}
/* Guard page: List of active and lifted bans */
	.bannedstart {
		color: {$style['BanColor']};
	}
	.bannedend {
		color: {$style['TimeColor']};
	}
	.bannedreason {
		color: {$style['BanHiliteColor']};
	}
	.bannedlifted {
		color: {$style['BanLiftColor']};
		font-style: italic;
	}
/* Guard page: List of bans */
	.banlist {
		width: 174px !important;
		font-size: 77.5%;
		border-collapse: collapse;
	}
	.banlist td {
		vertical-align: top;
	}
	.banlist .l {
		text-align: right;
	}
	.banlist .t {
		white-space: nowrap;
	}
	.banlist th {
		border-top: 1px solid {$style['HRColor']};
	}

/* Control Panel Pages */
	.cpanel-wrapper {
		width: 660px;
		text-align: left;
		margin: auto;
	}

/* Control Panel Page: Settings */
	#cpanel-settings {
		font-size: 90%;
		border-collapse: collapse;
	}
	#cpanel-settings tr {
		border-top: 1px solid {$style['MultiChatBorder']};
	}
	#cpanel-settings th {
		color: {$style['HRColor']};
		font-size: 120%;
		border: 1px solid {$style['MultiChatBorder']};
	}
	#cpanel-settings .l {
		font-weight: bold;
		font-size: 105%;
	}
	#cpanel-settings .l span {
		font-weight: normal;
		font-size: 80%;
	}
/* Control Panel Page: Login Manager */
	#cpanel-login-list {
		font-size: 90%;
		border-collapse: collapse;
	}
	#cpanel-login-list tr {
		border-top: 1px solid {$style['MultiChatBorder']};
	}
	#cpanel-login-list th {
		color: {$style['HRColor']};
		font-size: 120%;
		border: 1px solid {$style['MultiChatBorder']};
	}

THESTYLESHEET;

// Look for a local stylesheet
	if(file_exists('local_style.css'))
		$css .= file_get_contents('local_style.css');

// Tack on our last-modified date
	$last_modified_date = getlastmod();
	$css = '/* Last Modified '
		 . gmdate("r", $last_modified_date)
		 . " */\n"
		 . $css;

// We'll use the checksum of the file as our ETag
	$etag = md5($css);
	$cached = false;
// Is the browser asking for our exact ETag?
	if($_SERVER['HTTP_IF_NONE_MATCH'])
		if($_SERVER['HTTP_IF_NONE_MATCH'] == $etag)
			$cached = true;

// Is the browser asking for the same exact modification time we have?
	if($_SERVER['HTTP_IF_MODIFIED_SINCE']) {
		$ifmodsince = strtotime($_SERVER['HTTP_IF_MODIFIED_SINCE']);
		if($ifmodsince == $last_modified_date)
			$cached = true;
	} // end if

// Can we 304 the user?
	if($cached) {
		header('HTTP/1.0 304 Not Modified', true, 304);
		header('Status: 304 Not Modified');
		exit;
	} // end if

// Emit cache control headers.  We *want* to be cached.
	header('Cache-Control: public');
	header('Last-Modified: ' . gmdate('r', $last_modified_date));
	header('ETag: ' . $etag);
	header('Content-type: text/css');
// Finally, spit out the style
	print $css;
	ob_flush();
