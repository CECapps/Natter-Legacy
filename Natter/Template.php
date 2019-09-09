<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

class Natter_Template {

    protected $config;

    protected $_data;
    protected $_filename;

    public function __construct($template_name) {
        global $config;
        $this->config = &$config;
        $filename = $config['NonCGIPath'] . '/templates/' . $template_name . '.phtml';
        if(!file_exists($filename))
            throw new Exception("Template '$template_name' not found.");
        $this->_filename = $filename;
    } // end __construct

    public function render() {
        ob_start();
        include $this->_filename;
        return ob_get_clean();
    } // end render

    public function raw($key)  {
        return $this->_data[$key];
    } // end raw

    public function __get($key) {
        return is_string($this->_data[$key]) ? htmlspecialchars($this->_data[$key]) : $this->_data[$key];
    } // end __get

    public function __set($key, $value) {
        $this->_data[$key] = $value;
    } // end __set

    public function __isset($key) {
        return isset($this->_data[$key]);
    } // end __isset

    public function __unset($key) {
        unset( $this->_data[$key] );
    } // end __unset

} // end Natter_Template
