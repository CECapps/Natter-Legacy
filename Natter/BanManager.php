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

// This'll get fleshed out more once the guard screen is ported.
class Natter_BanManager {

	public static function checkIPBan($ip_address = '127.0.0.1') {
		global $dbh;
		$ip_splode = explode('.', $ip_address);
		$ip_3 = join('.', $ip[0], $ip[1], $ip[2], 0);
		$ip_3 = join('.', $ip[0], $ip[1], 0,      0);
		$dbh->queryAssoc('
			SELECT *
			  FROM ip_bans
			 WHERE ip IN(?, ?, ?)
			       AND lifted >= ?
				   AND cleared > 0
			 ORDER BY duration DESC
			 LIMIT 1
		',
		array($ip_address, $ip_3, $ip_2, time())
		);
	} // end checkIPBan

}
