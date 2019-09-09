<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

class Natter_Action_Css implements Natter_Action {

    public $style = array();

/** @property Natter_HTTPRequest */
    protected $request;
/** @property Natter_HTTPResponse */
    protected $response;
/** @property Natter_Session */
    protected $session;

    public function __construct(Natter_HTTPRequest $request, Natter_HTTPResponse $response, Natter_Session $session) {
        /** @var Natter_HTTPRequest */
        $this->request = $request;
        /** @var Natter_HTTPResponse */
        $this->response = $response;
        /** @var Natter_Session */
        $this->session = $session;
    } // end __construct

    public function run() {
        global $config;
    // Okay, what color are we?
        $style_number = isset($_REQUEST['style']) ? $_REQUEST['style'] : 1;
    // Render the CSS
        $template = new Natter_Template('css');
        $template->style = $this->getStyle($style_number);
        $css = $template->render() . "\n";
    // Attach any custom CSS
        $local_css = $config['NonCGIPath'] . '/local_style.css';
        if(file_exists($local_css))
            $css .= file_get_contents($local_css);
    // Change the output type and attach the CSS
        $this->response->setContentType('text/css');
        $this->response->setBody($css);
        return;
    } // end run

    public function getStyle($number = 1) {
        global $dbh;
        return $dbh->queryPairs('SELECT name, value FROM style_values WHERE style_id = ?', array( $number ));
    } // end getStyle

}
