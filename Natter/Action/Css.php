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

class Natter_Action_Css implements Natter_Action {

	public $style = array();

/** @property Natter_HTTPRequest */
	protected $request;
/** @property Natter_HTTPResponse */
	protected $response;
/** @property Natter_Session */
	protected $session;

	public function __construct(Natter_HTTPRequest $request, Natter_HTTPResponse $response, Natter_Session $session) {
		/** @var Natter_HTTPRequest */
		$this->request = $request;
		/** @var Natter_HTTPResponse */
		$this->response = $response;
		/** @var Natter_Session */
		$this->session = $session;
	} // end __construct

	public function run() {
		global $config;
	// Okay, what color are we?
		$style_name = isset($_REQUEST['style']) ? $_REQUEST['style'] : 'bronze';
	// Render the CSS
		$template = new Natter_Template('css');
		$template->style = $this->getStyle($style_name);
		$css = $template->render() . "\n";
	// Attach any custom CSS
		$local_css = $config['NonCGIPath'] . '/local_style.css';
		if(file_exists($local_css))
			$css .= file_get_contents($local_css);
	// Change the output type and attach the CSS
		$this->response->setContentType('text/css');
		$this->response->setBody($css);
		return;
	} // end run

	public function getStyle($color = 'bronze') {
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
		if(!isset($styles[ $color ]))
			$color = 'bronze';
		return $styles[ $color ];
	} // end getStyle

}
