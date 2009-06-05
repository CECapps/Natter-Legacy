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
	// Certain things are hard-coded, do so now.
		$config['Script'] 			= 'chat3.cgi';
		$config['GuardScript'] 		= 'guard3.cgi';
		$config['CPanelScript']		= 'control3.cgi';
		$config['MessagesFN'] 		= 'messages';
		$config['MessagesFX']		= '.html';
		$config['DBFile']			= $config['DatabasePath']	. '/chat3.sqlite';
		$config['ScriptName'] 		= $config['CGIURL'] 		. "/" . $config['Script'];
		$config['GuardScriptName'] 	= $config['CGIURL'] 		. "/" . $config['GuardScript'];
		$config['CPanelScriptName']	= $config['CGIURL'] 		. "/" . $config['CPanelScript'];
		$config['MessagesFile'] 	= $config['NonCGIPath'] 	. "/" . $config['MessagesFN'] . $config['MessagesFX'];
		$config['MessagesName'] 	= $config['NonCGIURL'] 		. "/" . $config['MessagesFN'] . $config['MessagesFX'];
		$config['PostlogFile'] 		= $config['NonCGIPath'] 	. "/" . $config['MessagesFN'] . "_bans.cgi";
		if(isset($config['CSSFile']))
			$config['CSSName']		= $config['NonCGIURL'] 		. "/" . $config['CSSFile'];
	// Additional defaults will go here.  At time of writing of this comment,
	// any and all configuration directives will already have defaults, because
	// they are in the database.  Yay small beta audience.
		if(!isset($config['DBUser']))
			$config['DBUser'] = null;
		if(!isset($config['DBPassword']))
			$config['DBPassword'] = null;
		return $config;
	} // end getConfigWithDefaults

	public static function getConfigFromDatabase() {
		global $config, $dbh;
		$splice = $dbh->queryPairs('SELECT name,value FROM settings');
		$GLOBALS['config'] = array_merge($config, $splice);
		return Natter_Util::getConfigWithDefaults();
	} // end getConfigFromDatabase

} // end Natter_Util
