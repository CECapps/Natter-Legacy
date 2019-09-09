<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

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
    require_once 'Natter/Error.php';
    $request = new Natter_HTTPRequest();
    $response = new Natter_HTTPResponse();
// Initiate our session
    $session_id = $request->getCookie($config['CookiePrefix'] . '_session');
    $session = new Natter_Session($session_id);
// Is this a new session?  If so, we need to cookienate.
    if(!$session_id || $session->id != $session_id) {
        $session->save();
        $response->addCookie($config['CookiePrefix'] . '_session', $session->id);
    } // end if
// Okay, if we managed to get this far, we can install our exception handler.
    set_exception_handler('natter_global_exception_handler');

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

// Handle unhandled exceptions.
    function natter_global_exception_handler(Exception $e) {
        global $response, $request, $session, $pwd;
        $response->reset();
        require_once $pwd . '/Natter/Action/Error.php';
        $standardhtml = new Natter_Action_Error($request, $response, $session);
        $standardhtml->run($e);
        $response->output();
    } // end natter_global_exception_handler
