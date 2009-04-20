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

package Natter::BanManager;
	use strict;
	use warnings;

# Cache / Singleton
	our $instance;

# Create a new instance
	sub new {
		return \$Natter::BanManager::instance if(defined $Natter::BanManager::instance);
		my $class = shift;
		my $options = {
			db => main::getDBHandle(),
		};
		my $self = bless($options, $class);
		$Natter::BanManager::instance = \$self;
		return $self;
	} # end new


# Return the database handle
	sub db { return \$_[0]->{db}; }


# Add a session ban
	sub addSessionBan {
		my $self = shift;
		my $session_id = shift;
		my $duration = shift;
		my $created_by = shift;
		my $reason = shift;
	# Load up the session
		my $session = new Session()->retrieve($session_id);
		return if(!$session);
	# Tell the session it's been banned
		$session->ban($created_by, $duration, $reason);
	# Record the ban in the log
		$self->db->do('
				INSERT INTO session_bans(session_id, created, duration, lifted, created_by, reason)
				VALUES(?, ?, ?, ?, ?, ?)
			',
			undef,
			$session_id,
			time(),
			$duration,
			time() + $duration,
			$created_by,
			$reason
		);
	} # end addSessionBan


# Add an IP ban
	sub addIPBan {
		my $self = shift;
		my $ip = shift;
		my $method = shift;
		my $duration = shift;
		my $created_by = shift;
		my $reason = shift;
	# What IP shall we ban?
		my $ip_method = $ip;
		if($method < 4) {
			my @ipb = split /\./, $ip;
			# method = 3 -> 0 .. 2; 4 - 3 = 1 -> 123.456.789.0
			# method = 2 -> 0 .. 1; 4 - 2 = 2 -> 123.456.0.0
			$ip_method = join('.', @ipb[0 .. ($method - 1)]) . ('.0' x (4 - $method));
		} # end if
		$self->db->do('
			INSERT INTO ip_bans(ip, created, duration, lifted, created_by, reason)
			VALUES(?, ?, ?, ?, ?, ?)
			',
			undef,
			$ip_method,
			time(),
			$duration,
			time() + $duration,
			$created_by,
			$reason
			);
	} # end addIPBan


# Lift an IP ban (by id)
	sub liftIPBan {
		my $self = shift;
		my $ban_id = shift;
		my $lifted_by = shift;
		$self->db->do('
			UPDATE ip_bans
			   SET lifted_by = ?,
			       lifted = ?
			 WHERE id = ?
			',
			undef,
			$lifted_by,
			time() - 1,
			$ban_id
			);
	} # end liftIPBan


# Clear an IP ban from the list (by id)
	sub clearIPBan {
		my $self = shift;
		my $ban_id = shift;
		my $cleared_by = shift;
		$self->db->do('
			UPDATE ip_bans
			   SET cleared_by = ?,
			       cleared = ?
			 WHERE id = ?
			',
			undef,
			$ban_id
		);
	} # end clearIPBan


# Check for an IP ban.  This method can be called statically.
# Returns info for the longest-running non-expired ban on this IP or IP range.
	sub checkIPBan {
		my $self = shift if(scalar @_ == 2);
		my $ip_address = shift if(scalar @_ == 1);
		my $db = $self ? $self->db() : main::getDBHandle();
	# Now, where were we?
		my @ip = split /\./, $ip_address;
		my $ip_3 = join('.', @ip[0,1,2]) . '.0';
		my $ip_2 = join('.', @ip[0,1]) . '.0.0';
		return $db->selectrow_hashref('
			SELECT *
			  FROM ip_bans
			 WHERE ip IN(?, ?, ?)
			       AND lifted >= ?
				   AND cleared > 0
			 ORDER BY duration DESC
			 LIMIT 1
			',
			undef,
			$ip_address, $ip_3, $ip_2,
			time()
		);
	} # end checkIPBan

1;
