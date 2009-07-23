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
		$config['MessagesName'] 	= $config['NonCGIURL'] 		. "/" . $config['MessagesFN'] . $config['MessagesFX'];
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
