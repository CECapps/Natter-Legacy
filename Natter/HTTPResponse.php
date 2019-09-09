<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

// This class is a direct port of the Perl code, and thus may not make a great
// deal of sense in the context of PHP, where we have output buffering and whatnot.
class Natter_HTTPResponse {

    private $headers = array(
        'Content-type' => 'text/html'
    );
    private $cookies = array();
    private $body = '';
    private $done = false;
    private $status = null;
    private $status_wording = null;

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

// Set the HTTP status
    public function setHttpStatus($status_code, $status_wording) {
        if(!$this->canOutput()) trigger_error('Can not set the HTTP status code, already posted output', E_USER_ERROR);
        $this->status = $status_code;
        $this->status_wording = $status_wording;
    } // end setHttpStatus

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
    public function clearBody() {
        $this->body = '';
        $this->done = headers_sent();
    } // end appendBody

// Can we send stuff to the browser?
    public function canOutput() {
        return !$this->done || !headers_sent();
    } // end canOutput

// Reset ourselves to a default stat
    public function reset() {
        $this->headers = array();
        $this->cookies = array();
        $this->body = '';
        $this->done = false;
    } // end reset

// Send stuff to the browser
    public function output() {
        if($this->done)
            trigger_error('Can not send body, already posted output', E_USER_ERROR);
        if(headers_sent() && (count($this->headers) || count($this->cookies)))
            trigger_error('Can not send body, already sent headers', E_USER_ERROR);
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
        if($this->status) {
            header('HTTP/1.0 ' . $this->status . ' ' . $this->status_wording);
            header('Status: ' .  $this->status . ' ' . $this->status_wording);
        } // end if
        foreach($this->headers as $header => $value)
            header($header . ': ' . $value);
    // And the cookies
        foreach($this->cookies as $name => $cookie)
            setcookie($name, $cookie['value'], $cookie['expires'], '/');
    // Print the body and mark the body as sent.
        echo $this->body;
        $this->done = true;
        @ob_end_flush();
        return true;
    } // end output

} // end Natter_HTTPResponse
