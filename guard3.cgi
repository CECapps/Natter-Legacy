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

use v5.8.0;
use lib('.', './ext');
use strict;
use warnings;
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser set_message);
use Natter::Session;
use Natter::HTTP_Request;
use Natter::HTTP_Response;
require "chat3_lib.cgi";

# All errors are handled by the standardHTML routine, courtesy CGI::Carp
	set_message(\&standardHTMLForErrors);

# Pull in our configuration information
	evalFile("./config.cgi");
	(defined &getConfig) ? (our $config = getConfigPlusDefaults()) : (die("I can't seem to find my configuration.\n"));
	(defined &getGuardList) ? (our $guard_list = getGuardList()) : (die("I can't seem to find my guard configuration.\n"));

# Fire up the HTTP Request...
	our $cgi = new CGI;
	our $request = new Natter::HTTP_Request();
	our $response = new Natter::HTTP_Response();
	our %in = $request->getParams();

# Initialize the user's session
	our $session = new Natter::Session();
	my $session_id = $request->getCookie($config->{CookiePrefix} . '_session');
	if(!$session_id) {
	# If we didn't get a session cookie, create a new session for the user.
		$session->create();
		$session_id = $session->{id};
		$response->addCookie(
			-name    => $config->{CookiePrefix} . '_session',
			-value   => [$session_id],
		);
	} else {
	# Otherwise, we got a valid session id.  Try and load it up.
		my $retrieved = $session->retrieve($session_id);
	# Make sure the retrieve worked and the IP matches
		if(!$retrieved || !$session->validate()) {
		# The IP didn't match or the session is bogus.  This may be a cookie hijack.
		# Clone the existing session data and try to recreate it.
			$session->create() if !$retrieved;
			$session->recreateId();
			$session_id = $session->{id};
			$response->addCookie(
				-name    => $config->{CookiePrefix} . '_session',
				-value   => [$session_id],
			);
		} # end if
	} # end if

# Engage the global file lock.  Due to concurrency issues, only one process is
# permitted to perform actions at once.  This is an intentional restriction due
# to having to deal with things on-disk.
	our $LOCKFILE;
	lockAndLoad($LOCKFILE);

# Make sure we're actually *DOING* something.
	if((!exists $in{action}) || ($in{action} eq "")) {
		$in{action} = "frameset";
	} # end if

# Set up a list of valid subroutines that the outside world can get to...
	my %actions = (
		authenticate	=> \&action_authenticate,
		frameset		=> \&action_frameset,
		list_users		=> \&action_list_users,
		ban				=> \&action_ban,
		list_bans		=> \&action_list_bans,
		lift_ban		=> \&action_lift_ban,
		clear_ban		=> \&action_clear_ban,
	);

# The user can't do anything at all unless he's logged in.
	if(!defined $session->{data}->{guard}) {
		$in{action} = 'authenticate';
	} # end if

# ... then do the right one.
	if(exists $actions{$in{action}}) {
		&{$actions{$in{action}}};
		&Exit();
	} else {
		$response->appendBody(standardHTML({
			header => "Error",
			body => "I'm sorry Dave, I can't do that.",
			footer => "Please try your request again.",
		}));
	} # end if

# That's all, folks!
	&Exit();


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# action_ subroutines

