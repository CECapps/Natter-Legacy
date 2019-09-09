<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

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
