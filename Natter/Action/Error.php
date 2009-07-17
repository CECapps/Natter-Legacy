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

class Natter_Action_Error implements Natter_Action {

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

	public function run($exception_or_title = null, $description = null) {
		if(is_object($exception_or_title) && !( $exception_or_title instanceof Natter_Error ) && $exception_or_title instanceof Exception)
			$this->handleException($exception_or_title);
		elseif(is_object($exception_or_title) && $exception_or_title instanceof Natter_Error )
			$this->handleMessage($exception_or_title->getTitle(), $exception_or_title->getMessage());
		else
			$this->handleMessage($exception_or_title, $description);
	} // end run

	protected function handleException($e) {
		$this->handleMessage(
			'Application Error',
			// 'Oops!  The code malfunctioned, and it\'s all your fault!'
			// . ' The error is: '
			$e->getMessage()
		);
	} // end handleException

	protected function handleMessage($title = 'Oh My, an Error!', $description = 'Yeah, something went so wrong that you get to see the default error message.  Congrats, you really busted it this time.') {
		$template = new Natter_Template('standard_html');
		$template->header = $title;
		$template->body = $description;
		$template->footer = '';
		$this->response->setBody($template->render());
	} // end handleMessage

}
