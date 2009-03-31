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

# This is a mess.  This is bad code.  Horrible code.  Nasty code.
# You shouldn't even look at this code if you want to keep your sanity.
# I wrote it ten years ago, and wish I could un-write it.
# While I could refactor this into sanity, it would also mean rewriting the
# entire guard script.  That's probably not a bad idea either, honestly.

package SessionKeeper;
use strict;
no strict("refs");
use Fcntl qw(:DEFAULT :flock);
use Storable qw(store retrieve);

BEGIN {
	our $VERSION = 0.21;
	our $NEVER = '2147483647';
} # end BEGIN


sub new {
	my $protoobj = shift;
	my $class = ref($protoobj) || $protoobj;
	my $self = shift; # a hashref

# Can we pull information about the chat sessions from the disk?
	my $file = "$self->{STOREDIR}/index.cgi";
	if(-e $file && -s $file) {
	# Yup.  Bring it back to life
		my $old_storedir = $self->{STOREDIR};
		$self = retrieve($file);
		$self->{STOREDIR} = $old_storedir;
	} else {
	# Nope, create a new instance of ourself
		$self = {
			STOREDIR => $self->{STOREDIR},
			VALIDS => {},
			THIS => {} ,
		};
		bless ($self, $class);
		$self->record();
	} # end if

	return $self;
} # end new

# Record chat session data to disk
sub record {
	my $self = shift;

	my $now = time();
	my $later = $now + (60 * 60 * 8);
	my $then = $now - (60 * 60 * 8);

	my %z = %{$self->{THIS}};

# Store this user's session
	if($self->is_valid($self->{THIS}->{UNIQID})) {
		my $file = $self->{STOREDIR} . '/' . $self->{VALIDS}->{ $self->{THIS}->{UNIQID} }->{FILENAME} . '.cgi';
		$self->{VALIDS}->{ $self->{THIS}->{UNIQID} }->{TIMEOUT} = $later;
		store($self->{THIS}, $file) or die $!;
	} # end if
	$self->{THIS} = {};

# Remove old session records
	foreach my $uniq (keys %{ $self->{VALIDS} }) {
		if($self->{VALIDS}->{$uniq}->{TIMEOUT} < $now ) {
			unlink($self->{STOREDIR} . '/' . $self->{VALIDS}->{$uniq}->{FILENAME} . '.cgi');
			delete $self->{VALIDS}->{$uniq};
		} # end if
	} # end foreach

# Finally, write out the index again
	store($self, $self->{STOREDIR} . '/index.cgi') or die $!;

# Restore the user's session back into ourself.
	$self->{THIS} = \%z;
} # end record

# Determine the vailidy of this user's session.
# I'm not sure what the purpose of this is.
sub is_valid {
	my $self = shift;
	my $test = shift;

	my $points = 0;

	if($test =~ m!^[a-zA-Z0-9]{32,}$!i) {
		$points++ if exists $self->{VALIDS}->{$test};
		$points++ if((exists $self->{THIS}->{UNIQID}) && ($test eq $self->{THIS}->{UNIQID}));
		$points++ if $self->is_special($test);
	} # end if

	return $points;
} # end is_valid

# Determine if this is a special user.
# Old bot code uses the special value '2147483647' in the session cookie.
# I think.  All known bots that work with this chat code (Feenix) can store
# and retrieve cookies and behave like normal chatters.  The Coddish Proxy
# has not been tested against this new code at time of writing.
sub is_special {
	my $self = shift;
	my $test = shift;

	my $points = 0;
	$points++ if(($test =~ m/^2147483647/) && (length($test) == 32));

	return $points;
} # end is_special


# Create a new blank session for the current user.
sub make_new {
	my $self = shift;
	my $uniq = time() . $self->_random(56);
	my $fn = $self-> _random(44);
	my $now = time();
	my $later = $now + (60 * 60 * 48);

	$self->{VALIDS}->{$uniq} = {
		FILENAME => $fn,
		TIMEOUT => $later,
	}; # end

	$self->{THIS} = {
		UNIQID => $uniq,
		TIMEOUT => $later,
		KICKBAN => { },
	}; # end

	return $uniq;
} # end make_new


