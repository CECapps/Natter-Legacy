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

class Natter_Action_Chattop implements Natter_Action {

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
	// We use the "chattop" template.  Herf.
		$template = new Natter_Template('chattop');

		$html = $template->render();
		$this->response->setBody($html);
		return;
	} // end run

}