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

class Natter_Action_Logs implements Natter_Action {

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
		$frame = isset($_GET['frame']) ? $_GET['frame'] : null;
		switch($frame) {
			case 'left':
				$this->leftFrame();
				break;
			case 'right':
				$this->rightFrame();
				break;
			default:
				$this->frameset();
		}
		return;
	} // end run



	protected function frameset() {
		global $config, $session;
		$template = new Natter_Template('logs_frameset');
		$html = $template->render();
		$this->response->setBody($html);
		return;
	} // end run



	protected function leftFrame() {
		global $config;
	// So, we're going to grab the contents of the logs directory.
		$logs = new DirectoryIterator($config['LogsPath']);
		$filenames = array();
		foreach($logs as $file) {
			if(!$file->isFile())
				continue;
			if($file->isDot())
				continue;
			if($file->isDir())
				continue;
			$filename = $file->getFilename();
			if(preg_match('/^messages.+\.html$/', $filename))
				$filenames[] = $filename;
		} // end foreach
		unset($logs);
	// Sort the files, newest first.
		rsort($filenames);
	// We want the last seven days of activity, meaning we'll never have
	// more than 168 hours worth of files.  Each file is one hour.
		if(count($filenames) > 168)
			$filenames = array_slice($filenames, 0, 167);
	// Group the logs by date
		$by_date = array();
		foreach($filenames as $filename) {
			$matches = array();
			preg_match('/^' . $config['MessagesFN'] . '\-(\d\d\d\d\-\d\d\-\d\d)\-(\d\d)\.html$/', $filename, $matches);
			if(count($matches) < 3)
				continue;
			$by_date[ $matches[1] ][] = $matches[2];
		} // end foreach
	// Okay, let's template this thing.
		$template = new Natter_Template('logs_list');
		$template->files_by_date = $by_date;
		$this->response->setBody($template->render());
		return;
	} // end leftFrame



	protected function rightFrame() {
		global $config, $session;
	// Don't permit bogus dates
		$date = isset($_GET['date']) && preg_match('/^\d{4}\-\d\d-\d\d$/', $_GET['date']) ? $_GET['date'] : null;
		$hour = isset($_GET['hour']) && preg_match('/^\d\d$/', $_GET['hour']) ? $_GET['hour'] : null;
		if(is_null($date) && is_null($hour))
			throw new Natter_Error(array('Log Viewer', 'Please select a log from the left.'));
		if(is_null($date) || is_null($hour))
			throw new Exception('Invalid date or hour.');
	// Reassemble our log filename
		$filename = $config['LogsPath'] . '/' . $config['MessagesFN'] . '-' . $date . '-' . $hour . '.html';
		if(!file_exists($filename))
			throw new Exception('Log file not found.');
	// Iterate through the file, filtering in or out the IP addresses as req'd
		$find_ip = '/\<\!\-\- [\d\.]+ \-\-\>/';
		$replace_ip = '';
		if($session->data['admin'] || $session->data['guard']) {
			$find_ip = '/\<\!\-\- ([\d\.]+) \-\->/';
			$replace_ip = '<div class="log-ip">^^^ $1</div>';
		} // end if
		$this->response->setBody(preg_replace($find_ip, $replace_ip, file_get_contents($filename)));
	} // end rightFrame


}
