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

	protected $saved;

/**
 * Constructor
 *
 * @param int $id Session ID
 * @return Natter_Session
 **/
	public function __construct($id = null) {
		if($id) {
			$this->retrieve($id);
			if(!$this->validate())
				$this->create();
		} // end if
	} // end __construct


/**
 * Create a new, clean session
 **/
	public function create() {
		$this->ip = Natter_Util::getIPAddress();
		$this->created = time();
		$this->updated = time();
		$this->kicked = 0;
		$this->data = array(
			'COPPA'			=> null,
			'password'		=> null,
			'entered'		=> null,
			'sanity'		=> null,
			'kick_by'		=> null,
			'kick_reason'	=> null,
			'guard'			=> null,
			'admin'			=> null
		);
		$this->saved = false;
		$this->recreateId();
	} // end create

/**
 * Recreate the Session ID
 **/
	public function recreateId() {
		$this->id = md5( mt_rand() . time() . getmypid() . mt_rand() );
		$this->saved = false;
	} // end recreateId

/**
 * Load session data from the database for the requested id
 *
 * @param string $id Session ID
 * @return bool
 **/
	public function retrieve($id) {
		global $dbh;
		$session_data = $dbh->queryAssoc('SELECT * FROM sessions WHERE id = ?', array( $id ));
		if(!$session_data || !is_array($session_data)) {
			$this->create();
			return false;
		} // end if
		$this->id = $session_data['id'];
		$this->ip = $session_data['ip'];
		$this->created = $session_data['created'];
		$this->updated = $session_data['updated'];
		$this->kicked = $session_data['kicked'];
		$this->data = Natter_Session::unserializeData($session_data['data']);
		$this->saved = true;
		return true;
	} // end retrieve

/**
 * Validate that this session has been loaded for the correct user
 *
 * @return bool
 **/
	public function validate() {
		$current_ip = preg_replace('/(\.\d+)$/', '', Natter_Util::getIPAddress());
		$last_ip = preg_replace('/(\.\d+)$/', '', $this->ip);
		return $current_ip == $last_ip;
	} // end validate

/**
 * Save this session to the database
 **/
	public function save() {
		global $dbh;
		$query = $this->saved
			? 'UPDATE sessions SET ip = ?, created = ?, updated = ?, kicked = ?, data = ? WHERE id = ?'
			: 'INSERT INTO sessions(ip, created, updated, kicked, data, id) VALUES(?, ?, ?, ?, ?, ?)';
		$dbh->query($query, array(
			$this->ip,
			$this->created,
			$this->updated,
			$this->kicked,
			Natter_Session::serializeData($this->data),
			$this->id
		));
		$this->saved = true;
	// Clean up after old sessions, 2% chance, 12 hour window.
		if(rand(0, 49) == 25) {
			$old_sessions = $dbh->queryCol('SELECT id FROM sessions WHERE updated < ?', array(time() - (60 * 60 * 12)));
			if(count($old_sessions)) {
				foreach($old_sessions as $old_session) {
					$dbh->query('DELETE FROM sessions WHERE id = ?', array($old_session));
					$dbh->query('UPDATE session_bans SET session_id = NULL WHERE session_id = ?', array($old_session));
				} // end foreach
			// Another 10% chance to clean up the database file
				if(rand(0, 9) == 5)
					$dbh->query('VACUUM');
			} // end if
		} // end if
	} // end save

/**
 * Enact a ban on this session
 *
 * @param string 	$banned_by 	User performing the ban
 * @param int 		$duration 	Length of ban, in seconds
 * @param string 	$reason 	Reason for the ban
 **/
	public function ban($banned_by = 'Auto', $duration = 300, $reason = '(unknown)') {
	// Session kicks only last twelve hours, max
		$twelve_hours = 60 * 60 * 12;
		if($duration > $twelve_hours)
			$duration = $twelve_hours;
	// Perform the actual kick
		$this->kicked = time() + $duration;
		$this->data['kick_by'] = $banned_by;
		$this->data['kick_reason'] = $reason;
		$this->save();
	} // end ban

/**
 * Lift a ban on this session
 **/
	public function unban() {
		$this->kicked = 0;
		$this->data['kick_by'] = null;
		$this->data['kick_reason'] = null;
		$this->save();
	} // end unban

/**
 * Determine if the current session is banned.
 *
 * @return int Duration of ban, or zero if not banned
 **/
	public function isBanned() {
	// Check to see if this session is kicked
		if($this->kicked < time())
			$this->kicked = 0;
		if($this->kicked)
			return $this->kicked;
	// The session hasn't been kicked.  Has our IP address been banned?
		require_once 'Natter/BanManager.php';
		$ban_info = Natter_BanManager::checkIPBan(Natter_Util::getIPAddress());
		if(!$ban_info || !count($ban_info) || !isset($ban_info['created']))
			return 0;
	// Oops, our IP address is banned.  Log the ban info.
		if($ban_info) {
			$this->kicked = $ban_info['created'] + $ban_info['duration'];
			$this->data['kick_by'] = $ban_info['created_by'];
			$this->data['kick_reason'] = $ban_info['reason'];
			$this->updated = time();
			$this->save();
		} // end if
		return $this->kicked;
	} // end isBanned


/**
 * Mark the current session as active
 **/
	public function markActive() {
		$this->ip = Natter_Util::getIPAddress();
		$this->updated = time();
		return true;
	} // end markActive


/**
 * Serialize the requested data, for storage in the shared session database
 *
 * @param array
 * @return string
 **/
	protected static function serializeData($data) {
		return json_encode($data);
	} // end serializeData

/**
 * Unserialize the requested data from the shared session database
 *
 * @param string
 * @return array
 **/
	protected static function unserializeData($data) {
		return (array)json_decode($data);
	} // end unserializeData

}
