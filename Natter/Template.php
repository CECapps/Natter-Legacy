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

class Natter_Template {

	protected $_data;
	protected $_filename;

	public function __construct($template_name) {
		global $config;
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
		return htmlspecialchars($this->_data[$key]);
	} // end __get

	public function __set($key, $value) {
		$this->_data[$key] = $value;
	} // end __set

} // end Natter_Template
