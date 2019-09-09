<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

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
