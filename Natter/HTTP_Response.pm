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

# Wrap up all script output (headers, etc), in a nice little package.
# The goal is to maintain control of the output stream so that Content-Length
# can be set, among other things.  The goal of that goal is to stop Leo from
# getting download prompts.  What the hell, Leo, what the hell.
package Natter::HTTP_Response;
	use lib '../ext', '..';
	use strict;
	use warnings;

	sub new {
		my $class = shift;
		my $options = {
			headers => [],
			cookies => [],
			body => '',
		};
	} # end new

	sub addCookie {}

	sub setContentType {}
	sub getContentType {}

	sub addHeader {}
	sub removeHeader {}

	sub addBody {}
	sub appendBody {}
	sub clearBody {}

	sub output {}
