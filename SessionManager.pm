#!/usr/bin/perl
#
# Natter 4.9
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

package SessionManager;
	use strict;
	use Storable qw(lock_store lock_retrieve);

# Cache / Singleton
	our $instance;

# Create a new instance / return the cached instance
	sub new {
		return \$SessionManager::instance if(defined $SessionManager::instance);
		my $class = shift;
		my $options = {
			'path' => shift(@_) . '/session_list.cgi',
			'sessions' => {},
			'banManager' => undef,
		};
		my $self = bless($options, $class);
		$SessionManager::instance = \$self;
		$self->_load();
		return $self;
	} # end new

# Save the session list to disk
	sub save {
		my $self = shift;
		$self->_save();
	} # end save

# Load the session list from disk
	sub _load {
		my $self = shift;
	# If the index doesn't exist, create it
		if(!-f $self->{path}) {
		# Note that this will cause a fatal error if the path does not exist or is not
		# writable.  Permissions and paths are a pain.
			lock_store({}, $self->{path});
		} # end if
	# Pull our session index off disk
		$self->{sessions} = lock_retrieve($self->{path});
	} # end load

# Perform the actual save internals
	sub _save {
		my $self = shift;
		lock_store($self->{sessions}, $self->{path});
	}

# Create a list of all active sessions
	sub listSessions {
		my $self = shift;
		return keys %{$self->{sessions}};
	} # end listSessions

# Create a new session, returning it
	sub createNewSession {
		my $self = shift;
		my $remote_addr = shift;
		my $session = Session->new(\$self);
		$session->markActive($remote_addr);
		$session->save();
		return \$session;
	} # end createNewSession

# Retrieve an existing session
	sub retrieveSession {
		my $self = shift;
		my $session_id = shift;
		return if(!exists $self->{session}->{$session_id});
		my $session = Session->retrieve($session_id, \$self);
		return \$session;
	} # end retrieveSession



package BanManager;
	use strict;
	use Storable qw(lock_store lock_retrieve);

# Cache / Singleton
	our $instance;

# Create a new instance
	sub new {
		return \$BanManager::instance if(defined $BanManager::instance);
		my $class = shift;
		my $options = {
			'path' => shift(@_) . '/ban_list.cgi',
			'bans' => {}
		};
		my $self = bless($options, $class);
		$BanManager::instance = \$self;
		$self->_load();
		return $self;
	} # end new

# Save the ban list to disk
	sub save {
		my $self = shift;
		$self->_save();
	} # end save

# Load the ban list from disk
	sub _load {
		my $self = shift;
	# If the index doesn't exist, create it
		if(!-f $self->{path}) {
		# Note that this will cause a fatal error if the path does not exist or is not
		# writable.  Permissions and paths are a pain.
			lock_store({}, $self->{path});
		} # end if
	# Pull our ban index off disk
		$self->{bans} = lock_retrieve($self->{path});
	} # end load

# Perform the actual save internals
	sub _save {
		my $self = shift;
		lock_store($self->{bans}, $self->{path});
	}

	sub addSessionBan {}
	sub addIPBan {}
	sub liftBan {}
	sub clearBan {}



package Session;
use strict;
use Storable qw(lock_store lock_retrieve);
use Digest::MD5;

sub new {}
sub retrieve {}
sub save {}

sub _load {}
sub _save {}

sub ban {}
sub unban {}

sub isBanned {}

sub markActive {}
