#!/usr/bin/perl

################################################################################
# This file is part of Natter, a legacy web chat in Perl and PHP.
# Copyright 1999-2019 Charles Capps <charles@capps.me>
#
# This software is covered by the license agreement in the LICENSE file.
# If the LICENSE file was not included, please contact the author.
################################################################################

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
	sub db { return $_[0]->{db}; }


# Add a session ban
	sub addSessionBan {
		my $self = shift;
		my $session_id = shift;
		my $duration = shift;
		my $created_by = shift;
		my $reason = shift;
	# Load up the session
		my $ban_session = new Natter::Session();
		my $session_loaded = $ban_session->retrieve($session_id);
		#use Data::Dumper;
		#die Dumper $ban_session;
		return if(!$session_loaded);
	# Tell the session it's been banned
		$ban_session->ban($created_by, $duration, $reason);
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


# Lift a Session ban (by id)
	sub liftSessionBan {
		my $self = shift;
		my $ban_id = shift;
		my $lifted_by = shift;
		$self->db->do('
			UPDATE session_bans
			   SET lifted_by = ?,
			       lifted = ?
			 WHERE id = ?
			',
			undef,
			$lifted_by,
			time() - 1,
			$ban_id
			);
	# Now, here's the fun part.  Does that ban still have a valid session id?
		my ($session_id,) = $self->db->selectrow_array('SELECT session_id FROM session_bans WHERE id = ?', undef, $ban_id);
		if($session_id) {
		# Yes, it does.  Pull up the session...
			my $banned_session = new Natter::Session();
			my $loaded = $banned_session->retrieve($session_id);
		# Now, if we can, unban it for real.
			$banned_session->unban() if($loaded);
		} # end if
	} # end liftSessionBan


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
			$cleared_by,
			time() - 1,
			$ban_id
		);
	} # end clearIPBan


# Clear a Session ban from the list (by id)
	sub clearSessionBan {
		my $self = shift;
		my $ban_id = shift;
		my $cleared_by = shift;
		$self->db->do('
			UPDATE session_bans
			   SET cleared_by = ?,
			       cleared = ?
			 WHERE id = ?
			',
			undef,
			$cleared_by,
			time() - 1,
			$ban_id
		);
	} # end clearSessionBan


# Check for an IP ban.  This method can be called statically.
# Returns info for the longest-running non-expired ban on this IP or IP range.
	sub checkIPBan {
		my $self = shift if(scalar @_ == 2);
		my $ip_address = shift if(scalar @_ == 1);
		$ip_address ||= '127.0.0.1';
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
				   AND cleared = 0
			 ORDER BY duration DESC
			 LIMIT 1
			',
			undef,
			$ip_address, $ip_3, $ip_2,
			time()
		);
	} # end checkIPBan


# Get a list of all bans as an arrayref
	sub getBanList {
		my $self = shift;
	# Grab the *entire* ban list at once.
		my $sth = $self->db->prepare(q~
			SELECT id, ip as token, 'ip' as token_type,
				   reason, created, duration, lifted, cleared, created_by, lifted_by, cleared_by
			  FROM ip_bans
		UNION -- this breaks under normal databases, heh, heh
			SELECT id, session_id as token, "session" as token_type,
				   reason, created, duration, lifted, cleared, created_by, lifted_by, cleared_by
			  FROM session_bans
			 ORDER BY created DESC
		~);
		my $res = $sth->execute();
		my @results;
	# Mutter mutter, why is there no selectall_arrayofhashrefs?
		while(my $row = $sth->fetchrow_hashref()) {
			$results[scalar @results] = $row;
		} # end while
		$sth->finish();
	# Refs are fun.
		return \@results;
	} # end getBanList

1;
