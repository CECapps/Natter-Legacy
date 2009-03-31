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

sub getConfig {
# Quick configuration for sane virtual hosting.  You may need to massively rewrite this.
	my $baseurl = '';
	my $basepath = '';
	my $pubdirname = '';

	my $z = {
	# URLs
		CGIURL 			=> $baseurl . $pubdirname,
		NonCGIURL 		=> $baseurl . $pubdirname,
		LogsURL 		=> $baseurl . $pubdirname . q!/logs!,
	# Paths
		CGIPath 		=> $basepath . $pubdirname,
		NonCGIPath 		=> $basepath . $pubdirname,
		LogsPath 		=> $basepath . $pubdirname . q!/logs!,
		SessionPath 	=> $basepath . $pubdirname . q!/sessions!,
	# Options
		MessageLimit	=> 15,
		EnableCaptions	=> 0,
		RefreshRate 	=> 8,
		DisableLamenessFilter => 0,
		TimeZoneCode	=> 'America/Los_Angeles', # see http://en.wikipedia.org/wiki/List_of_zoneinfo_time_zones
		TimeZoneName 	=> 'Pacific',
		ChatName		=> q!CHAT NAME GOES HERE!,
	};

# Options based on configurations.  Don't touch this.
	$z->{Script} 		= 'chat3.cgi';
	$z->{GuardScript} 	= 'guard3.cgi';
	$z->{CSSFile} 		= 'style.php';
	$z->{MessagesFN} 	= 'messages';
	$z->{MessagesFX} 	= '.html';
	$z->{ScriptName} 		= $z->{CGIURL} 		. "/" . $z->{Script};
	$z->{GuardScriptName} 	= $z->{CGIURL} 		. "/" . $z->{GuardScript};
	$z->{MessagesFile} 		= $z->{NonCGIPath} 	. "/" . $z->{MessagesFN} . $z->{MessagesFX};
	$z->{MessagesName} 		= $z->{NonCGIURL} 	. "/" . $z->{MessagesFN} . $z->{MessagesFX};
	$z->{PostlogFile} 		= $z->{NonCGIPath} 	. "/" . $z->{MessagesFN} . "_bans.cgi";
	$z->{CSSName} 			= $z->{NonCGIURL} 	. "/" . $z->{CSSFile};

	return $z;
} # end sub

sub getGuardList {
	my $gl = {
		"Guard" => "password1",
	};
	return $gl;
} # end sub

1;
