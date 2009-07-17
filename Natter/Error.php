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

class Natter_Error extends Exception {

	protected $_title = 'Error';

// We can take an array for the message.
	public function __construct($message, $code = null) {
		if(is_array($message)) {
			$this->_title = $message[0];
			$message = $message[1];
		} // end if
		parent::__construct($message, $code);
	} // end __construct

	public function getTitle() {
		return $this->_title;
	} // end getTitle

}
