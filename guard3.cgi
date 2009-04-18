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

# This is slightly more wtftastic than the main chat script.

use lib('.', './ext');
use strict;
no strict("subs");	# :-P
no strict("refs");	# :-P x2
use warnings;
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser set_message);
use Storable qw(retrieve);
use SessionKeeper;
use Digest::MD5;
require "chat3_lib.cgi";

# All errors are handled by the standardHTML routine, courtesy CGI::Carp
	set_message(\&standardHTML);

# Pull in our configuration information
	&evalFile("./config.cgi");
	(defined &getConfig) ? (our $config = &getConfigPlusDefaults) : (die("I can't seem to find my configuration.\n"));
	(defined &getGuardList) ? (our $guard_list = &getGuardList) : (die("I can't seem to find my guard configuration.\n"));

# Pull in the session manager
	our $sessions = new SessionKeeper({ STOREDIR => $config->{SessionPath} });

# Engage the global file lock
	our $LOCKFILE = &makeGlob;
	&lockAndLoad;

# Emulate cgi-lib's ReadParse() for ease of use.  Calling param() all the time is annoying.
	our %in = map{$_ => CGI::param($_)} CGI::param();

# Make sure we're actually *DOING* something.
	if((!exists $in{action}) || ($in{action} eq "")) {
		$in{action} = "frameset";
	} # end if

# Set up a list of valid subroutines that the outside world can get to...
	my %actions = (
		frameset => \&action_frameset,
		view => \&action_view,
		ban => \&action_ban,
		unban => \&action_unban,
		delban => \&action_delban,
		logs => \&action_logs,
		bans => \&action_bans,
	);

# ... then do the right one.
	if(exists $actions{$in{action}}) {
		&{$actions{$in{action}}};
		&Exit();
	} else {
		&standardHTML({
			header => "Error",
			body => "I'm sorry Dave, I can't do that.",
			footer => "Please try your request again.",
		});
	} # end if

# That's all, folks!
	&Exit();


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# action_ subroutines

# Rewrite the frameset code to insert a section on the right
	sub action_frameset {
		&checkAuthCookie;

		my $file = &openFile($config->{NonCGIPath} . "/chat.html");
		my $frametop = qq(<frameset cols="*, 210" border="2">);
		my $framebo = qq(<frame src="$config->{GuardScriptName}?action=view" name="ips" id="ips" scrolling="auto"></frameset>);
		$file =~ s/\<\!-- GFS --\>/$frametop/;
		$file =~ s/\<\!-- EGFS --\>/$framebo/;
		print header . $file;
		&Exit;
	} # end action_frameset


