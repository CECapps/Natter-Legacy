<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

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
