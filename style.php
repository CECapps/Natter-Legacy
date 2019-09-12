<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

// This code was designed when Netscape 4 was a dominant browser, and CSS support
// in other browsers sucked.  Pardon the mess.  Refactoring can only do so much.

    header('Location: index.php?action=css&style=' . (isset($_GET['style']) ? $_GET['style'] : ''));
    exit;
