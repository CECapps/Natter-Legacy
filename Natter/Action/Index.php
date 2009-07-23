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

class Natter_Action_Index implements Natter_Action {

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
		global $config, $session;
	// We use the "index" template.  Derf.
		$template = new Natter_Template('index');

	// Do we display a chat top frame?
		$template->show_chat_top = $config['ChatTopFrameHeight'] > 0 ? true : false;
		$template->chat_top_pixels = $config['ChatTopFrameHeight'];
	// Do we have a static HTML file for the chat top?
		$template->chat_top_file = file_exists($config['NonCGIPath'] . '/chattop.html') ? 'chattop.html' : 'index.php?action=chattop';
	// Are we dealing with an admin or guard?  They get the guard frameset.
		$template->is_guard = ($session->data['guard'] || $session->data['admin']) ? true : false;
		$template->guard_script_url = $config['GuardScriptName'] . '?action=list_users';

		$html = $template->render();
		$this->response->setBody($html);
		return;
	} // end run

}
