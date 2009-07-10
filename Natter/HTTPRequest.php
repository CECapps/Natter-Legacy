<?php
/**
 * Natter 5.0
 * Copyright 1999-2009 Charles Capps
 *
 * This software is covered by a license agreement.
 * If you do not have a license for this software, please
 * contact <capps@solareclipse.net> immediately.
 *
 * Using this software without a valid license is a violation
 * of the author's rights and is often illegal.
 *
 * Distribution of this script is stricly prohibited.
 *
 * Questions?  Comments?  <capps@solareclipse.net>
 **/

// This class is a direct port of the Perl code, and thus may not make a great
// deal of sense in the context of PHP, where things like getting all the script
// paramaters is already done.  It's also complicated because PHP doesn't expose
// the actual HTTP headers that generated the request.
class Natter_HTTPRequest {

// Shouldn't really need these two in PHP code.
	public function getParams() { return $_REQUEST; }
	public function getCookie($cookie) { return isset($_COOKIE[$cookie]) ? $_COOKIE[$cookie] : null; }

// Erk, why does PHP make me do this?
	public function getHeader($header) {
		$header = strtr(strtoupper($header), '-', '_');
		return isset($_SERVER['HTTP_' . $header]) ? $_SERVER['HTTP_' . $header] : false;
	} // end getHeader

// These are technically wrong, but we don't care about HEAD, PUT, etc.
	public function isGet() { return $_SERVER['REQUEST_METHOD'] != 'POST'; } 
	public function isPost() { return $_SERVER['REQUEST_METHOD'] != 'GET'; } 

// Check for signs of ajaxness.  Certain actions work differently if they're
// being requested via ajax instead of by direct request.
	public function isAjax() {
		if(isset($_SERVER['HTTP_X_REQUESTED_WITH']))
			if($_SERVER['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest')
				return true;
		if(isset($_REQUEST['ajax_api']))
			if($_REQUEST['ajax_api'] == 1)
				return true;
		return false;
	} // end isAjax


} // end Natter_HTTPRequest