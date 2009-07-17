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

// Yeah, it's stored here.
	global $VERSION, $VERSION_TAG;
	$VERSION = '5.0.0';
	$VERSION_TAG = '"Trespass"';

// What's our configuration look like?
	global $config;
	require_once 'config.inc.php';

// Load the various utility classes
	require_once 'Natter/Util.php';
	require_once 'Natter/PDO.php';

// Connect to the database and retrieve the configuration
	$config = Natter_Util::getConfigWithDefaults();
	$dsn = 'sqlite:' . $config['DBFile'];
	$driver_options = array();
	$dbh = new Natter_PDO($dsn, $config['DBUser'], $config['DBPassword'], $driver_options);
	$dbh->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_WARNING);
	$config = Natter_Util::getConfigFromDatabase();
