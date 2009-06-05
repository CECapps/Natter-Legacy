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
// deal of sense in the context of PHP, where we have output buffering and whatnot.
class Natter_HTTPResponse {

	private $headers = array(
		'Content-type' => 'text/html'
	);
	private $cookies = array();
	private $body = '';
	private $done = false;

// Fire up output buffering, though this honestly should be done by the caller.
	public function __construct() {
		ob_start();
	} // end __construct

// Wrapper for setcookie()
	public function addCookie($name, $value, $expires_in_seconds = null) {
		if(!$this->canOutput()) trigger_error('Can not add cookie, already posted output', E_USER_ERROR);
		$this->cookies[ $name ] = array(
			'value' => $value,
			'expires' => $expires_in_seconds
		);
		return true;
	} // end addCookie

// Set the content type, defaults to text/html
	public function setContentType($mime_type) {
		if(!$this->canOutput()) trigger_error('Can not set content type, already posted output', E_USER_ERROR);
		$this->headers['Content-type'] = $mime_type;
	} // end setContentType

// Return the current content type
	public function getContentType() {
		return $this->headers['Content-type'];
	} // end getContentType

// Add an HTTP header
	public function addHeader($header, $value) {
		if(!$this->canOutput()) trigger_error('Can not add an HTTP header, already posted output', E_USER_ERROR);
		$this->headers[$header] = $value;
	} // end addHeader

// Remove an HTTP header, preventing it from being set during output
	public function removeHeader($header) {
		if(!$this->canOutput()) trigger_error('Can not remove an HTTP header, already posted output', E_USER_ERROR);
		$this->headers[$header] = '';
	} // end removeHeader

// Set the output body
	public function setBody($string) {
		if(!$this->canOutput()) trigger_error('Can not set body, already posted output', E_USER_ERROR);
		$this->body = $string;
	} // end setBody

// Append a string to the body
	public function appendBody($string) {
		if(!$this->canOutput()) trigger_error('Can not append to body, already posted output', E_USER_ERROR);
		$this->body .= $string;
	} // end appendBody

// Clear the existing body and reset the sent status, if we can
	public function clearBody($string) {
		$this->body = '';
		$this->done = headers_sent();
	} // end appendBody

// Can we send stuff to the browser?
	public function canOutput() {
		return !$this->done || !headers_sent();
	} // end canOutput

// Send stuff to the browser
	public function output() {
		if($this->done) trigger_error('Can not send body, already posted output', E_USER_ERROR);
		if(headers_sent()) trigger_error('Can not send body, already sent headers', E_USER_ERROR);
	// Grab the output buffer and add it to the body.  Note that we're doing a
	// manual calculation of the content length.  The original intent of the
	// native Perl code did this because Perl's CGI.pm didn't, and users were
	// reporting very, very weird problems that all had to with missing content
	// lengths.  Technically, this entire class just exists to bring output
	// buffering to the original Perl code.  It's being kept because the next
	// steps in the port are a "quick and dirty" port of the Perl code to PHP,
	// in which I'd rather not have to rethink the entire design of the code.
	// This class (and HTTPRequest) will probably be refectored out of existence
	// at some point or another before the public release.
		$this->body .= ob_get_clean();
		$this->addHeader('Content-length', strlen($this->body));
	// Throw out the headers
		foreach($this->headers as $header => $value)
			header($header . ': ' . $value);
	// And the cookies
		foreach($this->cookies as $name => $cookie)
			setcookie($name, $cookie['value'], $cookie['expires']);
	// Print the body and mark the body as sent.
		echo $this->body;
		$this->done = true;
		ob_end_flush();
		return true;
	} // end output

} // end Natter_HTTPResponse
