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
use JSON::PP;
use Natter::Session;
use Natter::HTTP_Request;
use Natter::HTTP_Response;
require "chat3_lib.cgi";

# All errors are handled by the standardHTML routine, courtesy CGI::Carp
	set_message(\&standardHTMLForErrors);

# Pull in our configuration information
	evalFile("./config.cgi");
	(defined &getConfig) ? (our $config = getConfigPlusDefaults()) : (die("I can't seem to find my configuration.\n"));

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
		$in{action} = 'intro';
	} # end if

# The user can't do anything at all unless he's logged in.
	if(!defined $session->{data}->{admin}) {
		$in{action} = 'authenticate';
	} # end if
# Make sure that the user still has admin privs
	our $dbh = getDBHandle();
	my($has_guard_privs,) = $dbh->selectrow_array('SELECT COUNT(*) FROM admin_users WHERE username = ? AND is_admin = 1', undef, $session->{data}->{admin});
	if(!$has_guard_privs) {
		$session->{data}->{admin} = undef;
		$in{action} = 'authenticate';
	} # end if

# Set up a list of valid subroutines that the outside world can get to...
	my %actions = (
		authenticate	=> \&action_authenticate,
		intro			=> \&action_intro,
		settings		=> \&action_settings,
		save_settings	=> \&action_save_settings,
		logins			=> \&action_logins,
		save_logins		=> \&action_save_logins,
		logout			=> \&action_logout,
	);

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



# Cleanly exit, emitting the response and saving the user's session
	sub Exit {
		$session->markActive();
		$response->output() if $response->canOutput();
		exit(0);
	} # end Exit




