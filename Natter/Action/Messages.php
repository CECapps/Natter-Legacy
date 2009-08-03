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

class Natter_Action_Messages implements Natter_Action {

/** @property Natter_HTTPRequest */
	protected $request;
/** @property Natter_HTTPResponse */
	protected $response;
/** @property Natter_Session */
	protected $session;

	public function __construct(Natter_HTTPRequest $request, Natter_HTTPResponse $response, Natter_Session $session) {
		$this->request = $request;
		$this->response = $response;
		$this->session = $session;
	} // end __construct


	public function run() {
		global $config;
	// Fetch our message file info
		$lines = $this->getMessageLines();
		$this->response->addHeader('Last-Modified', date(DATE_RFC1123, $lines['newest_timestamp']));

// Did we get an If-Modified-Since?
		$ims = $this->request->getHeader('If-Modified-Since');
		if($ims && !isset($_REQUEST['newer_than'])) {
			$ims = strtotime($ims);
			if(isset($ims) && $ims - $lines['newest_timestamp'] == 0) {
			// The requested timestamp is still our max, no need to reutrn data.
				$this->response->setHttpStatus(304, 'Not Modified');
				return;
			} // end if
		} // end if

	// Otherwise, let's prepare the newer lines.
		$newer_than = array();
		$newest = 0;
		foreach($lines as $message_id => $line) {
			if(!is_numeric($message_id))
				continue;
			if($message_id > $newest)
				$newest = $message_id;
			if(isset($_REQUEST['newer_than']) && $message_id > $_REQUEST['newer_than'])
				$newer_than[ $message_id ] = $line;
		} // end foreach

	// If we aren't getting a request for a line-newer-than, let's just spit out the page.
		if(!isset($_REQUEST['newer_than'])) {
			$template = new Natter_Template('messages_frame');
			$template->lines = $lines;
			$template->newest_id = $newest;
			$this->response->setBody($template->render());
			return;
		} // end if

	// We need to wrap the message list to get sane JSON results...
		$json_messages = array();
		foreach($newer_than as $k => $v) {
			$json_messages[] = array(
				'message_id' => $k,
				'html' => $v
			);
		} // end foreach
		$json_messages = array_reverse($json_messages);

	// Now spit it back out as JSON
		$this->response->setContentType('text/javascript');
		$this->response->setBody(json_encode(array( 0 => count($newer_than), $newest, $json_messages )));
		return;
	} // end run



/**
 * Parse the messages file data, extracting the header, footer, message IDs, etc.
 *
 * @return array
 **/
	protected function getMessageLines() {
		$file_contents = $this->readMessagesFile();
		$lines = array( 'head' => $file_contents[0] );
		$newest_timestamp = 0;
		foreach($file_contents as $line) {
			$matches = array();
			if(preg_match('/^<div class="messageline" data-timestamp="(\d+)" id="message-(\d+)"> /', $line, $matches)) {
				$lines[ $matches[2] ] = $line;
				if($matches[1] > $newest_timestamp)
					$newest_timestamp = $matches[1];
			} // end if
		} // end foreach
		$lines['foot'] = $file_contents[ (count($file_contents) - 1) ];
		$lines['newest_timestamp'] = $newest_timestamp;
		return $lines;
	} // end getMessages


/**
 * Read the messages.html file into an array.  This function exists only because
 * the built-in file() function does not use flock().
 *
 * @return array
 **/
	protected function readMessagesFile() {
		global $config;
		$file_contents = array();
		$fh = fopen($config['MessagesFile'], 'r');
		if(!$fh)
			return $file;
		flock($fh, LOCK_SH);
		while(!feof($fh)) {
			$line = trim(fgets($fh));
			if($line)
				$file_contents[] = $line;
		} // end while
		fclose($fh);
		return $file_contents;
	} // end readMessagesFile

}
