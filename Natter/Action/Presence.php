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

class Natter_Action_Presence implements Natter_Action {

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
		$do = isset($_REQUEST['do']) ? $_REQUEST['do'] : '';
		switch($do) {
			case 'set':
				$this->setPresenceInfo();
				break;
			case 'get':
				$this->getPresenceInfo();
				break;
			default:
				$this->getPrettyFrame();
				break;
		} // end switch
	} // end run


	public function setPresenceInfo() {
		$this->response->setContentType('text/javascript');
		$this->response->setBody(json_encode(array(
			'status' => 'ok'
		)));
	} // end setPresenceInfo


	public function getPresenceInfo() {
		$this->response->setContentType('text/javascript');
		$this->response->setBody(json_encode(array(
			'presence_data' => array(),
			'presence_html' => '<b>This is the HTML!</b>'
		)));
	} // end getPresenceInfo


	public function getPrettyFrame() {
		global $config, $session;
		$template = new Natter_Template('presence_frame');
		$this->response->setBody($template->render());
	} // end getPrettyFrame

}