# Prompt the user to log in.
	sub action_authenticate {
	# If the user can be authenticated, do so and throw them at the frameset
		if($request->isPost() && exists $guard_list->{ $in{username} } && $guard_list->{ $in{username} } eq $in{password}) {
			migrateBans();
			$session->{data}->{guard} = $in{username};
			$response->addHeader('Status', '302 Found');
			$response->addHeader('Location', $config->{GuardScriptName} . '?action=frameset');
		} # end if
	# If not, the user will need to be prompted.
		if(!defined $session->{data}->{guard}) {
			my $error = ($request->isPost() || exists $in{username} || exists $in{password})
						? '<div style="color: red; font-weight: bold; margin: 10px; ">Invalid Credentials</div>'
						: '';
		# The user did not provide a username, or this wasn't the submit.  Show them the form.
			$response->setBody(standardHTML({
				header => "Enter Credentials",
				body => <<FORMBODY
$error
<form id="entrance" method="POST" action="$config->{GuardScriptName}">
<table border="0" align="center">
<tr><td class="body">Username:</td><td><input type="text" name="username" id="username" class="textbox"></td></tr>
<tr><td class="body">Password:</td><td><input type="password" name="password" id="password" class="textbox"></td></tr>
<tr><td colspan="2"><input type="submit" value="Submit Credentials" class="button"></td></tr>
</table>
</form>
FORMBODY
				,
				footer => '<small class="copy">Misuse of this system is prohibited.<br />Violators will be prosecuted by lawyers and persecuted by lemurs.</small>',
			}));
		} # end if
	} # end action_authenticate


# Rewrite the frameset code to insert a section on the right
	sub action_frameset {
		my $file = openFile($config->{NonCGIPath} . "/chat.html");
		my $frametop = qq(<frameset cols="*, 210" border="2">);
		my $framebo = qq(<frame src="$config->{GuardScriptName}?action=list_users" name="ips" id="ips" scrolling="auto"></frameset>);
		$file =~ s/\<\!-- GFS --\>/$frametop/;
		$file =~ s/\<\!-- EGFS --\>/$framebo/;

		$response->appendBody($file);
		&Exit();
	} # end action_frameset


