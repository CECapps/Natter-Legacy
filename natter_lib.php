<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

// Yeah, it's stored here.
    global $VERSION, $VERSION_TAG;
    $VERSION = '5.1.2';
    $VERSION_TAG = '"Transmogrification"';

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
