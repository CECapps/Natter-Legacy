<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

class Natter_Action_Session implements Natter_Action {

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

        // "sanity" is set to the string literal '1' (boolean true) when the user requests action=intro, and is checked
        // on following requests.  If the user never hits action=intro, requests to action=post are rejected.
        // API clients should GET chat3 action=intro in response to this being false.
        $is_valid = (bool)$this->session->data['sanity'];

        // "COPPA" is set to the string literal 'over' when the user clicks through the age warning.
        // It will be set to string literal 'under' if they click through to the underage page instead.
        // COPPA=under will cause chat3 to reject *ALL* user requests.  Yikes!  What the hell was I thinking?
        // API clients should POST chat3 action=coppa check=over in response to this being true.
        $needs_age_check = $config['COPPAAge'] > 0 && !($this->session->data['COPPA'] == 'over');

        // "password" will be set to the string literal contained in the ChatPassword configuration value if and only
        // if the configuration is non-empty and the user has already validated it.  If there is no password, then
        // the configuration value will be empty and the session value will be null, allowing == to match.
        // API clients should POST chat3 action=password_check password=... in response to this being true.
        $needs_password = !($this->session->data['password'] == $config['ChatPassword']);

        // The first redirect of the user to the empty chat form (action=post) includes the query string param
        // special=entrance.  When this is set, action=post will create a special "the user has entered the chat"
        // message and post it, then set session data 'entered' to the string literal '1' (boolean true).  Guards and
        // admins are excluded from this feature.  As all admins are guards, we only check the guard status.
        // API clients should POST chat3 action=post special=entrance in response to this being true.
        $needs_entry = (strlen($this->session->data['guard']) == 0) && !(bool)$this->session->data['entered'];

        // "guard" will be set to the string guard login name if the user has authenticated with the guard script, or
        // if the user is an admin and has authenticated with the control panel script.
        $is_guard = strlen($this->session->data['guard']) > 0;

        // "admin" will be set to the string admin name if the user has authenticated with the control panel script.
        $is_admin = strlen($this->session->data['admin']) > 0;

        // There are two ban levels - session, and IP.  Session bans ("kicks") are recorded in session data, under the
        // top level session key 'kicked', and by the two data keys 'kick_by' and 'kick_reason'.  IP bans are recorded
        // in the database.  Every request to chat3 checks the IP ban list and will recorded ban data in the session
        // if req'd.  Users can go quite a while between chat3 requests, so we'll just check and update it now.
        // session->kicked is the unixtime of the ban ending.
        // 'kick_by' is the string guard login name of the banning guard, which we will not use here.
        // 'kick_reason' is the string ban reason entered by the banning guard.
        // API clients that get is_kicked=true should present the kick_reason to the user and not issue any calls to
        // chat3 until the ban has been lifted.  chat3 will not provide well-formed API responses to banned users.
        $kick_expires = $this->session->isBanned();
        $is_kicked = $kick_expires > 0;
        if (!$is_kicked) {
            $kick_expires = null; //  it'll be zero otherwise, which is inconsistent with the other values
        }
        $kick_reason = $is_kicked ? $this->session->data['kick_reason'] : null;

        // As mentioned above, if the user indicates that they're underage, chat3 will actively reject all subsequent
        // requests with a "go away" message.  Rather than build an entirely separate mechanism to tell the user, let's
        // hikack the kick reason.  Nothing could possibly go wrong with this plan.
        if(!$is_kicked && $config['COPPAAge'] > 0 && $this->session->data['COPPA'] == 'under') {
            $is_kicked = true;
            $kick_expires = strtotime('now + 12 hours'); // session length
            $kick_reason = 'Sorry, those under the age of ' . $config['COPPAAge'] . ' may not chat here.';
        }

        $session_data = [
            'is_valid'          => $is_valid,
            'needs_age_check'   => $needs_age_check,
            'needs_password'    => $needs_password,
            'needs_entry'       => $needs_entry,
            'is_guard'          => $is_guard,
            'is_admin'          => $is_admin,
            'is_kicked'         => $is_kicked,
            'kick_expires'      => $kick_expires,
            'kick_reason'       => $kick_reason,
            // '_data' => $this->session
        ];

        $this->response->setContentType('application/javascript');
        $this->response->setBody(json_encode($session_data, \JSON_PRETTY_PRINT));
        return;
    } // end run

}