# View the list of current users
	sub action_view {
		&checkAuthCookie;
	# User data for this page is kept in an external file in the following format:
	# Name|^!^|main color|^!^|message color|^!^|Session|^!^|IP|^!^|Timestamp|^!^|
		my @users = grep(/\|\^\!\^\|/, &openFileAsArray($config->{PostlogFile}));
		my $html;
		my %uniqs;
		my $seens = 0;
		my $linecount = 0;
		foreach my $line (@users) {
			chomp($line);
			my @data = split(/\|\^\!\^\|/, $line);
		# Reset certain data to sane deaults
			my $nc = $data[2] || "white";
			my $mc = $data[1] || "white";
			my $name = $data[0] || "(lurker)";
			$name = "(lurker)" if $name eq "Name";
		# Multiple chat users can have the same session (one user, multiple tabs)
			my $idnum;
			if(exists $uniqs{$data[3]}) {
				$idnum = $uniqs{$data[3]};
			} else {
				$seens++;
				$uniqs{$data[3]} = $seens;
				$idnum = $uniqs{$data[3]};
			} # end if
		# Reassemble the timestamp
			my $dt = &getTime($data[5]);
			my $timer = $dt->strftime('%H:%M:%S %Y-%m-%d');

			$html .= <<TABLE;
<tr class="bantoprow" id="toprow-$linecount">
	<td rowspan="2" name="radio-$linecount" id="radio-$linecount" class="banbtncell">
		<span>
			<input type="radio" name="iden" id="iden-$linecount" value="$data[3]|^|$data[4]">
		</span>
	</td>
	<td name="name-$linecount" id="name-$linecount" class="bannamecell name">
		<font color="$nc">$name</font>
	</td>
</tr>
<tr class="banbotrow" id="botrow-$linecount">
	<td name="data-$linecount" id="data-$linecount" class="banipcell thetime">
		<span>
			<font color="$mc">$data[4] (<i>$idnum</i>)</font>
			<br />
			<small>$timer</small>
		</span>
	</td>
</tr>

TABLE
			$linecount++;
		} # end foreach

	# This is crap, but it's refactored crap.
		$html = q~
<script language="JavaScript" type="text/javascript">

	$().ready(function(){
		$('tr.bantoprow, tr.banbotrow')
		// Twiddle borders on hover
			.mouseover(function(event){
			// Who are we pointing at?  Note we use currentTarget here, not target.
			// currentTarget is the element that fired the event, target is the one
			// that is *active* in the event, i.e. a child.
				var tr = $(event.currentTarget);
			// Extract the line number
				var match = tr.attr('id').match(/\-(\d+)/);
				if(!match || !match[1])
					return;
			// Now use that to turn the cells on.
				$('#radio-' + match[1]).addClass('active');
				$('#name-' + match[1]).addClass('active');
				$('#data-' + match[1]).addClass('active');
			})
		// Twiddle hovers on unhover
			.mouseout(function(event){
				var tr = $(event.currentTarget);
			// Extract the line number
				var match = tr.attr('id').match(/\-(\d+)/);
				if(!match || !match[1])
					return;
			// Now use that to turn the cells on.
				$('#radio-' + match[1]).removeClass('active');
				$('#name-' + match[1]).removeClass('active');
				$('#data-' + match[1]).removeClass('active');
			})
		// Clicking any of the cells will trigger selection of the checkbox.
			.click(function(event){
				var tr = $(event.currentTarget);
			// Extract the line number
				var match = tr.attr('id').match(/\-(\d+)/);
				if(!match || !match[1])
					return;
				var line_id = match[1];
			// Check it
				$('#iden-' + line_id).attr('checked', 'checked');
			// Now update the ban info at the bottom
				update_summary(line_id);
			});
		// The method dropdown changes the IP information...
			$('#meethod').change(function(){ update_summary(); });
		// The big red button needs extra special magic
			$('#bankickbtn').click(function(event){
				var reason = $('#reason').attr('value');
				if(!reason || !reason.length) {
					alert("You must provide a reason for this kick or ban.");
					event.preventDefault();
					event.stopPropagation();
					return false;
				} // end if
			});
		// The refresh button
			$('#banrefreshbtn').click(function(event){
				location.href = '~ . $config->{GuardScriptName} . q~?action=view';
			});
	});

	function update_summary(line_id) {
	// If we didn't get a line id, try to determine it...
		if(!line_id) {
			var match = $('input[name=iden]:checked').attr('id').match(/\-(\d+)/);
			if(!match || !match[1])
				return;
			line_id = match[1];
		} // end if
	// Extract data from the radio button
		var radio = $('#iden-' + line_id);
		var mrf = radio.attr('value');
		var match = mrf.match(/^([a-zA-Z0-9]+)\|\^\|([\d\.]+)$/);
		if(!match || match.length != 3)
			return;
	// Update the one form value we care about, and display IP info if needed
		var ban_type = $('#meethod').attr('value');
		var data;
		if(ban_type == 'byid') {
		// This will be a session ban
			data = match[1];
			$('#pubip').css({ visibility: 'hidden' });
			$('#pubip-label').css({ visibility: 'hidden' });
		} else {
		// This will be an IP-based ban.
			data = match[2];
			$('#pubip').html(data);
			$('#pubip').css({ visibility: 'visible' });
			$('#pubip-label').css({ visibility: 'visible' });
		} // end if
		$('#summy').attr('value', data);
		return data;
	} // end update_summary

</script>
~ . qq~
       &raquo; <a href="logs.php?guard=1" target="_blank">Guard Chat Logs</a>
<br /> &raquo; <a href="$config->{GuardScriptName}?action=bans">Ban History</a>

<form action="guard3.cgi" method="post" name="ex" id="ex">
<table id="bantable" cellpadding="0" cellspacing="0" border="0">
$html
</table>
~;
	$html .= qq(
<br />

<input type="hidden" name="action" id="action" value="ban">
<input type="button" value="Refresh" class="button" id="banrefreshbtn">
<input type="hidden" name="summy" id="summy" value="">

<br /><br /><hr />

<table border="0" cellspacing="0" cellpadding="1" id="banopttable">
	<tr>
		<td align="right" id="pubip-label" style="visibility: hidden">IP:</td>
		<td id="pubip" style="visibility: hidden">&nbsp;</td>
	</tr>
	<tr>
		<td align="right"><label for="meethod">Method:</label></td>
		<td>
			<select name="meethod" id="meethod" class="textbox">
				<option value="byid" selected="selected">Session</option>
				<option value="byip4">IP (x.x.x.x)</option>
				<option value="byip3">IP (x.x.x.*)</option>
				<option value="byip2">IP (x.x.*)</option>
			</select>
		</td>
	</tr>
	<tr>
		<td align="right"><label for="time">Duration:</label></td>
		<td>
			<select name="time" id="time" class="textbox">
				<option value="5"		>5 minutes</option>
				<option value="15"		>15 minutes</option>
				<option value="30"		>30 minutes</option>
				<option value="60" selected="selected">1 hour</option>
				<option value="360"		>6 hours</option>
				<option value="720"		>12 hours</option>
				<option value="1440"	>1 day</option>
				<option value="10080"	>1 week</option>
				<option value="40320"	>1 month</option>
				<option value="120960"	>3 months</option>
				<option value="241920"	>6 months</option>
				<option value="483840"	>1 year</option>
				<option value="2419200"	>5 years</option>
			</select>
		</td>
	</tr>
	<tr>
		<td align="right"><label for="reason">Reason:</label></td>
		<td>
			<input type="text" name="reason" id="reason" class="textbox" size="15" />
		</td>
	</tr>
	<tr>
		<td colspan="2">
			<input type="submit" value="Ban/Kick" class="button" id="bankickbtn">
		</td>
	</tr>
</table>

</form>
);
	# Yes, we use StandardHTML to emit this block of code.... I'm sorry.
		&standardHTML($html);
	} # end action_view


