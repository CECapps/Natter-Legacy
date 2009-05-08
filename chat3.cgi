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

# This code was designed when the COPPA law was interpreted more striclty than
# it was now.  The minimum entry age can be dictated in the config, or disabled.
# If the user flagged themselves as underage, stop right here.
	noEntry_COPPA() if(defined $session->{data}->{COPPA} && $session->{data}->{COPPA} eq "under");

# If the user has been kicked or banned, stop right here.
	my $ban_duration = $session->isBanned();
	noEntry_KickBan($ban_duration, $session->{data}->{kick_reason}) if($ban_duration);

# No bogus actions, please
	if((!exists $in{action}) || ($in{action} eq "")) {
		$in{action} = $config->{ChatPassword} ? 'password_prompt' : 'intro';
	} # end if

# Set up a list of valid subroutines that the outside world can get to...
	my %actions = (
		intro => \&action_intro,
		coppa => \&action_coppa,
		post => \&action_post,
		password_prompt => \&action_password_prompt,
		password_check => \&action_password_check,
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





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# action_ subroutines

# If passwords are enabled, prompt the user to enter one
	sub action_password_prompt {
	# Check the session, is the user already OK?
		if(!$config->{ChatPassword} || (defined $session->{data}->{password} && $session->{data}->{password} eq $config->{ChatPassword})) {
			action_intro();
			return;
		} # end if
	# Otherwise, check to see if their IP has had too many tries.  Yes, this
	# is done outside the realm of the session, to try and fight off brute-force
	# cracking attempts.  Not that I seriously expect this to be a real problem.
		my $dbh = getDBHandle();
		my $record = $dbh->selectrow_arrayref('SELECT tries, last_try FROM floodcheck WHERE ip = ?', undef, currentIP());
		my $tries = $record->[0] + 0;
		my $last_try = $record->[1] + 0;
	# Reset their tries after half an hour
		my $now = time();
		$tries = 0 if($last_try < $now - (60 * 30));
	# Too many tries?  No entry for you.
		noEntry_TooManyTries() if($tries >= $config->{PasswordAttempts});
	# How many tries are left?
		my $tries_left = $config->{PasswordAttempts} - $tries;
		my $tries_wording = $tries_left == $config->{PasswordAttempts} ? '' : "You have <b>$tries_left</b> tries remaining.";
	# Prompt the user.
		$response->appendBody(standardHTML({
			header => "Welcome to $config->{ChatName}",
			body => <<PASSWORD_PROMPT
<script type="text/javascript">
\$().ready(function(){ \$('#frm').show(); \$('#js').hide(); });
</script>
This chat is now password protected.  $tries_wording Please enter the password:
<br /><br />
<form action="$config->{ScriptName}" method="post" name="frm" id="frm" style="display: none">
<input type="hidden" name="action" value="password_check">
	<input type="text" size="10" name="password" id="password" class="textbox" />
	<input type="submit" value="Check Password" class="button" />
</form>
<div id="js">If you do not see a password prompt, please enable Javascript in your browser.</div>
PASSWORD_PROMPT
			,
			footer => '',
		}));
	} # end action_password_prompt

# If passwords are enabled and the user provided one, check it
	sub action_password_check {
	# No session check here.
		my $dbh = getDBHandle();
		my $record = $dbh->selectrow_arrayref('SELECT tries, last_try FROM floodcheck WHERE ip = ?', undef, currentIP());
		my $tries = $record->[0];
		my $last_try = $record->[1];
		my $now = time();
	# Is this their first try?
		if(!$tries) {
			$dbh->do('INSERT OR IGNORE INTO floodcheck(tries, last_try, ip) VALUES(0, ?, ?)', undef, $now, currentIP());
		} # end if
		noEntry_TooManyTries() if($tries > $config->{PasswordAttempts});
	# Did they enter the proper password?  If so, intro'em.
		if($tries <= $config->{PasswordAttempts} && $in{'password'} eq $config->{ChatPassword}) {
			$session->{data}->{password} = $config->{ChatPassword};
			return action_intro();
		} # end if
	# It must be a failure.
		$dbh->do('UPDATE floodcheck SET tries = tries + 1, last_try = ? WHERE ip = ?', undef, $now, currentIP());
		$response->appendBody(standardHTML({
			header => 'Wrong Password',
			body => qq~<br />Wrong password, no cookie!  <a href="$config->{ScriptName}?action=password_prompt">Try again?</a>~,
			footer => '',
		}));
	} # end action_password_check

# Say hi to the user, ask them to indicate their age
	sub action_intro {
	# Set a sanity token for later checking -- this ensures that the user accepts cookies
		$session->{data}->{sanity} = 1;
	# Check for the passwordy bits
		noEntry_MissingPassword() if($config->{ChatPassword} && (!defined $session->{data}->{password} || $session->{data}->{password} ne $config->{ChatPassword}));
	# If they've already done the age check, throw them at the post form.
		if(defined $session->{data}->{COPPA} && $session->{data}->{COPPA} eq 'over') {
			$response->addHeader('Status', '302 Found');
			$response->addHeader('Location', $config->{ScriptName} . '?action=post');
			&Exit();
		} # end if
	# Otherwise, prompt them for the required age check
		if($config->{COPPAAge}) {
			$response->appendBody(standardHTML({
				header => "Welcome to $config->{ChatName}",
				body => <<COPPA_CHECK
Thank you for visiting.  In order to enter this chat, you must verify your age.
<br />
<br />
<a href="$config->{ScriptName}?action=coppa&check=over">I am $config->{COPPAAge} or older.</a>
&nbsp; &nbsp; | &nbsp; &nbsp;
<a href="$config->{ScriptName}?action=coppa&check=under">I am under $config->{COPPAAge}.</a>
COPPA_CHECK
,
				footer => "",
			}));
		} else {
			$response->appendBody(standardHTML({
				header => "Welcome to $config->{ChatName}",
				body => <<COPPA_CHECK
Thank you for visiting.  Please be sure to read the rules before joining the chat.
<br />
<br />
<a href="$config->{ScriptName}?action=coppa&check=over">Enter Chat</a>
COPPA_CHECK
,
				footer => "",
			}));
		} # end if
	} # end sub


# Make sure the user is the correct age for the chat
	sub action_coppa {
	# Check for the sanity session flag
		noEntry_Insane() unless defined $session->{data}->{sanity} && $session->{data}->{sanity} == 1;
	# Check for the passwordy bits
		noEntry_MissingPassword() if($config->{ChatPassword} && (!defined $session->{data}->{password} || $session->{data}->{password} ne $config->{ChatPassword}));
	# If they forged the form, they're underage
		my $this = ($in{check} =~ m/^(over|under)$/ ? $in{check} : "under" );
	# If they're underage, kick'em out.
		if($this eq "under") {
			$session->{data}->{COPPA} = 'under';
			noEntry_COPPA();
			&Exit();
		}
	# Otherwise they get to notify everyone that they've entered the chat
		else {
			$session->{data}->{COPPA} = 'over';
			$response->addHeader('Status', '302 Found');
			$response->addHeader('Location', $config->{ScriptName} . '?action=post;special=entrance');
			&Exit();
		} # end if
	} # end sub



# Post a new message / retrieve the posting form
	sub action_post {
	# Check for the sanity session flag
		noEntry_Insane() unless defined $session->{data}->{sanity} && $session->{data}->{sanity} == 1;
	# Check for the passwordy bits
		noEntry_MissingPassword() if($config->{ChatPassword} && (!defined $session->{data}->{password} || $session->{data}->{password} ne $config->{ChatPassword}));

	# If the user posted a message, add it
		my $added_chat_message;
		if(exists $in{'username'}) {
			my %data = formatInput();
			%in = %data;
			my $log_line = updateMessages();
			$added_chat_message = $log_line ? 1 : 0;
			updateLog($log_line);
		} # end if
	# If the user should post a entrance line, add it now
		if(!$added_chat_message && defined $in{special} && $in{special} eq "entrance") {
			my $log_line = updateMessages();
			$added_chat_message = $log_line ? 1 : 0;
			updateLog($log_line);
		} # end if
	# Update the guard/ban list of users
		updatePostlog() if $added_chat_message;
	# If this is an ajax request, we'll want to return json...
		if($request->isAjax()) {
			$response->setContentType('application/json');
			$response->setBody(JSON::PP::encode_json(generatePostForm(1)));
		} else {
		# Feed the form back to them
			$response->appendBody(standardHTML({
				header => "",
				body => generatePostForm(),
				footer => "",
				no_powered => 1,
			}));
		} # end if
		&Exit();
	} # end sub



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Common library subroutines

# Sanitize and format the input from the post form
	sub formatInput {
		my %filter = %in;

	# Strip newlines, extra spaces
		foreach (qw(username url caption mcolor color)) {
			chomp($filter{$_});
			$filter{$_} =~ s!<br ?/?>!\n!gi;
			$filter{$_} =~ s/[\n\r]//gis;
			$filter{$_} =~ s/\s+$//gi;
			$filter{$_} =~ s/^\s+//gi;
		} # end foreach

	# HTMLize username and message
		$filter{'username'} = formatHTML($in{'username'}, {a => 1, autolink => 1});
		$filter{'message'} = formatHTML($in{'message'});
		$filter{'caption'} = formatHTML($in{'caption'});

	# Process markup in message and name
		$filter{'message'} = formatMarkup($filter{'message'});
		$filter{'username'} = formatMarkup($filter{'username'});

	# Filters for URL
		if($filter{'url'} ne "URL") {
			$filter{'url'} = ( $filter{'url'} =~ m!^(http|ftp|https)://! ? $filter{'url'} : "http://" . $filter{'url'} );
			$filter{'url'} = ( $filter{'url'} =~ m!^((http|ftp|https)://)?\S+\.\S+$! ? $filter{'url'} : "URL" );
		} # end if

	# Filters for email (replaces Caption when Caption is disabled)
		if(!$config->{EnableCaptions} && $filter{'caption'} ne "E-Mail") {
			$filter{'caption'} = ( $filter{'caption'} =~ m!^\S+\@\S+\.\S{2,4}$! ? $filter{'caption'} : "E-Mail" );
		} # end if

	# Filters for colors
		foreach (qw(color mcolor)) {
			$filter{$_} = '' if($filter{$_} eq 'Message Color');
			$filter{$_} = fix_color($filter{$_});
			$filter{$_} = '' if($filter{$_} eq "#");
		} # end foreach
		$filter{'color'} = 'white' if(!$filter{'color'} || $filter{'color'} eq '');

	# Okay, we're done
		return %filter;
	} # end formatInput


# Sanitize HTML provided by the user
	sub formatHTML {
		my $value = shift;
		my $flags = shift;
		$flags = {} unless ref($flags) eq "HASH";

	# Strip all tags with parens inside (Javascript)
		$value =~ s!<[^><]+?(\(|\))[^><]+?>!!gi;

	# Neutralize HTML
		$value =~ s!<!&lt;!gi;

	# Convert newlines (if any)
		$value =~ s/\r//gis;
		$value =~ s/\n{3,}/\n/gis;
		$value =~ s/\n/<br \/>/gis;

	# Allow select tags
		my @allow_tags = qw(b sub sup pre i u s big small strike center);
		foreach my $stwing (@allow_tags) {
			$value =~ s!&lt;($stwing)(>)(.*?)&lt;/(\1)([ >])!<$1$2$3</$4$5!gis;
		} # end foreach

	# Convert <font>
		$value = formatHTMLfont($value) unless $flags->{font};

	# Autolink
		$value = formatHTMLautolink($value) unless $flags->{autolink};

	# Convert <a>
		$value = formatHTMLa($value) unless $flags->{a};

	# Convert <span style="">
		$value = formatHTMLspan($value) unless $flags->{span};

	# try to fix color monger idiocy
		$value =~ s!\&lt\;\/u>\&lt\;\/s>(\<\/i>)?(\<\/b>)?\&lt\;\/font>\&lt\;\/font>\&lt\;\/font>!$1$2!g;
		return $value;
	} # end formatHTML

# Attempt to sanitize the <font> tag.
	sub formatHTMLfont {
		my $value = shift;

	# Don't process unless start and end tags match
		my($starts, $ends) = (0,0);
		while($value =~ m/&lt;font /gi) { $starts++ }
		while($value =~ m/&lt;\/font[\s >]/gi) { $ends++ }
		if($starts <= $ends) {
			my $c = $starts;
			while($c > 0) {
				$value =~ s!&lt;font([^><]+)>(.*?)&lt;/font>!<font$1>$2</font>!i;
				$c--;
			} # end while
		} else {
			$value =~ s!&lt;font([^><]+)>(.*?)&lt;/font>!<font$1>$2</font>!gi;
		} # end if

		return $value;
	} # end formatHTMLfont

# Attempt to sanitize the <a> tag.
	sub formatHTMLa {
		my $value = shift;

		# Don't process unless start and end tags match
		my($starts, $ends) = (0,0);
		while($value =~ m/&lt;a /gi) { $starts++ }
		while($value =~ m/&lt;\/a>/gi) { $ends++ }
		return $value unless $starts == $ends;

		# Forcefully reformat the tag
		$value =~ s!&lt;a[^>]*href=\"([^\"\'\`]+?)\"[^>]*>(.*?)&lt;/a>!<a href="$1" target="_blank">$2</a>!gis;

		return $value;
	} # end formatHTMLa

# Attempt to sanitize the <span> tag.  This is dangeorus.
	sub formatHTMLspan {
		my $value = shift;

		# Don't process unless start and end tags match
		my($starts, $ends) = (0,0);
		while($value =~ m/&lt;span /gi) { $starts++ }
		while($value =~ m/&lt;\/span>/gi) { $ends++ }
		return $value unless $starts == $ends;

		# Forcefully reformat the tag
		my $reformat = 1;
		while($reformat > 0) {
			$reformat = 0;
			$reformat++ if $value =~ s!&lt;span[^>]*style=\"([^\"\'\`]+?)\"[^>]*>(.*?)&lt;/span>!<span style="$1">$2</span>!gis;
			$reformat++ if $value =~ s!&lt;span[^>]*class=\"([^\"\'\`]+?)\"[^>]*>(.*?)&lt;/span>!<span class="$1">$2</span>!gis;
			$reformat++ if $value =~ s!&lt;span[^>]*id=\"([^\"\'\`]+?)\"[^>]*>(.*?)&lt;/span>!<span id="$1">$2</span>!gis;
			$reformat++ if $value =~ s!&lt;span[^>]*title=\"([^\"\'\`]+?)\"[^>]*>(.*?)&lt;/span>!<span title="$1">$2</span>!gis;
		} # end while

		return $value;
	} # end formatHTMLspan

# Attempt to auto-link URL-like strings
	sub formatHTMLautolink {
		# Courtesy UBB
		my $check = shift;
		$check =~ s/(^|\s)(http:\/\/\S+)(\.|\,|\))?/$1<a href="$2" target="_blank">$2<\/a>$3/isg;
		$check =~ s/(^|\s)(https:\/\/\S+)(\.|\,|\))?/$1<a href="$2" target="_blank">$2<\/a>$3/isg;
		$check =~ s/(^|\s)(www\.\S+)(\.|\,|\))?/$1<a href="http:\/\/$2" target="_blank">$2<\/a>$3/isg;

		return ($check);
	} # end formatHTMLautolink

# Attempt to apply BBCode markup and provide other sanitizization
	sub formatMarkup {
		my $this = shift;
		my $thart = $this;

	# JeffK filter
		my($uppers, $lowers) = (0, 0);
		my $these = $this;
		$these =~ s/\<.+?\>//g;
		while($these =~ m/[A-Z]/g) { $uppers++; }
		while($these =~ m/\d/g) { $uppers++; }
		while($these =~ m/[a-z]/g) { $lowers++; }
		my $totals = $uppers + $lowers;
		if(!$config->{DisableLamenessFilter} && ($totals > 10) && (($uppers / $totals) > 0.75)) {
			$this = lc($this);
		} # end if
	# Don't process if there's nothing to process
		return $this unless $this =~ m/\[.+\]/;
	# Grab a subset of BBCode
		my $match = 1;
		my $cycles = 0;
		while($match != 0 && $cycles < 100) {
			$cycles++;
			$match = 0;
			$match++ if $this =~ s/(\[(monger|gradient)(=([a-zA-Z0-9\,\#]+))?\])(.+?)\[\/(?:monger|gradient)\]/formatMongerMarkup($4, $5)/isge;
			$match++ if $this =~ s/(\[color(=([a-zA-Z0-9\,\#]+))\])(.+?)\[\/color\]/formatColorMarkup($3, $4)/isge;
			$match++ if $this =~ s/\[small\](.+?)\[\/small\]/<span style="font-size: 85%;">$1<\/span>/isg;
			$match++ if $this =~ s/\[big\](.+?)\[\/big\]/<span style="font-size: 120%;">$1<\/span>/isg;
			$match++ if $this =~ s/\[s(?:trike)?\](.+?)\[\/s(?:trike)?\]/<span style="text-decoration: line-through">$1<\/span>/isg;
			$match++ if $this =~ s/\[u(?:nder(?:line)?)?\](.+?)\[\/u(?:nder(?:line)?)?\]/<span style="text-decoration: underline">$1<\/span>/isg;
			$match++ if $this =~ s/\[sub(?:script)?\](.+?)\[\/sub(?:script)?\]/<sub>$1<\/sub>/isg;
			$match++ if $this =~ s/\[sup(?:er(?:script)?)?\](.+?)\[\/sup(?:er(?:script)?)?\]/<sup>$1<\/sup>/isg;
			$match++ if $this =~ s/(\[URL\])(http|https|ftp)(:\/\/\S+?)(\[\/URL\])/ <a href="$2$3" target="_blank">$2$3<\/a> /isg;
			$match++ if $this =~ s/(\[URL\])(\S+?)(\[\/URL\])/ <a href="http:\/\/$2" target="_blank">$2<\/a> /isg;
			$match++ if $this =~ s/(\[URL=)(http|https|ftp)(:\/\/\S+?)(\])(.+?)(\[\/URL\])/<a href="$2$3" target="_blank">$5<\/a>/isg;
			$match++ if $this =~ s/(\[URL=)(\S+?)(\])(.+?)(\[\/URL\])/<a href="http:\/\/$2" target="_blank">$4<\/a>/isg;
			$match++ if $this =~ s/(\[EMAIL\])(\S+\@\S+?)(\[\/EMAIL\])/ <a href="mailto:$2">$2<\/a> /isg;
			$match++ if $this =~ s/(\[i\])(.+?)(\[\/i\])/<i>$2<\/i>/isg;
			$match++ if $this =~ s/(\[b\])(.+?)(\[\/b\])/<b>$2<\/b>/isg;
		} # end while
		return $this;
	} # end formatMarkup

# Set an HTML color (via markup)
	sub formatColorMarkup {
		my @colors = map { fix_color($_) } split /\,/, shift;
		my $text = shift;
		if(scalar @colors == 1) {
			return qq~<span style="color: $colors[0]">$text</span>~;
		} elsif(scalar @colors == 2) {
			return qq~<span style="color: $colors[0]; background-color: $colors[1]">$text</span>~;
		} # en dif
		return $text;
	} # end formatColorMarkup

# Generate an HTML gradient (via markup)
	sub formatMongerMarkup {
	# Take the comma separated list and fix it.
		my $color_list = shift;
		if(!defined $color_list) {
		# Skip back to the name and message colors if there were no paramaters.
			$color_list = $in{color} . ',' . ($in{mcolor} eq "Message Color" ? $in{color} : $in{mcolor});
		} # end if
		my @colors = map { my $x = fix_color($_); $x =~ s/\#//; $x; } split /\,/, $color_list;
	# What's our text look like?
		my $text = shift;
	# Don't bother processing unless there's a gradient to be made.
		return $text if(scalar @colors == 1);
	# Don't bother processing if all the colors are the same.
		my %unique_colors = map { $_ => 1 } @colors;
		return $text if( scalar keys %unique_colors == 1 );
	# Most of the time, we'll be handed two colors.  This is easy, do it now.
		if(scalar @colors == 2) {
			my @mongered_characters = processMonger($colors[0], $colors[1], $text);
			return join '', @mongered_characters;
		} # end if
	# The user provided more than two colors.  Split the text up into chunks.
		my $chunk_count = scalar @colors;
		$chunk_count--;
		my $character_count = length $text;
		my $chars_per_chunk = $character_count / $chunk_count;
	# We can't process the chunks unless we have at least two characters per chunk.
		return $text if($chars_per_chunk < 2);
		my @chunks;
		my $chunk_num = 0;
		my $char_num = 0;
		my $total_chars = 0;
		foreach my $character ( split //, $text ) {
			$chunks[ $chunk_num ] .= $character;
			$char_num++;
			$total_chars++;
			if($char_num > $chars_per_chunk && $total_chars < $character_count) {
				$chunk_num++;
				$char_num = 0;
			} # end if
		} # end foreach
	# We now have a list of chunks.  Chances are that they're not equal in length.
	# The last chunk has a tendency to be a bit short.  If it's only one character
	# in length, and the previous chunk is at least three, steal the last character
	# from the previous chunk and give it to the last one.
		if(length $chunks[$chunk_num] == 1 && length $chunks[ ($chunk_num - 1) ] > 2) {
			$chunks[$chunk_num] = substr($chunks[ ($chunk_num - 1) ], -1, 1, '') . $chunks[$chunk_num];
		} # end if
	# To make the gradient prettier, copy letters from chunk to chunk - 1.
	# These will be removed later, and is the sole reason that the process function
	# returns an array instead of a string.  <_<
		foreach my $chunk_id ( 0 .. $chunk_count - 2 ) {
			$chunks[$chunk_id] .= substr $chunks[ ($chunk_id + 1) ], 0, 1;
		} # end foreach
	# Now, mongerize each chunk.
		my @mongered_chunks;
		foreach my $chunk_id ( 0 .. $chunk_count - 1 ) {
			my $from_color = $colors[ $chunk_id ];
			my $to_color = $colors[ $chunk_id + 1 ] ? $colors[ $chunk_id + 1 ] : $colors[ $chunk_id  ];
			my @html = processMonger($from_color, $to_color, $chunks[ $chunk_id ]);
			pop @html if $chunk_id < $chunk_count - 1;
			$mongered_chunks[ $chunk_id ] = join '', @html;
		} # end foreach
		return join '', @mongered_chunks;
		#return $text;
		# [monger=red,green,blue]1234567890abcdefghijklmnopqrstuvwxyz[/monger]
		# [monger=yellow,orange,red,purple,blue,green,yellow]TASTETHERAINBOWKTHX[/monger]
		# [monger=yellow,orange,red,purple,blue,green,yellow]aXslightlyXdifferentXstringXtoXtryXitXoutXandXstuff[/monger]
		# TA STE TH ERA INB OWK THX
	} # end formatMongerMarkup

# Create an HTML gradient (core of formatMonger)
	sub processMonger {
		my $from_rgb = extractRGBComponentsFromHexColor(shift);
		my $to_rgb = extractRGBComponentsFromHexColor(shift);
		my $characters = shift;
	# What's the difference between the colors?
		my $red_step 	= ($from_rgb->[0] - $to_rgb->[0]) / length $characters;
		my $green_step 	= ($from_rgb->[1] - $to_rgb->[1]) / length $characters;
		my $blue_step 	= ($from_rgb->[2] - $to_rgb->[2]) / length $characters;
	# Begin the transformation!
		my @chars;
		my @color_round = @$from_rgb;
		foreach my $character ( split //, $characters ) {
			my $hexcolor = assembleHexColorFromRGBComponents(@color_round);
			$chars[ scalar @chars ] = '<font color="#' . $hexcolor . '">' . $character . '</font>';
			$color_round[0] -= $red_step;
			$color_round[1] -= $green_step;
			$color_round[2] -= $blue_step;
		} # end foreach
		return @chars;
	} # end processMonger

# Given a hex color, return the *decimal* components of Red, Green, and Blue.
	sub extractRGBComponentsFromHexColor {
		$_[0] =~ m/^(..)(..)(..)$/ or return [0, 0, 0];
		return [hex($1), hex($2), hex($3)];
	} # end extractRGBComponentsFromHexColor

# Given Red, Green, and Blue *decimal* values, return a hex color.
	sub assembleHexColorFromRGBComponents {
		my $red = sprintf '%x', int shift;
		my $green = sprintf '%x', int shift;
		my $blue = sprintf '%x', int shift;
		$red = '0' . $red if length $red == 1;
		$green = '0' . $green if length $green == 1;
		$blue = '0' . $blue if length $blue == 1;
		return $red . $green . $blue;
	} # end assembleHexColorFromRGBComponents

# Generate the HTML responsible for the posting form
	sub generatePostForm {
		my $return_hash = shift;
		my %clone;
	# Hash slices don't work like I'd like them to.
		$clone{username} =		$in{username};
		$clone{url} =			$in{url};
		$clone{color} =			$in{color};
		$clone{mcolor} =		$in{mcolor};
		$clone{caption} =		$in{caption};
	# Fields are labled by replacing the value with the label when there's no value
		$clone{'username'} = $in{username} || "Name";
		$clone{'url'} = CGI::escapeHTML($clone{'url'}) || "URL";
		$clone{'mcolor'} = CGI::escapeHTML(getColorName($clone{'mcolor'})) || "Message Color";
		$clone{'color'} = CGI::escapeHTML(getColorName($clone{'color'})) || "white";
	# The caption field replaces the email field, if the caption field is used
		if($config->{EnableCaptions}) {
			$clone{'caption'} ||= "Caption";
			$clone{'caption'} = "Caption" if $clone{'caption'} eq "E-Mail";
			$clone{'caption'} = CGI::escapeHTML($clone{'caption'});
		} else {
			$clone{'caption'} = CGI::escapeHTML($clone{'caption'}) || "E-Mail";
		}

	# Assemble the URL for the name change link
		my $conglom = $config->{ScriptName} . "?action=post&";
		foreach my $k (keys %clone) {
			$conglom .= "$k=" . CGI::escape($clone{$k}) . "&";
		} # end foreach
		$clone{'username_coded'} = CGI::escapeHTML($clone{'username'});
		$clone{'username_hexcoded'} = CGI::escape($clone{'username'});
		$conglom .= "&name_change=true";
	# The user can click their own name to get the name change form.  Deal with
	# that little problem here.
		my $name_box;
		if((exists $in{'name_change'} && $in{'name_change'} eq "true") || $config->{MultiChat}) {
			$name_box = qq(<input type="text" class="textbox" id="username" name="username" value="$clone{username_coded}" size="13">);
		} else {
			$name_box = (
				$clone{'username'} ne "Name"
				? qq(<input type="hidden" name="username" id="username" value="$clone{username_coded}"><a href="$conglom" id="namechange_link" class="namer"><font color="$clone{color}" class="name"><b>$clone{username}</b></font></a>)
				: qq(<input type="text" class="textbox" id="username" name="username" value="$clone{username_coded}" size="13">)
			);
		} # end else

	# Ajax requests get the sanitized form data back
		$clone{'message'} = '';
		$clone{'hex_color'} = $in{color} if($return_hash);
		$clone{'hex_mcolor'} = $in{mcolor} if($return_hash);
		return \%clone if $return_hash;

	# Otherwise, prepare the HTML.
		my $javascript = q~
<script type="text/javascript">

	var multichat_enabled = ~ . ($config->{MultiChat} + 0) . q~;

	function refresh_chat() {
		if($('#frm'))
			parent.messages.location.href = '~ . $config->{MessagesName} . q~?' + Math.floor(Math.random()*1000);
	} // end refresh_chat

	$().ready(function(){
	// Set up hover compat for stupid browsers
		$('.textbox, .textarea')
			.focus(function(event){
				$(event.target).addClass('focus');
				$(event.target).select();
			})
			.blur(function(event){
				$(event.target).removeClass('focus');
			})
			.mouseover(function(event){
				$(event.target).addClass('hover');
			})
			.mouseout(function(event){
				$(event.target).removeClass('hover');
			});
	// Submit button gets disabled on click, and the form submitted manually.
		$('#subm').click(function(event){
			var el = $(event.target);
			var is_disabled = el.attr('disabled') ? 1 : 0;
			el.attr('disabled', 'disabled');
			el.addClass('disabled');
			if(!is_disabled && multichat_enabled) {
				multichat.post();
			} else if(!is_disabled) {
				$('#frm').submit();
			} // end if
			event.preventDefault();
			event.stopPropagation();
			return false;
		});
	// Update button is scripty
		$('#upd').click(refresh_chat);
	// Now focus the message field
		var msg = $('#message');
		if(msg)
			msg.focus();
	// And force a refresh of the messages window
		refresh_chat();
	// Relocate the ajax loading box
		var subm_tl = $('#subm').offset();
		$('#ajaxloader').css({ top: subm_tl.top + 'px', left: (subm_tl.left - 25) + 'px', position: 'absolute' });
	// Attach hiding and showing the ajax loading box to the loading box...
		$('#ajaxloader').ajaxStart(function(){ $(this).addClass('loading') });
		$('#ajaxloader').ajaxComplete(function(){ $(this).removeClass('loading') });
	// Hide the name change link and show the name form, when clicked
		$('#multichat_name').click(function(event){
			$('#multichat_name').hide();
			$('#username').show();
		});
	});
</script>~;

		my $multichat = generateMultiChatForm();

		return<<WHOSITS;
$javascript
$multichat
<form action="$config->{ScriptName}" method="post" name="frm" id="frm">
<input type="hidden" name="action" value="post">
	<table width="800" cellpadding="0" cellspacing="0" align="center" id="postformtable">
		<tr>
			<td width="140" align="left">
				<hr width="85%" />
			</td>
			<td align="center" width="520">
				<table width="520" border="0" cellspacing="0" cellpadding="1">
					<tr>
						<td align="left" width="145">
							<input type="text" name="url" id="url" value="$clone{url}" size="13" class="textbox" />
						</td>
						<td align="center">
							<input type="text" name="caption" id="caption" value="$clone{caption}" size="13" class="textbox" />
						</td>
						<td align="right" width="145">
							<input type="text" name="mcolor" id="mcolor" value="$clone{mcolor}" size="13" class="textbox" />
						</td>
					</tr>
					<tr>
						<td colspan="3">
							<textarea tabindex="1" name="message" id="message" rows="1" cols="80" class="textarea"></textarea>
						</td>
					</tr>
					<tr>
						<td align="left" valign="top" width="145">
							<div id="ajaxloader">&nbsp;</div>
							<input tabindex="2" type="submit" class="button" value="Send" name="subm" id="subm" accesskey="s" />
							&nbsp;&nbsp;
							<input type="button" class="button" onclick="refresh_chat()" name="upd" id="upd" value="Update" />
						</td>
						<td align="center">$name_box<span id="multichat_name" class="namer"></span></td>
						<td align="right" valign="top" width="145">
							<input type="text" name="color" id="color" class=textbox value="$clone{color}" size="13" />
						</td>
					</tr>
				</table>
			</td>
			<td width="140" align="right">
				<hr width="85%" />
			</td>
		</tr>
	</table>
</form>
WHOSITS
	} # end generatePostform


# Generate the top form for MultiChat
	sub generateMultiChatForm {
		return '' unless $config->{MultiChat};
		return q~
<script type="text/javascript">
// Multichat permits one posting form to switch between multiple sets of nifty data.
multichat = {
//
	_base_struct: {
		username: 'Name',
		color: 'white',
		hex_color: '#ffffff',
		mcolor: 'Message Color',
		hex_mcolor: '#ffffff',
		caption: '~ . ($config->{EnableCaptions} ? 'Caption' : 'E-Mail') . q~',
		url: 'URL'
	},
// What's our name data look like?
	name_data: [
		{}
	],
// Which tab is active?
	active: 0,


// Init the module
	init: function() {
		multichat.initNameData(0);
	},

// Init a name data structure
	initNameData: function(index) {
		var clone = {};
		$.each(multichat._base_struct, function(k, v) { clone[k] = v });
		multichat.name_data[index] = clone;
	},

// Post a message
	post: function() {
		var form_data = $('#frm').serializeArray();
		form_data.subm = 'Send';
		$.post(
			'~ . $config->{ScriptName} . q~',
			form_data,
			function(json_data, textStatus){
			// Update the post form.
				multichat.updateForm(json_data, false, true);
			// Now turn the submit button back on.
				$('#subm').removeAttr('disabled');
				$('#subm').removeClass('disabled');
			// And refresh the chat frame
				refresh_chat();
			// And refocus the posting form.
				$('#message').focus();
			},
			'json'
		);
	},

// Update the post form
	updateForm: function(data, skip_data_update, clobber_message) {
		$.each(data, function(index, value){
			if(!clobber_message && index == 'message') return;
			var el = $('#' + index);
			if(el) {
				el.attr('value', value);
			} // end if
		});
	// Update the internal representation of the username data
		if(!skip_data_update)
			multichat.updateName(multichat.active, data);
	// Show the user's name, hiding the text box until clicked.
		$('#multichat_name').html('<font color="' + data.hex_color + '" class="name"><b>' + data.username + '</b></font>');
		if(data.username == '' || data.username == 'Name') {
			$('#multichat_name').hide();
			$('#username').show();
		} else {
			$('#multichat_name').show();
			$('#username').hide();
		} // end if
	// Now hide the old name change link
		if($('#namechange_link'))
			$('#namechange_link').hide();
	},

// Update the name data in the tab list
	updateName: function(name_index, data) {
		multichat.name_data[ name_index ] = data;
		var name = data.username;
		if(name == '' || name == 'Name') name = 'lurker';
		$('#name-' + name_index).html('<font color="' + data.hex_color + '" class="name"><b>' + name + '</b></font><span class="yoink">x</span>');
	},

// Add a new name to the tab list
	addName: function() {
		var new_name_id = multichat.name_data.length;
		multichat.initNameData(new_name_id);
		$('#multichat-table-end').before('<td id="name-' + new_name_id + '"><font color="white" class="name"><b>lurker</b></font><span class="yoink">x</span></td>');
		multichat.selectName(new_name_id);
		$('#message').blur();
		$('#username').focus();
	},

// Select a name tab
	selectName: function(index) {
		if(index != parseInt(index)) return;
		if(!multichat.name_data) return;
	// Play class switcheroo
		$('#name-' + multichat.active).removeClass('picked');
		multichat.active = index;
		$('#name-' + multichat.active).addClass('picked');
	// Update the form with the name info
		multichat.updateForm(multichat.name_data[ multichat.active ], true, false);
		$('#message').focus();
	},

// Close a name tab
	closeName: function(index) {
		if(multichat.active == index) {
			var names = multichat.getNameList();
		// Can't close the last name.
			if(names.count < 2) {
				return;
			} // end if
			var found_index = null;
			var first_index = null;
			for(var k in names) {
				if(k == 'count') continue;
				if(k == index) continue;
			// Keep track of the first still active name
				if(first_index == null)
					first_index = k;
			// Try to find the name immediately to the left of the closed name
				if(found_index > index)
					break;
				found_index = k;
			} // end foreach
		// If we didn't find one to the left, default to the first.
			if(found_index == null)
				found_index = first_index;
			multichat.selectName(found_index);
		} // end if
	// Yoink the table cell
		$('#name-' + index).hide();
		multichat.name_data[index].disabled = 1;
	},

// Get a list of all active names
	getNameList: function() {
		var names = {};
		var count = 0;
		$.each(multichat.name_data, function(k, v) {
			if(!v.disabled) {
				names[k] = v;
				count++;
			}
		});
		names.count = count;
		return names;
	}
};
$().ready(function(){
// Attach behavior to the add button
	$('#multichat-adder').click(function(){
		multichat.addName();
	});
// Attach behavior to the name change tab
	$('#multichat-name-pick-list td').live('click', function(event){
	// Determine the table cell
		var el = event.target;
		if(el.nodeName != 'TD') el = ($(event.target).parents('td'))[0];
	// Extract the id attribute
		if(!el.id) return;
		var name_id = el.id.split(/\-/);
		if(!name_id || !name_id.length || name_id.length != 2) return;
	// Call the select
		multichat.selectName(name_id[1]);
	// Stop bubbling.
		event.stopImmediatePropagation();
		event.stopPropagation();
		return false;
	});
// Attach behavior to the close tab link
	$('#multichat-name-pick-list td span.yoink').live('click', function(event){
	// Determine the table cell
		var el = event.target;
		if(el.nodeName != 'TD') el = ($(event.target).parents('td'))[0];
	// Extract the id attribute
		if(!el.id) return;
		var name_id = el.id.split(/\-/);
		if(!name_id || !name_id.length || name_id.length != 2) return;
	// Call the delete
		multichat.closeName(name_id[1]);
	// Stop bubbling.
		event.stopImmediatePropagation();
		event.stopPropagation();
		return false;
	});
// Finally, set up an ajax listener that looks for the X-JSON header
// and will throw error messages that are returned from the server
	$.ajaxSetup({
		complete: function(request, status) {
		// Did we get the header?
			var oops = request.getResponseHeader('X-JSON');
			if(!oops) return;
		// Yeeeup.  How bad is it?  We can only process standardHTML messages.
			var data = eval('(' + oops + ')');
			if(!data.standardhtml) return;
		// Yeah, it's bad.  This is a world-ender.  Rewrite the world.
			if(data.html) {
				data.header = '';
				data.body = data.html;
				data.footer = '';
			} // end if
			$('div.header').attr('id', 'old_header').hide().after('<div class="header">' + data.header + '</div>');
			$('div.body').attr('id', 'old_body').hide().after('<div class="body">' + data.body + '</div>');
			$('div.footer').attr('id', 'old_footer').hide().after('<div class="footer">' + data.footer + '</div>');
		}
	});
});
multichat.init();
</script>
<table border="0" cellspacing="0" cellpadding="0" id="multichat-name-pick-list" align="center">
	<tr>
		<td id="multichat-table-start">&nbsp;</td>
		<td class="picked" id="name-0"><span class="name"><i><font color="~ . $in{color} . q~">~ . ($in{username} eq 'Name' || !$in{username} ? 'lurker' : $in{username}) . q~</font></i></span></td>
		<td id="multichat-table-end">&nbsp;</td>
		<td id="multichat-adder" class="adder">&nbsp;+&nbsp;</td>
	</tr>
</table>
~;
	} # end generateMultiChatForm


# Update the chat messages file
	sub updateMessages {
	# Don't actually update anything if it's just a name change
		return undef if(defined $in{name_change} && $in{name_change} eq "true");
		my $raw = CGI::unescapeHTML($in{'message'});
		$raw ||= '';
	# Yoink out nasty crap and emptyness.
		$raw =~ s!<[^<]+>!!gi;
		$raw =~ s![\s\n\r]!!gi;
	# Don't post blank messages
		return undef if((!defined $raw || $raw eq "") && !$in{special});
	# Don't post the intro message if the user is an authenticated guard.
		return undef if exists $in{special} && defined $session->{data}->{guard} && $session->{data}->{guard};
	# Don't post the intro message if it's been posted.
		return undef if exists $in{special} && defined $session->{data}->{entered} && $session->{data}->{entered};

	# Piece together the form HTML
		my $name = ($in{'username'} ne "Name" ? $in{'username'} : " " );
		my $message = $in{'message'};
		my $namecolor = $in{'color'};
		my $msgcolor = ( $in{'mcolor'} ne "Message Color" ? $in{'mcolor'} : $namecolor );
		$msgcolor = $namecolor unless $msgcolor;
		my $linkhtml = ( $in{'url'} ne "URL" ? qq(<a href="$in{'url'}" target="_blank" class="url"><font color="$namecolor" face="Wingdings">2</font></a>) : "" );
		my $captionhtml = ( ($in{'caption'} && ($in{'caption'} ne "Caption")&& ($in{'caption'} ne "E-Mail")) ? qq!<font color="$namecolor"><i>($in{'caption'})</i></font>! : "" );
	# If captions are disabled, add the email address to the link
		if(!$config->{EnableCaptions}) {
			$captionhtml = '';
			if($in{'caption'} && $in{'caption'} ne "E-Mail") {
				$linkhtml .= ( $in{'caption'} ne "E-Mail" ? qq(<a href="mailto:$in{'caption'}" class="email"><font color="$namecolor" face="Wingdings">*</font></a>) : "" );
			} # end if
		} # end if
		my $dt = getTime();
		my $timebit = $dt->strftime('%H:%M');

	# Piece together the new message line
		my $newline = qq(<div class="messageline"> <span class="thename"><font color="$namecolor">$name </font></span>);
		$newline .= qq! &nbsp;<span class="thecaption">$captionhtml</span> ! if $captionhtml;
		$newline .= qq( <span class="thelinks">$linkhtml</span>) if($linkhtml);
		$newline .= qq! <br />&nbsp;&nbsp;! if($config->{EnableCaptions} && !$config->{DisableCaptionBR});
		$newline .= qq! <span class="thetime"><font color="$msgcolor"> ($timebit) </font></span>!;
		$newline .= qq( <span class="themessage"><font color="$msgcolor">$message</font></span> </div>);

	# If this is a special user entrance, post that instead.  Users logged in as guards don't get this.
		if((defined $in{special} && $in{special} eq "entrance")) {
			$session->{data}->{entered} = 1;
			$newline = qq~<div class="messageline welcome"> <span class="themessage"><span class="star">*</span> A user has entered the chat.</font></span> <span class="thetime"> ($timebit) </span> </div>~;
		} # end if

	# Pull in the message file
		my $fh = openFileRW($config->{MessagesFile});
	# Discard the first and last lines.
		my @messages = <$fh>;
		shift @messages;
		pop @messages;
		chomp foreach @messages;
	# Drop the first line on top
		my @lines;
		unshift(@messages, $newline);
		@messages = @messages[0 .. ($config->{MessageLimit} - 1)];
	# Reassemble the chat lines
		push(@lines, qq(<html><head><meta http-equiv="refresh" content="$config->{RefreshRate}"><style type="text/css"> body { background-color: black; color: white; } </style><link rel="stylesheet" href="$config->{CSSName}" type="text/css" /></head><body bgcolor="black" text="white">));
		push(@lines, @messages);
		my $powered_by = createPoweredBy(1);
		push(@lines, qq(<p class="timeline">All times are $config->{TimeZoneName}</p><p class="copy">$powered_by</p></body></html>\n));
	# Write the file back out
		seek($fh, 0, 0);
		truncate($fh, 0);
		print $fh join("\n", @lines);
		close($fh);
	# I .. what?
		return $newline;
	} # end updateMessages



# Update the chat log
	sub updateLog {
	# Don't log nothing
		return unless $_[0];
	# Log files have a specific naming format
		my $dt = getTime();
		my $timestring = $dt->strftime('%Y-%m-%d-%H');
		my($fh, $isnew) = openFileAppend($config->{LogsPath} . "/" . $config->{MessagesFN} . "-$timestring" . $config->{MessagesFX});
	# If we're the first new line in the log, add a proper HTML header
		if($isnew) {
			my $new_timestamp = $dt->strftime('%Y-%m-%d %H:%M:%S');
			print $fh qq(<html><head><style type="text/css"> body { background-color: black; color: white; } </style><link rel="stylesheet" href="$config->{CSSName}" type="text/css" /></head><body bgcolor="black" text="white"> Log started: $new_timestamp<br /><br /> \n);
		} # end if
	# IP address?  I see no IP address here.  What are you talking about?
		print $fh "$_[0]<!-- " . currentIP() . " -->\n";
		close($fh);
	} # end updateLog


# Update the log of posts for the guard frame
	sub updatePostlog {
	# De-HTMLize the name
		my $username = $in{'username'};
		$username ||= 'Name'; # yes, really.
		$username =~ s/<.+?>//g;
	# Pick the proper color
		my $namecolor = $in{'color'};
		$namecolor ||= 'white';
		my $msgcolor = ( $in{'mcolor'} ne "Message Color" ? $in{'mcolor'} : $namecolor );
		$msgcolor = $namecolor unless $msgcolor;
	# Which user are we?
		my $sesid = $session->{id};
		my $ip = currentIP();

	# time() -> UTC, so it's OK here
		my $timer = time();
		my $newline = qq($username|^!^|$msgcolor|^!^|$namecolor|^!^|$sesid|^!^|$ip|^!^|$timer|^!^|);

	# Pull in the existing file contents
		my $fh = openFileRW($config->{PostlogFile});
		my @messages = <$fh>;
		chomp foreach @messages;
	# Shove our line at the top
		unshift(@messages, $newline);
	# Trim the record to messages + 10
		@messages = @messages[0 .. ($config->{MessageLimit} + 10)];
	# Rewrite the file
		seek($fh, 0, 0);
		truncate($fh, 0);
		print $fh join("\n", @messages);
		close($fh);
	} # end updatePostlog


# Cleanly exit, emitting the response and saving the user's session
	sub Exit {
		$session->markActive();
		$response->output() if $response->canOutput();
		exit(0);
	} # end Exit


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# List of likely error messages

# Complain that the user has tried the wrong password too many times.
	sub noEntry_TooManyTries {
		$response->appendBody(standardHTML({
			header => "Password Failure",
			body => "You have failed at entering the password too many times.  Try again later.",
			footer => "",
		}));
		&Exit();
	} # end noEntry_TooManyTries


# Complain that the user's password token is missing
	sub noEntry_MissingPassword {
		$response->appendBody(standardHTML({
			header => "Missing Password",
			body => "You don't seem to know the password.  You'll need to re-enter the chat, sorry.",
			footer => "",
		}));
		&Exit();
	} # end noEntry_MissingPassword


# Complain that the user's cookies are busted.
	sub noEntry_Insane {
		$response->appendBody(standardHTML({
			header => "No Cookie",
			body => "It appears that your web browser did not store the cookie I sent it.  You must enable cookies to chat here.",
			footer => "(For more information on cookies, please refer to your web browser's help function.)",
		}));
		&Exit();
	} # end noEntry_Insane


# Complain that the user has been kicked or banned
	sub noEntry_KickBan {
	# Do banned users get redirected to another page?
		if($config->{BannedRedirect}) {
			$response->addHeader('Status', '302 Found');
			$response->addHeader('Location', $config->{BannedRedirect});
		} # end if
		my $pretty = getTime($_[0])->strftime('%Y-%m-%d %H:%M:%S');
	# Otherwise / in addition, let's let the user know that they're banned
		$response->appendBody(standardHTML({
			header => "Kicked or Banned",
			body => "Sorry, you have been kicked or banned from this chat room until $pretty.<br />The reason for this kick or ban is: $_[1].",
			footer => ($config->{BannedRedirect} ? qq~<script type="text/javascript">location.href='$config->{BannedRedirect}';</script>~ : ''),
		}));
		&Exit();
	} # end noEntry_KickBan


# Complain that the user is underage.
	sub noEntry_COPPA {
		$response->appendBody(standardHTML({
			header => "Sorry",
			body => "Sorry, those under the age of $config->{COPPAAge} may not chat here.",
			footer => "",
		}));
		&Exit();
	} # end noEntry_COPPA
