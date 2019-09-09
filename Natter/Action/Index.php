<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

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
    // Where's our messages.html?
        $template->messages_url = $config['IndexName'] . '?action=messages';

        $html = $template->render();
        $this->response->setBody($html);
        return;
    } // end run

}