# Ban the requested user
	sub action_ban {
		&checkAuthCookie;

		if(!$in{"reason"}) {
			&standardHTML("You must enter a reason.");
		} elsif(!$in{"summy"}) {
			&standardHTML("You forgot to select someone to remove!");
		} elsif(!$in{"meethod"}) {
			&standardHTML("How did you forget the method!?");
		} elsif(!$in{"time"}) {
			&standardHTML("How did you forget the time!?");
		} # end if

		use Data::Dumper;

	# Ban data looks like:
	#$v->{'63.24.226.48'} = {
	#                              'BY' => 'Charles',
	#                              'FOR' => 'RW being an idiot again.',
	#                              'TIME' => time() + (60 * 60),
	#                            };

	# Yes, it is spelled with two "e"s.  Why?
		if($in{meethod} eq "byid") {
		# Pull up the user's session and smash'em
			if($sessions->load_if_valid($in{summy})) {
				$sessions->ban_current({
				# time() -> UTC, fine here
					TIME	=> (time() + ($in{time} * 60)),
					BY		=> (cookie("$config->{CookiePrefix}_guard"))[0], # OH GOD WHAT
					FOR		=> $in{reason}
				});
				$sessions->record();
				&standardHTML(qq!User banned for $in{time} minutes.<br /><a href="$config->{GuardScriptName}?action=view">Back</a>!);
			} else {
				&standardHTML("That session number is invalid.<br /><br />Perhaps my index is b0rked?");
			} # end if
		} else {
		# This is more fun though...
			$sessions->prep_ip_ban();
			my $thisip = $in{summy};
			if($in{meethod} eq "byip3") {
				$thisip =~ s/^(\d+\.\d+\.\d+\.)\d+$/$1/;
			} elsif($in{meethod} eq "byip2") {
				$thisip =~ s/^(\d+\.\d+\.)\d+\.\d+$/$1/;
			} # end if
			$sessions->add_ip_ban($thisip, {
			# time() -> UTC, fine here
				TIME	=> (time() + ($in{time} * 60)),
				BY		=> (cookie("$config->{CookiePrefix}_guard"))[0],
				FOR		=> $in{reason},
				STARTTIME => time()
			});
			$sessions->write_ip_ban();
			&standardHTML(qq!IP banned for $in{time} minutes.<br /><a href="$config->{GuardScriptName}?action=view">Back</a>!);
		} # end if

	} # end action_ban



