<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

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
