#!/usr/bin/perl

################################################################################
# This file is part of Natter, a legacy web chat in Perl and PHP.
# Copyright 1999-2019 Charles Capps <charles@capps.me>
#
# This software is covered by the license agreement in the LICENSE file.
# If the LICENSE file was not included, please contact the author.
################################################################################

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
			_headers => {
				'Content-Type' => 'text/html',
			},
			_status => 200,
			_status_message => '',
			_cookies => [],
			_body => '',
			_done => 0,
		};
		return bless($options, $class);
	} # end new


# Add a new cookie to be provided to the client.
# Works exactly like CGI::cookie(), 'cause it IS CGI::cookie()
	sub addCookie {
		my $self = shift;
		die 'Already produced output, can not add cookie ' if $self->{_done};
		$self->{_cookies}->[ scalar @{$self->{_cookies}} ] = scalar $main::cgi->cookie(@_);
	} # end addCookie


# Set the output content type.  Defaults to text/html
	sub setContentType {
		die 'Already produced output, can not set content type ' if $_[0]->{_done};
		$_[0]->{_headers}->{'Content-Type'} = $_[1];
	} # end setContentType


# Return the currently set content type.
	sub getContentType {
		return $_[0]->{_headers}->{'Content-Type'};
	} # end getContentType


# Set the HTTP status
	sub setHttpStatus {
		my $self = shift;
		$self->{_status} = shift;
		$self->{_status_message} = shift;
	} # end setHttpStatus


# Add a header to the output
	sub addHeader {
		die 'Already produced output, can not add header ' if $_[0]->{_done};
		$_[0]->{_headers}->{$_[1]} = $_[2];
	} # end addHeader


# Remove a header, preventing it from being provided during output.
	sub removeHeader {
		die 'Already produced output, can not remove header ' if $_[0]->{_done};
		delete $_[0]->{_headers}->{$_[1]};
	} # end addHeader


# Set the output body
	sub setBody {
		die 'Already produced output, can not set body ' if $_[0]->{_done};
		$_[0]->{_body} = $_[1];
	} # end addBody


# Append a string to the body.
	sub appendBody {
		die 'Already produced output, can not append to body ' if $_[0]->{_done};
		$_[0]->{_body} .= $_[1];
	} # end appendBody


# Clear the existing body
	sub clearBody {
		die 'Already produced output, can not clear body ' if $_[0]->{_done};
		$_[0]->{_body} = '';
	} # end clearBody


# Send stuff to the browser
	sub output {
		my $self = shift;
		die 'Already produced output, can not do it again ' if $self->{_done};
	# Prepare the HTTP headers. Content type is handled on its own by CGI.pm.
		my $content_type = $self->{_headers}->{'Content-Type'};
		delete $self->{_headers}->{'Content-Type'};
	# Set our own content length
		$self->{_headers}->{'Content-length'} = length $self->{_body};
	# Transform the headers into the format CGI.pm likes.
		my %headers = map { ('-' . $_) => $self->{_headers}->{$_} } keys %{$self->{_headers}};
	# Add the two expected paramaters regarldess of how many headers we have...
		$headers{'-type'} = $content_type;
		$headers{'-cookie'} = $self->{_cookies} if scalar @{$self->{_cookies}};
		$headers{'-status'} = $self->{'_status'};
	# Print the header and body
		print $main::cgi->header(%headers);
		print $self->{_body};
	# Prevent further output.
		$self->{_done} = 1;
	} # end output


# Can we send stuff to the browser?
	sub canOutput {
		return !$_[0]->{_done};
	} # end canOutput
1;