# Pull the user session from disk, if the user session exists.
sub load_if_valid {
	my $self = shift;
	if($self->is_valid($_[0])) {
		$self->{THIS} = retrieve($self->{STOREDIR} . '/' . $self->{VALIDS}->{$_[0]}->{FILENAME} . '.cgi') unless $self->is_special($_[0]);
		return 1;
	} # end if
	return 0;
} # end load_if_valid


# Return the current user unique ID
sub current_id {
	return $_[0]->{THIS}->{UNIQID};
} # end current_id


# Determine if thie user is banned.  Sets the KICKBAN attribute.  What?
sub comp_to_banned {
	my $self = shift;
	my $ip = shift;
	my $banlist = $self->_load_banlist();
# Direct IP ban
	if(exists $banlist->{$ip}) {
		$self->{THIS}->{KICKBAN} = $banlist->{$ip};
	} # end if
# /24 ban
	if($ip =~ m/^(\d+\.\d+\.\d+\.)\d+$/) {
		my $partial_ip = $1;
		if(exists $banlist->{$partial_ip}) {
			$self->{THIS}->{KICKBAN} = $banlist->{$partial_ip};
		} # end if
	} # end if
# /16 ban
	if($ip =~ m/^(\d+\.\d+\.)\d+\.\d+$/) {
		my $partial_ip = $1;
		if(exists $banlist->{$partial_ip}) {
			$self->{THIS}->{KICKBAN} = $banlist->{$partial_ip};
		} # end if
	} # end if

	return;
} # end comp_to_banned


# Return the end ban time, or undef
sub this_banned {
	my $self = shift;
	if($self->{THIS}->{KICKBAN}->{TIME} > time()) {
		return $self->{THIS}->{KICKBAN}->{TIME};
	} else {
		return undef;
	} # end if
} # end this_banned


# Ban the user until the specified time
sub ban_current {
	$_[0]->{THIS}->{KICKBAN} = $_[1];
} # end ban_current


# Load the ban list
sub prep_ip_ban {
	$_[0]->{BANLIST} = $_[0]->_load_banlist();
} # end prep_ip_ban


# Add an IP to the ban list
sub add_ip_ban {
	$_[0]->{BANLIST}->{$_[1]} = $_[2];
} # end add_ip_ban


# *EXPIRE* an IP from the ban list.
sub remove_ip_ban {
	my %temp = %{$_[0]->{BANLIST}->{$_[1]}};
	my %t2 = %{$_[2]};
	my %t3 = (%temp, %t2);
	$_[0]->{BANLIST}->{$_[1]} = \%t3;
} # end remove_ip_ban


# Delete an IP from the ban list.
sub del_ip_ban {
	delete $_[0]->{BANLIST}->{$_[1]};
} # end del_ip_ban


# Store the ban list to disk
sub write_ip_ban {
	store($_[0]->{BANLIST}, "$_[0]->{STOREDIR}/ban.cgi") or die $!;
} # end write_ip_ban


# Inner workings of the ban list store
sub _load_banlist {
	my $self = shift;
	my $banlist;
	my $file = "$self->{STOREDIR}/ban.cgi";
	if(-e $file && -s $file) {
		$banlist = retrieve($file);
	} else {
		$banlist = {};
	} # end if
	return $banlist;
	#$banlist{"IP"} = { TIME => 100000000, BY => "Name", FOR => "Reason" };
} # end _load_banlist


# Create a sequence of random characters.
sub _random {
	my @letters = ("a".."z","A".."Z",0..9);
	my $string; my $l = scalar(@letters); $l--;
	foreach(1 .. $_[1]) {
		$string .= $letters[(int(rand($l)) + 1)];
	} # end foreach
	return $string;
} # end _random


1 + 2 == 3;