# Prompt the user to log in.
	sub action_authenticate {
	# If the user can be authenticated, do so and throw them at the intro page
		if($request->isPost()) {
			my $dbh = getDBHandle();
			my($success,) = $dbh->selectrow_array('SELECT COUNT(*) FROM admin_users WHERE is_admin = 1 AND username = ? AND password = ?', undef, $in{username}, Digest::MD5::md5_hex($in{password}));
			if($success == 1) {
			# Set both the admin and guard flags
				$session->{data}->{admin} = $in{username};
				$session->{data}->{guard} = $in{username};
				$response->addHeader('Status', '302 Found');
				$response->addHeader('Location', $config->{CPanelScriptName} . '?action=intro');
			} # end if
		} # end if
	# If not, the user will need to be prompted.
		if(!defined $session->{data}->{admin}) {
			my $error = ($request->isPost() || exists $in{username} || exists $in{password})
						? '<div style="color: red; font-weight: bold; margin: 10px; ">Invalid Credentials</div>'
						: '';
		# The user did not provide a username, or this wasn't the submit.  Show them the form.
			$response->setBody(standardHTML({
				header => "Enter Credentials",
				body => <<FORMBODY
$error
<form id="entrance" method="POST" action="$config->{CPanelScriptName}">
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


# Show the user a list of things he or she can do
	sub action_intro {
		$response->setBody(standardHTML({
			header => 'Chat Control Panel',
			body => <<WTB_TEMPLATE_LIBRARY_PST
<div class="cpanel-wrapper">
Welcome to the Chat Control Panel.  Please select an action to perform:
<ul>
	<li><a href="$config->{CPanelScriptName}?action=settings">Change Settings</a></li>
	<li><a href="$config->{CPanelScriptName}?action=logins">Manage Admin/Guard Logins</a></li>
	<li><a href="$config->{GuardScriptName}?action=frameset">View Chat Guard Frame</a></li>
	<li><a href="$config->{NonCGIURL}/chat.html">View Chat</a></li>
	<li><a href="$config->{CPanelScriptName}?action=logout">Log Out</a></li>
</ul>
</div>
WTB_TEMPLATE_LIBRARY_PST
,
			footer => undef,
		}));
	} # end action_intro


# Allow the user to manage settings
	sub action_settings {
	# Prep work, ugh.
	# Chat Name
		my $ChatName = CGI::escapeHTML($config->{ChatName});
	# Cookie Prefix
		my $CookiePrefix = CGI::escapeHTML($config->{CookiePrefix});
	# TimeZoneCode
		my @zone_names = sort { $a eq 'America' ? 0 : 1 } DateTime::TimeZone->categories();
		my $zone_list_html;
		foreach my $cat (@zone_names) {
			$zone_list_html .= '<optgroup label="'
							 . $cat
							 . '">'
							 . join('', map {
									'<option value="'
									. $cat
									. '/'
									. $_
									. '"'
									. ($config->{TimeZoneCode} eq $cat . '/' . $_ ? ' selected="selected"' : '')
									. '>'
									. $_
									. '</option>';
								} DateTime::TimeZone::names_in_category($cat)
								)
							 . '</optgroup>';
		} # end foreach
	# TimeZoneName
		my $TimeZoneName = CGI::escapeHTML($config->{TimeZoneName});
	# MultiChat
		my $MultiChatChecked = $config->{MultiChat} ? ' checked="checked"' : '';
	# DisableLamenessFilter
		my $DisableLamenessFilterChecked = $config->{DisableLamenessFilter} ? '' : ' checked="checked"';
	# EnableCaptions
		my $EnableCaptionsChecked = $config->{EnableCaptions} ? ' checked="checked"' : '';
	# DisableCaptionBR
		my $DisableCaptionBRChecked = $config->{DisableCaptionBR} ? '' : ' checked="checked"';
	# COPPAAge
		my $COPPAAge = $config->{COPPAAge} + 0;
	# CheckProxyForward
		my $CheckProxyForwardChecked = $config->{CheckProxyForward} ? ' checked="checked"' : '';
	# HttpBLAPIKey
		my $HttpBLAPIKey = CGI::escapeHTML($config->{HttpBLAPIKey});
	# ChatPassword
		my $ChatPassword = CGI::escapeHTML($config->{ChatPassword});
	# PasswordAttempts
		my $PasswordAttempts = $config->{PasswordAttempts} + 0;
	# BannedRedirect
		my $BannedRedirect = CGI::escapeHTML($config->{BannedRedirect});
	# CSSFile
		my %css_files = (
			'style.php' => 'default',
			'style_blue.php' => 'Blue',
			'style_bronze.php' => 'Bronze',
			'style_orange.php' => 'Orange',
		);
		my $CSSFile = '';
		foreach my $file (sort keys %css_files) {
			$CSSFile .= '<option value="'
			          . $file
					  . '"'
					  . ($config->{CSSFile} eq $file ? ' selected="selected"' : '')
					  . '>'
					  . $css_files{$file}
					  . '</option>';
		} # end foreach

	# Emit the HTML.
		$response->setBody(standardHTML({
			header => 'Chat Settings',
			body => <<YEGODS_SO_MUCH_HTML
<div class="cpanel-wrapper">
<br />
<form method="post" action="$config->{CPanelSriptName}">
<input type="hidden" name="action" value="save_settings" />
<table border="0" cellspacing="0" cellpadding="2" id="cpanel-settings" align="center" width="650">
	<caption style="text-align: left;">
	&laquo; <a href="$config->{CPanelScriptName}?action=intro">Back</a>
	</caption>

	<tr><th colspan="2">Basic Settings</th></tr>

	<tr><!-- ChatName -->
		<td class="l">
			Chat Name
			<br />
			<span>The name of the chat will appear in a number of places, including
			but not limited to the introduction screen and certain error messages.</span>
		</td>
		<td valign="top">
			<input type="text" name="ChatName" id="ChatName" value="$ChatName" size="30" />
		</td>
	</tr>

	<tr><!-- CookiePrefix -->
		<td class="l">
			Cookie Prefix
			<br />
			<span>If you run multiple chats on a single domain name, you will
			need to provide a unique cookie prefix for each, unless you have
			linked their databases together.  If this technobabble was too much
			for you, you can just leave this alone.</span>
		</td>
		<td valign="top">
			<input type="text" name="CookiePrefix" id="CookiePrefix" value="$CookiePrefix" size="10" />
		</td>
	</tr>

	<tr><!-- TimeZoneCode -->
		<td class="l">
			Time Zone Code
			<br />
			<span>Select the time zone geographically closest to a city or area
			in your desired <a href="http://en.wikipedia.org/wiki/Time_zone"
			target="_blank">time zone</a>.  If you're confused by this, picking
			America/Los_Angeles for the Pacific timezone or America/New_York
			for the Eastern timezone would probably be a good guess.  You may
			also wish to <a href="http://en.wikipedia.org/wiki/Zoneinfo"
			target="_blank">read more information about the Zoneinfo list</a>.</span>
		</td>
		<td valign="top">
			<select name="TimeZoneCode" id="TimeZoneCode">
				$zone_list_html
			</select>
		</td>
	</tr>

	<tr><!-- TimeZoneName -->
		<td class="l">
			Time Zone Name
			<br />
			<span>Time zone names are icky, and while I have no problem exposing
			you to them, exposing them to your users would be silly.  Pick a
			friendly name for the chat time zone, such as "Pacific" or "Eastern."</span>
		</td>
		<td valign="top">
			<input type="text" name="TimeZoneName" id="TimeZoneName" value="$TimeZoneName" size="15" />
		</td>
	</tr>

	<tr><th colspan="2">Feature Settings</th></tr>

	<tr><!-- CSSFile -->
		<td class="l">
			Stylesheet
			<br />
			<span>Which stylesheet file shall be used?</span>
		</td>
		<td valign="top">
			<select id="CSSFile" name="CSSFile">
				$CSSFile
			</select>
		</td>
	</tr>

	<tr><!-- MessageLimit -->
		<td class="l">
			Message Limit
			<br />
			<span>How many messages will appear in the messages frame?</span>
		</td>
		<td valign="top">
			<input type="text" name="MessageLimit" id="MessageLimit" value="$config->{MessageLimit}" size="3" />
			messages
		</td>
	</tr>

	<tr><!-- RefreshRate -->
		<td class="l">
			Refresh Rate
			<br />
			<span>How quickly will the messages frame update?</span>
		</td>
		<td valign="top">
			<input type="text" name="RefreshRate" id="RefreshRate" value="$config->{RefreshRate}" size="3" />
			seconds
		</td>
	</tr>

	<tr><!-- MultiChat -->
		<td class="l">
			Enable MultiChat
			<br />
			<span>MultiChat allows users to use multiple sets of names and colors
			within one chat frame.  If disabled, users that desire to chat under
			multiple names and colors will need to open multiple instances of
			the chat in their browser.</span>
		</td>
		<td valign="top">
			<input type="checkbox" name="MultiChat" id="MultiChat" value="1" $MultiChatChecked />
		</td>
	</tr>

	<tr><!-- DisableLamenessFilter -->
		<td class="l">
			Enable Lameness Filter
			<br />
			<span>When enabled, the Lameness Filter will prevent all-capital or
			mostly-captial posts from going through.  Fixed posts will be transformed
			into all lower-case.</span>
		</td>
		<td valign="top">
			<input type="checkbox" name="DisableLamenessFilter" id="DisableLamenessFilter" value="1" $DisableLamenessFilterChecked />
		</td>
	</tr>

	<tr><!-- EnableCaptions -->
		<td class="l">
			Enable Captions
			<br />
			<span>Captions are small blurbs of text, shown next to each chatter's
			name.  Captions can be used to describe mood, attitude, etc.</span>
		</td>
		<td valign="top">
			<input type="checkbox" name="EnableCaptions" id="EnableCaptions" value="1" $EnableCaptionsChecked />
		</td>
	</tr>

	<tr><!-- DisableCaptionBR -->
		<td class="l">
			Break After Captions
			<br />
			<span>When disabled, the name and caption will appear on the same line
			with each chat message.  When enabled, the name and caption will be
			displayed above each message.  You may wish to adjust the Message
			Limit to accomodate the extra space required by this feature.</span>
		</td>
		<td valign="top">
			<input type="checkbox" name="DisableCaptionBR" id="DisableCaptionBR" value="1" $DisableCaptionBRChecked />
		</td>
	</tr>

	<tr><th colspan="2">Security &amp; Protection</th></tr>

	<tr><!-- COPPAAge -->
		<td class="l">
			Minimum Chatter Age
			<br />
			<span>Depending on local or national laws, you may need to check the
			age of your users before permitting them to chat.  Set to zero to
			disable this feature.</span>
		</td>
		<td valign="top">
			<input type="text" name="COPPAAge" id="COPPAAge" value="$COPPAAge" size="3" />
		</td>
	</tr>

	<tr><!-- CheckProxyForward -->
		<td class="l">
			Trust X-Forwarded-For Header?
			<br />
			<span>Users behind proxy servers can be detected by using this HTTP
			header.  Beware that this header can be forged by malicious users.
			If you don't know what this means, leave this disabled.</span>
		</td>
		<td valign="top">
			<input type="checkbox" name="CheckProxyForward" id="CheckProxyForward" value="1" $CheckProxyForwardChecked />
		</td>
	</tr>

	<tr><!-- HttpBLAPIKey -->
		<td class="l">
			Http:BL API Key
			<br />
			<span>If you have an Http:BL API key from Project Honeypot and wish
			to use it to filter users, please enter the key here.  If you don't
			know what this means, leave this field blank.</span>
		</td>
		<td valign="top">
			<input type="text" name="HttpBLAPIKey" id="HttpBLAPIKey" value="$HttpBLAPIKey" size="20" />
		</td>
	</tr>

	<tr><!-- ChatPassword -->
		<td class="l">
			Chat Password
			<br />
			<span>Users will be required to provid this password before they enter
			the chat.  Leave this blank to not require a password.</span>
		</td>
		<td valign="top">
			<input type="text" name="ChatPassword" id="ChatPassword" value="$ChatPassword" size="15" />
		</td>
	</tr>

	<tr><!-- PasswordAttempts -->
		<td class="l">
			Password Attempts
			<br />
			<span>If users fail entering the password more than this many times,
			they will be prevented from attempting again for up to half an hour.</span>
		</td>
		<td valign="top">
			<input type="text" name="PasswordAttempts" id="PasswordAttempts" value="$PasswordAttempts" size="3" />
		</td>
	</tr>

	<tr><!-- BannedRedirect -->
		<td class="l">
			Banned Redirect URL
			<br />
			<span>If you wish to direct users to another web site when they have
			been banned, enter the full and complete URL to the site here.</span>
		</td>
		<td valign="top">
			<input type="text" name="BannedRedirect" id="BannedRedirect" value="$BannedRedirect" size="30" />
		</td>
	</tr>

</table>
<br />
<center>
	<input type="submit" value="Save Settings" class="button" />
</center>
</form>
</div>
<br /><br />
YEGODS_SO_MUCH_HTML
,
			footer => undef,
		}));
	} # end action_settings


# Save changes to settings
	sub action_save_settings {
		my @string_settings = qw~
			TimeZoneCode TimeZoneName ChatName HttpBLAPIKey BannedRedirect ChatPassword CSSFile
		~;
		my @numeric_settings = qw~
			MessageLimit RefreshRate COPPAAge PasswordAttempts
		~;
		my @bool_settings = qw~
			EnableCaptions CheckProxyForward MultiChat
		~;
		my @negative_bool_settings = qw~
			DisableLamenessFilter DisableCaptionBR
		~;
		my $dbh = getDBHandle();
		$dbh->do('BEGIN TRANSACTION');
		$dbh->do('DELETE FROM settings');
		my $sth = $dbh->prepare('INSERT INTO settings(name,value) VALUES(?,?)');
		foreach my $setting_name (@numeric_settings) {
			$sth->execute($setting_name, $in{$setting_name} + 0);
		} # end foreach
		foreach my $setting_name (@bool_settings) {
			$sth->execute($setting_name, (int $in{$setting_name} ? 1 : 0));
		} # end foreach
		foreach my $setting_name (@negative_bool_settings) {
			$sth->execute($setting_name, ($in{$setting_name} ? 0 : 1));
		} # end foreach
		foreach my $setting_name (@string_settings) {
			$sth->execute($setting_name, $in{$setting_name});
		} # end foreach
		$sth->finish();
		$dbh->do('COMMIT');

		$response->setBody(standardHTML({
			header => 'Settings Saved',
			body => qq~
<div class="cpanel-wrapper">
Your settings have been saved.
<br />
&raquo; <a href="$config->{CPanelScriptName}?action=intro">Return to Control Panel</a>
</div>~,
			footer => undef,
		}));
	} # end action_save_settings


# Allow the user to manage user logins
	sub action_logins {
		my $dbh = getDBHandle();
		my $sth = $dbh->prepare('SELECT * FROM admin_users ORDER BY username ASC');
		$sth->execute();
		my @user_html;
		while(my $row = $sth->fetchrow_hashref) {
			my $sane_name = CGI::escapeHTML($row->{username});
			my $admin_checked = $row->{is_admin} ? 'checked="checked"' : '';
			my $guard_checked = $row->{is_guard} ? 'checked="checked"' : '';
			my $delete = qq~<input type="checkbox" name="delete-$sane_name" id="delete-$sane_name" />~;
			if($session->{data}->{admin} eq $row->{username}) {
				$delete = '--';
				$admin_checked .= ' disabled="disabled"';
				$guard_checked .= ' disabled="disabled"';
			} # end if
			push @user_html, qq~
			<tr>
				<td align="center">$delete</td>
				<td><b>$row->{username}</b></td>
				<td><input type="text" size="10" name="password-$sane_name" id="password-$sane_name" value="" autocomplete="off" /></td>
				<td align="center"><input type="checkbox" name="admin-$sane_name" id="admin-$sane_name" $admin_checked value="1" /></td>
				<td align="center"><input type="checkbox" name="guard-$sane_name" id="guard-$sane_name" $guard_checked value="1" /></td>
			</tr>
			~
		} # end while
		$sth->finish();
		my $user_html = join '', @user_html;
		use Data::Dumper;
		$response->setBody(standardHTML({
			header => 'Manage Admin/Guard Logins',
			footer => undef,
			body => qq~
<br />
<div class="cpanel-wrapper">
<form method="post" action="$config->{CPanelScriptName}">
<input type="hidden" name="action" value="save_logins" />
<table id="cpanel-login-list" border="0" cellspacing="0" cellpadding="2" align="center">
	<caption style="text-align: left;">
	&laquo; <a href="$config->{CPanelScriptName}?action=intro">Back</a>
	</caption>

	<thead>
		<tr>
			<th>Del?</th>
			<th>Username</th>
			<th>Password</th>
			<th>Admin?</th>
			<th>Guard?</th>
		</tr>
	</thead>
	<tbody>
		$user_html
		<tr>
			<th colspan="5">Add New Login</th>
			<tr>
				<td>&nbsp;</td>
				<td><input type="text" size="10" name="new-username" id="new-username" value="" /></td>
				<td><input type="text" size="10" name="new-password" id="new-password" value="" autocomplete="off" /></td>
				<td align="center"><input type="checkbox" name="new-admin" id="new-admin" checked="checked" value="1" /></td>
				<td align="center"><input type="checkbox" name="new-guard" id="new-guard" checked="checked" value="1" /></td>
			</tr>
		</tr>
	</tbody>
</table>
<br />
<center>
	<input type="submit" value="Save Changes" />
</center>
</form>
</div>
<br />
~
		}));
	} # end action_logins


# Save changes to logins
	sub action_save_logins {
		my $dbh = getDBHandle();
		$dbh->do('BEGIN TRANSACTION');
		my $sth = $dbh->prepare('SELECT * FROM admin_users ORDER BY username ASC');
		$sth->execute();
		my @user_html;
		while(my $row = $sth->fetchrow_hashref) {
			if($row->{username} ne $session->{data}->{admin} && $in{'delete-' . $row->{username}}) {
				$dbh->do('DELETE FROM admin_users WHERE username = ?', undef, $row->{username});
				next;
			} # end if
		# Update admin/guard status for existing users *except* the current user
			if($row->{username} ne $session->{data}->{admin}) {
				$dbh->do(
					'UPDATE admin_users SET is_admin = ?, is_guard = ? WHERE username = ?',
					undef,
					$in{'admin-' . $row->{username}} ? 1 : 0,
					$in{'guard-' . $row->{username}} ? 1 : 0,
					$row->{username}
				);
			} # end if
		# Update password if needed
			if($in{'password-' . $row->{username}} && length $in{'password-' . $row->{username}}) {
				$dbh->do(
					'UPDATE admin_users SET password = ? WHERE username = ?',
					undef,
					Digest::MD5::md5_hex($in{'password-' . $row->{username}}),
					$row->{username}
				);
			} # end if
		} # end while
		$sth->finish();
	# Do we have a new user to add?
		my $err = '';
		if($in{'new-username'} && $in{'new-password'} && ($in{'new-admin'} || $in{'new-guard'})) {
			my($dupe_check,) = $dbh->selectrow_array('SELECT COUNT(*) FROM admin_users WHERE username = ?', undef, $in{'new-username'});
			if(!$dupe_check) {
				$dbh->do(
					'INSERT INTO admin_users(username, password, is_admin, is_guard) VALUES(?,?,?,?)',
					undef,
					$in{'new-username'},
					Digest::MD5::md5_hex($in{'new-password'}),
					($in{'new-admin'} ? 1 : 0),
					($in{'new-guard'} ? 1 : 0),
				);
			} else {
				$err = 'Your changes to admin/guard logins have been saved, but there was an error while adding the new user:<br />Username already in use, please try again.';
			} # end if
		} # end if
		$err ||= 'Your changes to admin/guard logins have been saved.';
		$dbh->do('COMMIT');
		$response->setBody(standardHTML({
			header => 'Settings Saved',
			body => qq~
<div class="cpanel-wrapper">
$err
<br />
&raquo; <a href="$config->{CPanelScriptName}?action=intro">Return to Control Panel</a>
</div>~,
			footer => undef,
		}));
	} # end action_save_logins


# Log the user out.
	sub action_logout {
		$session->{data}->{admin} = undef;
		$response->addHeader('Status', '302 Found');
		$response->addHeader('Location', $config->{CPanelScriptName} . '?action=authenticate');
	} # end action_logout