# List bans in the logs
	sub action_bans {
		&checkAuthCookie;

		my $filename = $config->{SessionPath} . '/ban.cgi';
		my $banlist = -e $filename && -s $filename ? retrieve($filename) : {};
		my(@list, @olds);
		foreach my $ip (keys %{$banlist}) {
			push(@list, $banlist->{$ip}->{TIME} . "|$ip") if $banlist->{$ip}->{TIME} > time();
			push(@olds, $banlist->{$ip}->{TIME} . "|$ip") if $banlist->{$ip}->{TIME} < time();
		} # end foreach

		my $string = qq!&raquo; <a href="$config->{GuardScriptName}?action=view">Back</a><br /><br /><b>Current Bans:</b><br />!;
		$string .= &banize($banlist, sort { $a <=> $b } @list);
		$string .= qq!<br /> <br /><hr /> <b>Expired/Lifted Bans:</b><br />!;
		$string .= &banize($banlist, reverse sort { $a <=> $b } @olds);

		&standardHTML($string);

	} # end action_bans


# Lift a current ban
	sub action_unban {
		&checkAuthCookie;

		$sessions->prep_ip_ban();
		my $thisip = $in{ip};
		$sessions->remove_ip_ban($thisip, {
			TIME => time(),
			LIFTEDBY => (cookie("$config->{CookiePrefix}_guard"))[0]
		});
		$sessions->write_ip_ban();
		&standardHTML(qq!Ban lifted.<br /><a href="$config->{GuardScriptName}?action=bans">Back</a>!);
	} # end action_unban


# Delete a lifted ban
	sub action_delban {
		&checkAuthCookie;

		$sessions->prep_ip_ban();
		my $thisip = $in{ip};
		$sessions->del_ip_ban($thisip);
		$sessions->write_ip_ban();
		&standardHTML(qq!Ban deleted.<br /><a href="$config->{GuardScriptName}?action=bans">Back</a>!);
	} # end action_delban


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Common library subroutines

sub banize {

	my ($banlist, @list) = @_;
	my @active_bans;

	foreach my $line (@list) {
		my($timer, $ip) = split(/\|/, $line);
		my $dt_ts = &getTime($banlist->{$ip}->{TIME});
		my $ts = $dt_ts->strftime('%Y-%m-%d %H:%M:%S');
		my $dt_ss = &getTime($banlist->{$ip}->{STARTTIME});
		my $ss = ($banlist->{$ip}->{STARTTIME} ? $dt_ss->strftime('%Y-%m-%d %H:%M:%S') : "<i>unknown</i>)" );
		my $iflift = ($banlist->{$ip}->{LIFTEDBY} ? qq!<br /><span class="bannedlifted">(Lifted by $banlist->{$ip}->{LIFTEDBY})</span>!
			:
			($banlist->{$ip}->{TIME} > time() ?
				qq!<br />[<a href="$config->{GuardScriptName}?action=unban&ip=$ip">Lift Ban</a>]!
				: "")
			);
		my $isdel = ($banlist->{$ip}->{TIME} < time() ? qq!<br />[<a href="$config->{GuardScriptName}?action=delban&ip=$ip">Delete Ban</a>]! : "");
		$active_bans[$#active_bans + 1] = <<HERE;
<br />
<b>$ip</b> (<i>$banlist->{$ip}->{BY}</i>)
<br />S: <span class="bannedstart">$ss</span>
<br />E: <span class="bannedend">$ts</span>
<br /><span class="bannedreason">$banlist->{$ip}->{FOR}</span>
$iflift$isdel
HERE
	} # end foreach

	my $string = join('<hr width="50%" />', @active_bans);
	$string = '<br />(none)' if(!$string);

	return $string;
} # end banize


# Exit cleanly.  Note: Unlike the version in the chat script, we do NOT write out session data!
	sub Exit {
		exit(0);
	} # end Exit
