<?php
/*******************************************************************************
 * This file is part of Natter, a legacy web chat in Perl and PHP.
 * Copyright 1999-2019 Charles Capps <charles@capps.me>
 *
 * This software is covered by the license agreement in the LICENSE file.
 * If the LICENSE file was not included, please contact the author.
 ******************************************************************************/

interface Natter_Action {
    public function __construct(Natter_HTTPRequest $request, Natter_HTTPResponse $response, Natter_Session $session);
    public function run();
}
