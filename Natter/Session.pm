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

package Natter::Session;
	use lib '../ext', '..';
	use strict;
	use warnings;
	use Digest::MD5;
	use JSON::PP;
	use Natter::BanManager;

# Create and return a new object
	sub new {
		my $class = shift;
		my $session_id = shift;
		my $options = {
			_db => main::getDBHandle(),
		};
		my $self = bless($options, $class);
		return $self;
	} # end new


# Create a new, clean session
	sub create {
		my $self = shift;
		$self->{ip} = main::currentIP();
		$self->{created} = time();
		$self->{updated} = time();
		$self->{kicked} = 0;
		$self->{data} = {
			COPPA			=> undef,
			password		=> undef,
			sanity			=> undef,
			kick_by			=> undef,
			kick_reason		=> undef,
		};
		$self->recreateId();
	} # end create


# Recreate the session ID, and mark this session as new.
	sub recreateId {
		my $self = shift;
		$self->{id} = Digest::MD5::md5_hex(rand(1000000) . rand(10000) . rand(100) . rand(2) . scalar localtime() . $$);
		$self->{saved} = 0;
	} # end recreateId


# Return the database handle
	sub db { $_[0]->{_db}; }


# Retrieve session information from the database
	sub retrieve {
		my $self = shift;
		my $id = shift;
		my $session_data = $self->db->selectrow_hashref('SELECT * FROM sessions WHERE id = ?', undef, $id);
	# No session?   Create a new one.
		if(!$session_data || !defined $session_data->{id}) {
			$self->create();
			return;
		} # end if
		$self->{id} = $session_data->{id};
		$self->{ip} = $session_data->{ip};
		$self->{created} = $session_data->{created};
		$self->{updated} = $session_data->{updated};
		$self->{kicked} = $session_data->{kicked};
		$self->{data} = Natter::Session::_unserializeData($session_data->{data});
		$self->{saved} = 1;
		return 1;
	} # end retrieve


# Validate the remote IP against the originally stored IP
# Returns false if the IPs don't match.
	sub validate {
		my $self = shift;
		my $current_ip = main::currentIP();
		$current_ip =~ s/(\.\d+)$//;
		my $last_ip = $self->{ip};
		$last_ip =~ s/(\.\d+)$//;
		return $current_ip eq $last_ip ? 1 : 0;
	} # end validate


# Save this session to the database
	sub save {
		my $self = shift;
		my $query = $self->{saved}
			? 'UPDATE sessions SET ip = ?, created = ?, updated = ?, kicked = ?, data = ? WHERE id = ?'
			: 'INSERT INTO sessions(ip, created, updated, kicked, data, id) VALUES(?, ?, ?, ?, ?, ?)';
		my $data = Natter::Session::_serializeData($self->{data});
		$self->db->do(
			$query,
			undef,
			$self->{ip},
			$self->{created},
			$self->{updated},
			$self->{kicked},
			$data,
			$self->{id}
		);
		$self->{saved} = 1;
	# Clean up after old sessions, 2% chance, 12 hour window.
		if(int(rand(50)) == 25) {
			my $old_sessions = $self->db->selectcol_arrayref('SELECT id FROM sessions WHERE updated < ?', undef, time() - (60 * 60 * 12));
			if(scalar @$old_sessions) {
				$self->db->do('DELETE FROM sessions WHERE id IN(?)', undef, $old_sessions);
				$self->db->do('UPDATE session_bans SET session_id = NULL WHERE session_id = IN(?)', undef, $old_sessions);
			# Another 10% chance to clean up the database file
				$self->db->do('VACUUM') if(int(rand(10)) == 5);
			} # end if
		} # end if
	} # end save


# Ban (kick) this session
# ** This should only be called by the BanManager.
# ** Self-banning code is a Bad Idea(tm)
	sub ban {
		my $self = shift;
		my $banned_by = shift;
		$banned_by ||= 'Auto';
		my $duration = shift;
		$duration ||= (60 * 5);
		$duration = (60 * 60 * 12) if($duration > (60 * 60 * 12));
		my $reason = shift;
		$reason ||= '(unknown)';
	# Perform the actual kick
		$self->{kicked} = time() + $duration;
		$self->{data}->{kick_by} = $banned_by;
		$self->{data}->{kick_reason} = $reason;
		$self->save();
	} # end ban


# Unban this session
	sub unban {
		my $self = shift;
	# Perform the unban
		$self->{kicked} = 0;
		$self->{data}->{kick_by} = undef;
		$self->{data}->{kick_reason} = undef;
		$self->save();
	} # end unban


# Determine if this user is banned; if so, return the end-of-ban time.
	sub isBanned {
		my $self = shift;
		$self->{kicked} = 0 if $self->{kicked} <= time();
		return $self->{kicked} if $self->{kicked};
	# Kicked is saved as part of the session; now check the IP...
		my $ban_info = Natter::BanManager::checkIPBan(main::currentIP());
	# No ban?
		return if (!$ban_info || !defined $ban_info->{ip});
	# b&
		if($ban_info) {
			$self->{kicked} = $ban_info->{created} + $ban_info->{duration};
			$self->{data}->{kick_by} = $ban_info->{created_by};
			$self->{data}->{kick_reason} = $ban_info->{reason};
			$self->{updated} = time();
			$self->save();
		} # end if
		return $self->{kicked};
	} # end isBanned


# Mark this session as active
	sub markActive {
		my $self = shift;
		$self->{ip} = main::currentIP();
		$self->{updated} = time();
		$self->save();
	} # end markActive


# Serialize the session data blob
	sub _serializeData {
		return JSON::PP::encode_json(shift);
	} # end _serializeData


# Unserialize the session data blob
	sub _unserializeData {
		return JSON::PP::decode_json(shift);
	} # end _unserializeData

1;
