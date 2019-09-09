<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

class Natter_Util {

    public static function getConfigWithDefaults() {
        global $config;
        $config['ChatTopFrameHeight'] = isset($config['ChatTopFrameHeight']) ? $config['ChatTopFrameHeight'] : 65;
    // Certain things are hard-coded, do so now.
        $config['Index']			= 'index.php';
        $config['Script'] 			= 'chat3.cgi';
        $config['GuardScript'] 		= 'guard3.cgi';
        $config['CPanelScript']		= 'control3.cgi';
        $config['MessagesFN'] 		= 'messages';
        $config['MessagesFX']		= '.html';
        $config['DBFile']			= $config['DatabasePath']	. '/chat3.sqlite';
        $config['IndexName'] 		= $config['CGIURL'] 		. "/" . $config['Index'];
        $config['ScriptName'] 		= $config['CGIURL'] 		. "/" . $config['Script'];
        $config['GuardScriptName'] 	= $config['CGIURL'] 		. "/" . $config['GuardScript'];
        $config['CPanelScriptName']	= $config['CGIURL'] 		. "/" . $config['CPanelScript'];
        $config['MessagesFile'] 	= $config['NonCGIPath'] 	. "/" . $config['MessagesFN'] . $config['MessagesFX'];
        $config['MessagesName'] 	= $config['IndexName'] 		. '?action=messages&';
        $config['PostlogFile'] 		= $config['NonCGIPath'] 	. "/" . $config['MessagesFN'] . "_bans.cgi";
        if(isset($config['StyleNumber']))
            $config['CSSName']              = $config['IndexName']          . '?action=css&style=' . $config['StyleNumber'];
        if(!isset($config['CSSName']))
            $config['CSSName']		= $config['IndexName'] 		. '?action=css';
    // Additional defaults will go here.  At time of writing of this comment,
    // any and all configuration directives will already have defaults, because
    // they are in the database.  Yay small beta audience.
        if(!isset($config['DBUser']))
            $config['DBUser'] = null;
        if(!isset($config['DBPassword']))
            $config['DBPassword'] = null;
    // PHP configuration sucks.
        if(isset($config['TimeZoneCode']))
            date_default_timezone_set($config['TimeZoneCode']);
        return $config;
    } // end getConfigWithDefaults

    public static function getConfigFromDatabase() {
        global $config, $dbh;
        $splice = $dbh->queryPairs('SELECT name,value FROM settings');
        $GLOBALS['config'] = array_merge($config, $splice);
        return Natter_Util::getConfigWithDefaults();
    } // end getConfigFromDatabase


/**
 * Get the IP address for the current request.  Hmm, this should be in the Request object.
 * #FIXME
 *
 * @return string
 **/
    public static function getIPAddress() {
        global $config;
    // Obvious, right?
        $ip = isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '127.0.0.1';
    // But if the user came here through a proxy, and we trust proxies, use the header instead.
        if(isset($_SERVER['HTTP_X_FORWARDED_FOR']) && $config['CheckProxyForward'])
            $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
        return $ip;
    } // end getIPAddress

} // end Natter_Util
