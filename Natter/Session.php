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

class Natter_Session {

	public $id;
	protected $dbh;

	public $ip;
	public $created;
	public $updated;
	public $kicked;
	public $data = array();

	public function __construct($id, Natter_PDO $dbh) {}
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
