#!/usr/bin/perl

################################################################################
# This file is part of Natter, a legacy web chat in Perl and PHP.
# Copyright 1999-2019 Charles Capps <charles@capps.me>
#
# This software is covered by the license agreement in the LICENSE file.
# If the LICENSE file was not included, please contact the author.
################################################################################

# Thinly wraps CGI.pm for slightly more modernly named methods.
package Natter::HTTP_Request;
	use lib '../ext', '..';
	use strict;
	use warnings;

	sub new { return bless({}, shift) }
	sub getParams { return $main::cgi->Vars(); }
	sub getHeader { return $main::cgi->http($_[1]); }
	sub getCookie { return $main::cgi->cookie($_[1]); }
# This is technically wrong, but we don't care about HEAD, PUT, etc.
	sub isGet { return $main::cgi->request_method() ne 'POST'; }
	sub isPost { return $main::cgi->request_method() eq 'POST'; }
	sub isAjax { return ($_[0]->getHeader('X-Requested-With') eq 'XMLHttpRequest' || $main::cgi->param('ajax_api')) ? 1 : 0 }

1;
