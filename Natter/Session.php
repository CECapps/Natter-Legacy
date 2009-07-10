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

// Yet another direct translation from the Perl codebase.  Again, because Perl
// lacks built-in session management, I had to roll something custom.  Unlike
// the Request/Response, this one is likely to stick around long-term.  Banning
// people's sessions, etc, is done by actually loading up the session data.
// That isn't something that the PHP session system allows in any sane way.
// Additionally, with this system it's possible to query based on session
// paramaters, which also isn't possible in the native PHP system.  I'd use the
// native system and just store the data in the shared database, but the PHP
// session saivng mechanism is so far beyond retarded that I have no appropriate
// words to express my severe discontent.  WHY ARE YOU GIVING ME THE PRE-SERIALIZED
// DATA INSTEAD OF THE ACTUAL DATA SO I CAN DO SOMETHING USEFUL WITH IT?  ARGH!
class Natter_Session {

	public $id;

	public $ip;
	public $created;
	public $updated;
	public $kicked;
	public $data = array();

	public function __construct($id) {
		$this->id = $id;
	}
	public function create() {}
	public function recreateId() {}
	public function retrieve($id) { return true; }
	public function validate() { return true; }
	public function save() {}
	public function ban($banned_by, $duration, $reason) {}
	public function unban() {}
	public function isBanned() { return false; }
	public function markActive() {}

	protected function serializeData() {}
	protected function unserializeData() {}

}
