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

// Set up the environment
	error_reporting(E_ALL | E_STRICT);
	ini_set('display_errors', true);
    $pwd = realpath(dirname(__FILE__));
    set_include_path($pwd . '/Natter' . PATH_SEPARATOR
                     . get_include_path());

// Pull in the main library, which pulls in our configuration
	global $config, $dbh;
	require_once 'natter_lib.php';

// Prepare our Request, Response, Session, etc
	require_once 'Natter/HTTPRequest.php';
	require_once 'Natter/HTTPResponse.php';
	require_once 'Natter/Session.php';
	require_once 'Natter/Action.php';
	require_once 'Natter/Template.php';
	$request = new Natter_HTTPRequest();
	$response = new Natter_HTTPResponse();
	$session_id = $request->getCookie($config['CookiePrefix'] . '_session');
	$session = new Natter_Session($session_id);

// If we were more complex, the router bits would go here.  Because we're simple
// and stupid, we can fall back to poking at $_REQUEST['action']
	$default_action = 'index';
	$user_action = isset($_REQUEST['action']) ? $_REQUEST['action'] : $default_action;
	$user_action = preg_replace('/[^a-z0-9_-]/', '', strtolower($user_action));
	$filename = 'Action/' . ucfirst($user_action) . '.php';
	if(!file_exists($pwd . '/Natter/' . $filename)) {
		$user_action = $default_action;
		$filename = 'Action/' . ucfirst($user_action) . '.php';
	} // end if
	$action_class = 'Natter_Action_' . ucfirst($user_action);
	require_once $filename;

// Okay, we now have our action, let's do something with it!
	$action = new $action_class($request, $response, $session);
	$action->run();

// The action should have populated the response...
	if($response->canOutput())
		$response->output();
	exit;