# View the list of current users
	sub action_list_users {
	# User data for this page is kept in an external file in the following format:
	# Name|^!^|main color|^!^|message color|^!^|Session|^!^|IP|^!^|Timestamp|^!^|
		my @users = grep(/\|\^\!\^\|/, openFileAsArray($config->{PostlogFile}));
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
			my $name = $data[0] || "Name";
			$name = "<small><i>(lurker)</i></small>" if $name eq "Name";
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
			my $dt = getTime($data[5]);
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
			$('#banrefreshbtn, #banrefreshbtn_top').click(function(event){
				location.href = '~ . $config->{GuardScriptName} . q~?action=list_users';
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
<br /> &raquo; <a href="$config->{GuardScriptName}?action=list_bans">Active Ban List</a>

<br /><br />
<input type="button" value="Refresh" class="button" id="banrefreshbtn_top">
<br />
<form action="guard3.cgi" method="post" name="ex" id="ex" autocomplete="off">
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
				<optgroup label="Session &amp; IP">
					<option value="5"		>5 minutes</option>
					<option value="15"		>15 minutes</option>
					<option value="30"		>30 minutes</option>
					<option value="60" selected="selected">1 hour</option>
					<option value="120"		>2 hours</option>
					<option value="180"		>3 hours</option>
					<option value="360"		>6 hours</option>
					<option value="720"		>12 hours</option>
				</optgroup>
				<optgroup label="IP Only">
					<option value="1440"	>1 day</option>
					<option value="10080"	>1 week</option>
					<option value="40320"	>1 month</option>
					<option value="120960"	>3 months</option>
					<option value="241920"	>6 months</option>
					<option value="483840"	>1 year</option>
					<option value="2419200"	>5 years</option>
				</optgroup>
			</select>
		</td>
	</tr>
	<tr>
		<td align="right"><label for="reason">Reason:</label></td>
		<td>
			<input type="text" name="reason" id="reason" class="textbox" size="15" autocomplete="off" />
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
	# Yes, we use StandardHTML to emit this block of code...
		$response->appendBody(standardHTML($html));
	} # end action_list_users


# Ban the requested user
	sub action_ban {
		my $error;
		if(!$in{"reason"}) {
			$error = "You must enter a reason.";
		} elsif(!$in{"summy"}) {
			$error = "You forgot to select someone to remove!";
		} elsif(!$in{"meethod"}) {
			$error = "How did you forget the method!?";
		} elsif(!$in{"time"}) {
			$error = "How did you forget the time!?";
		} # end if

	# You can't ban yourself...
		if($in{meethod} eq 'byid' && $in{summy} eq $session->{id}) {
			$error = 'You can not ban your own session.';
		} # end if
		if($in{meethod} =~ m/^byip/ && $in{summy} eq currentIP()) {
			$error = 'You can not ban your own IP address.';
		} # end if

	# Okay, now, where were we?
		my $success;
		my $banman = new Natter::BanManager();
		if(!$error && $in{meethod} eq 'byid') {
		# This is a session ban.  They're limited to 12 hours.
			$in{time} = 720 if($in{time} > 720);
			$banman->addSessionBan(
				$in{summy}, # this will be the session ID in the event of a session ban.
				$in{time} * 60, # duration
				$session->{data}->{guard}, # created by
				$in{reason}, # reason
			);
			$success = 'The requested session has been kicked from the chat.';
		} elsif(!$error && $in{meethod} =~ m/^byip(\d)$/) {
		# This is an IP ban!
			my $method = $1;
			$banman->addIPBan(
				$in{summy}, # this will be the IP address in the event of an IP ban
				$method,
				$in{time} * 60, # duration
				$session->{data}->{guard}, # created by
				$in{reason}, # reason
			);
			$success = 'The requested IP address has been banned from the chat.';
		} elsif(!$error) {
		# Neither circumstance matched, yet there was no error.  What?
			$error = 'You confused my poor little brain.  Try again.';
		} # end if

		$success = $error if $error && !$success;
		$response->appendBody(standardHTML( $success .  qq~<br />&raquo;<a href="$config->{GuardScriptName}?action=list_users">Return</a>~ ));
	} # end action_ban


# List bans in the logs
	sub action_list_bans {
		my $banman = new Natter::BanManager();
		my $bans = $banman->getBanList();
	# Split out current bans from lifted bans.  Makes sorting a bit easier.
		my $now = time();
		my @active = grep { $_->{lifted} > $now } @$bans;
		my @lifted = grep { ($_->{lifted} < $now || $_->{lifted_by}) && !$_->{cleared_by} } @$bans;
		my @cleared = grep { $_->{cleared_by} } @$bans;
		my $clearcount = scalar @cleared;
		my $show_cleared = qq~&raquo; <a href="$config->{GuardScriptName}?action=list_bans&show_cleared=1">Show $clearcount Cleared Bans</a><br />~;
		if($in{show_cleared}) {
			$show_cleared = qq~&raquo; <a href="$config->{GuardScriptName}?action=list_bans">Hide Cleared Bans</a><br />~
						   . '<br /><b>Cleared Bans:</b><br />'
			               . createBanListHTML(@cleared)
						   . '<br /><hr />';
		} # end if

		my $string = qq!
&raquo; <a href="$config->{GuardScriptName}?action=list_users">Back to User List</a>
<br />
$show_cleared
<br /><b>Active Bans:</b><br />
		! . createBanListHTML(@active) . qq!
<br /> <br /><hr /> <b>Expired &amp; Lifted Bans:</b><br />
		! . createBanListHTML(@lifted);

		$response->appendBody(standardHTML($string));
	} # end action_list_bans


# Lift a currently active ban.
	sub action_lift_ban {
		my $banman = new Natter::BanManager();
		my $ban_id = $in{ban_id} + 0;
		my $ban_type = ($in{ban_type} eq 'session') ? 'session' : 'ip';
		if(!$ban_id || $in{ban_type} ne $ban_type) {
			$response->appendBody(standardHTML("Sorry, I don't know what you're trying to do."));
			&Exit();
		} # end if
	# Need to add a check to ensure that the ban is still active...
		if($ban_type eq 'session') {
			$banman->liftSessionBan($ban_id, $session->{data}->{guard});
		} else {
			$banman->liftIPBan($ban_id, $session->{data}->{guard});
		} # end if
		$response->appendBody(standardHTML(qq~
			The requested ban has been lifted.  Please note that users may need
			to restart their browsers before they see that they have been unbanned.
			<br />
			&raquo; <a href="$config->{GuardScriptName}?action=list_bans">Back to Ban List</a>
		~));
	} # end action_lift_ban


# Clear an expired or lifted ban
	sub action_clear_ban {
		my $banman = new Natter::BanManager();
		my $ban_id = $in{ban_id} + 0;
		my $ban_type = ($in{ban_type} eq 'session') ? 'session' : 'ip';
		if(!$ban_id || $in{ban_type} ne $ban_type) {
			$response->appendBody(standardHTML("Sorry, I don't know what you're trying to do."));
			&Exit();
		} # end if
	# Need to add a check to ensure that the ban has already been lifted...
		if($ban_type eq 'session') {
			$banman->clearSessionBan($ban_id, $session->{data}->{guard});
		} else {
			$banman->clearIPBan($ban_id, $session->{data}->{guard});
		} # end if
		$response->appendBody(standardHTML(qq~
			The requested ban has been cleared, and will no longer appear in the ban list.
			<br />
			&raquo; <a href="$config->{GuardScriptName}?action=list_bans">Back to Ban List</a>
		~));
	} # end action_clear_ban


# Migrate bans from the old Storable format
	sub migrateBans {
	# Have we already performed the migration?
		return unless $config->{SessionPath};
		return if -f $config->{SessionPath} . '/migrated.cgi';
		return unless -f $config->{SessionPath} . '/ban.cgi';
	# Okay, let's get ugly.
		require 'Storable.pm';
		my $bans = Storable::retrieve($config->{SessionPath} . '/ban.cgi');
		return unless $bans;
		return unless ref $bans eq 'HASH';
		return unless scalar keys %$bans;
	# It's an actual hash, let's migrate!
		my $dbh = getDBHandle();
		my $sth = $dbh->prepare('
			INSERT INTO ip_bans(ip, reason, created, duration, lifted, created_by, lifted_by)
						VALUES(?, ?, ?, ?, ?, ?, ?)
		');
	# Sort by creation time, newest first
		foreach my $partial_ip (sort { $bans->{$b}->{STARTTIME} <=> $bans->{$a}->{STARTTIME} } keys %$bans) {
		# The partial IPs are stored like '123.456.789.' and '123.456.'
		# We need to add zeros.
			my $ban_info = $bans->{$partial_ip};
			my @boom = grep /\d+/, split /\./, $partial_ip;
			$boom[3] ||= '0';
			$boom[2] ||= '0';
			my $full_ip = join '.', @boom;
		# Can we get a duration?
			my $start_time = $ban_info->{STARTTIME};
			my $end_time = $ban_info->{TIME};
			my $duration = $end_time - $start_time;
		# Note: This duration will be bogus if the ban has been lifted.
			$sth->execute(
				$full_ip,
				($ban_info->{FOR} || '(no reason provided)'),
				$start_time,
				$duration,
				$end_time,
				$ban_info->{BY},
				(exists $ban_info->{LIFTEDBY} ? $ban_info->{LIFTEDBY} : undef)
			);
			$sth->finish();
		} # end foreach
	# Mark the bans as migrated.
		my ($fh,) = openFileAppend($config->{SessionPath} . '/migrated.cgi');
		print $fh time() . "\n";
		close $fh;
	} # end migrateBans

# Create the HTML for the banned user list
	sub createBanListHTML {
		my @bans = @_;
		my @ban_html;
		#use Data::Dumper;
		#print CGI::header();
		foreach my $ban (@bans) {
			#print Dumper $ban;
			next unless ref $ban eq 'HASH';
			#$ban = {
			#	id				=> 0
			#	token			=> '127.0.0.1' # or session id if it still exists
			#	token_type		=> 'ip' # or 'session'
			#	reason			=> 'reason as entered by guard',
			#	created			=> time(),
			#	duration		=> 0,
			#	lifted			=> time(), # in future
			#	cleared			=> 0, # or time() if cleared
			#	created_by		=> '',
			#	lifted_by		=> '',
			#	cleared_by		=> '',
			#}
		# What a mess.  Ban header
			my $string = '<tr><th colspan="2" align="left">'
					 . ($ban->{token_type} eq 'ip' ? 'IP Ban #' : 'Sess Ban #')
					 . $ban->{id}
					 . ', by '
					 . $ban->{created_by}
					 . '</th></tr>';
		# Created timestamp
			$string .= '<tr><td class="l">Created:</td><td class="t">'
					 . getTime($ban->{created})->strftime('%Y-%m-%d %H:%M:%S')
					 . '</td></tr>';
		# IP address, if an IP ban
			$string .= qq!<tr><td class="l">IP:</td><td><b>$ban->{token}</b></td></tr>! if $ban->{token_type} eq 'ip';
		# Reason
			$string .= qq!<tr><td class="l">Reason:</td><td>$ban->{reason}</td></tr>!;
		# Expires date, if not lifted
			$string .= '<tr><td class="l">Expires:</td><td class="t">'
					 . getTime($ban->{lifted})->strftime('%Y-%m-%d %H:%M:%S')
					 . '</td></tr>' if(!$ban->{lifted_by} && $ban->{lifted} > time());
		# Lift link.
			$string .= '<tr><td class="l" colspan="2">&raquo; <a href="'
					 . $config->{GuardScriptName}
					 . '?action=lift_ban&ban_id='
					 . $ban->{id}
					 . '&ban_type='
					 . $ban->{token_type}
					 . '">Lift Ban</a></td></tr>' if(!$ban->{lifted_by} && $ban->{lifted} > time() && !$ban->{cleared_by});
		# Expired / Lifted date, if expired or lifted
			$string .= '<tr><td class="l">'
					 . ($ban->{lifted_by} ? 'Lifted:' : 'Expired:')
					 . '</td><td class="t">'
					 . getTime($ban->{lifted})->strftime('%Y-%m-%d %H:%M:%S')
					 . '</td></tr>' if(($ban->{lifted} < time()) || $ban->{lifted_by});
		# Lifted guard name, if lifted
			$string .= '<tr><td class="l">Lifted By:</td><td>' . $ban->{lifted_by} . '</td></tr>' if $ban->{lifted_by};
		# Clear link.
			$string .= '<tr><td class="l" colspan="2">&raquo; <a href="'
					 . $config->{GuardScriptName}
					 . '?action=clear_ban&ban_id='
					 . $ban->{id}
					 . '&ban_type='
					 . $ban->{token_type}
					 . '">Clear '
					 . ($ban->{lifted_by} ? 'Lifted' : 'Expired')
					 . ' Ban</a></td></tr>' if((($ban->{lifted} < time()) || $ban->{lifted_by}) && !$ban->{cleared_by});
		# Cleared date, if cleared
			$string .= '<tr><td class="l">Cleared:</td><td class="t">'
					 . getTime($ban->{cleared})->strftime('%Y-%m-%d %H:%M:%S')
					 . '</td></tr>' if $ban->{cleared};
		# Cleared guard name, if cleared
			$string .= '<tr><td class="l">Cleared By:</td><td>' . $ban->{cleared_by} . '</td></tr>' if $ban->{cleared_by};
			$ban_html[scalar @ban_html] = $string;
		} # end foreach
		if(!scalar @ban_html) {
			@ban_html = ('<tr><th colspan="2">-none-</th></tr>');
		} # end if
		return '<table class="banlist">'
			 . join('<tr class="breaker"><td colspan="2"></td></tr>', @ban_html)
			 . '</table>';
	} # end createBanListHTML


# Cleanly exit, emitting the response and saving the user's session
	sub Exit {
		$session->markActive();
		$response->output() if $response->canOutput();
		exit(0);
	} # end Exit
