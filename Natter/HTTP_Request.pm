#!/usr/bin/perl
#
# Natter 4.10
# Copyright 1999-2009 Charles Capps
#
# This software is covered by a license agreement.
# If you do not have a license for this software, please
# contact <capps@solareclipse.net> immediately.
#
# Using this software without a valid license is a violation
# of the author's rights and is often illegal.
#
# Distribution of this script is stricly prohibited.
#
# Questions?  Comments?  <capps@solareclipse.net>

# Thinly wraps CGI.pm for slightly more modernly named methods.
package Natter::HTTP_Request;
	use lib '../ext', '..';
	use strict;
	use warnings;

	sub new { return bless({}, shift) }
	sub getParams { return scalar $main::cgi->Vars(); }
	sub getHeader { return $main::cgi->http($_[1]); }
# This is technically wrong, but we don't care about HEAD, PUT, etc.
	sub isGet { return $main::cgi->request_method() ne 'POST'; }
	sub isPost { return $main::cgi->request_method() eq 'POST'; }
