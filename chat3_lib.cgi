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

use Fcntl qw(:flock);
use DateTime;

# CAUTION: Spaghetti code ahead.
our $VERSION = '4.9.1';
our $VERSION_TAG = '"Diaspora"';


# Create a "Powered By" HTML blub
	sub createPoweredBy() {
		my $include_copyright = shift;
		my $version_number = $VERSION;
		$version_number .= " <i>$VERSION_TAG</i>" if($VERSION_TAG);
		my $dt = &getTime();
		my $current_year = $dt->year;
		return qq~<a href="http://natter.pleh.net/" target="_blank">Powered by Natter $version_number</a>~ . ($include_copyright ? qq~<br />Copyright 1999-$current_year Charles Capps~ : '');
	} # end createPoweredBy


# Retrieve a localized time zone object
	sub getTime {
		my $time = shift;
		$time = time() if(!$time);
		$dt = DateTime->from_epoch( epoch => $time, time_zone => $config->{TimeZoneCode} );
		return $dt;
	} # end getTime


# Open a file and Perl-eval its contents.
	sub evalFile {
		return eval openFile($_[0]);
	} # end evalFile


# Open a file and return its contents as an array
	sub openFileAsArray {
		return split("\n", openFile($_[0]));
	} # end openFileAsArray


# Open a file (read-only) and return the file handle
	sub openFile {
		if((-e $_[0]) && (-s $_[0])) {
			my $filehandle = &makeGlob;
			open($filehandle, "<$_[0]") or die "$! opening $_[0]";
			flock($filehandle, LOCK_SH) or die "$! SHlocking $_[0]";
			my $string = join("", <$filehandle>);
			close($filehandle);
			return $string;
		} # end if
	} # end openFile


# Open a file (read-write) and return the file handle.
	sub openFileRW {
		if((-e $_[0]) && (-s $_[0])) {
			my $filehandle = &makeGlob;
			open($filehandle, "+<$_[0]") or die "$! opening $_[0]";
			flock($filehandle, LOCK_EX) or die "$! EXlocking $_[0]";
			return $filehandle;
		} else {
			die "Can't RW $_[0], it doesn't exist or is blank.";
		} # end if
	} # end openFileRW


# Open a file in append mode
	sub openFileAppend {
		my $filehandle = &makeGlob;
		my $isnew = (-e $_[0] ? 0 : 1);
		open($filehandle, ">>$_[0]") or die "$! opening $_[0]";
		flock($filehandle, LOCK_EX) or die "$! EXlocking $_[0]";
		return($filehandle, $isnew);
	} # end openFileRW


# Print a cookie header
	sub printCookie {
		&printHeader("Set-Cookie: $_[0]");
	} # end printCookie


# Print an HTTP header
	sub printHeader {
		print qq($_[0]\n);
	} # end printHeader


# Generate a string of random characters
	sub randomGenerator {
		my @letters = ("a".."z","A".."Z",0..9);
		my $string; my $l = scalar(@letters); $l--;
		foreach(1 .. $_[0]) {
			$string .= $letters[(int(rand($l)) + 1)];
		} # end foreach
		return $string;
	} # end randomGenerator


# Create a filehandle Perl glob.
	sub makeGlob {
		my $x = "FileHandle" . randomGenerator(32);
		return \*{$x};
	} # end makeGlob


# Establish a global lock file
	sub lockAndLoad {
		open($LOCKFILE, ">$config->{NonCGIPath}/lockfile.cgi") or die "$! opening $config->{NonCGIPath}/lockfile.cgi";
		flock($LOCKFILE, LOCK_EX) or die "$! EXlocking $config->{NonCGIPath}/lockfile.cgi";
	} # end lockAndLoad


# Emit boilerplate HTML and print a message to the user
	sub standardHTML {
		my $text;

		print CGI::header();
	# If we received a hash of options, it's a complex message.
		my $pbstring = &createPoweredBy();
		if(ref($_[0]) =~ m/HASH/) {
			my $ifoot = ( $_[0]->{footer} ne "" ? "<br />" : "" );
			my $powered_by = ( !exists $_[0]->{no_powered} ? qq~<p class="copy">$pbstring</p>~: "" );
			$text = <<FORMAT;
<div class="header">$_[0]->{header}</div>
<div class="body">$_[0]->{body}</div>
$ifoot
<div class="footer">$_[0]->{footer}</div>
$powered_by
FORMAT
		} else {
	# Otherwise it's just a simple message.
			$text = join("", @_) . qq~<p class="copy">$pbstring</p>~;
		} # end if

		print<<STANDARDhtml;
<html>
<head>
	<link rel="stylesheet" href="$config->{CSSName}" type="text/css" />
	<script language="JavaScript" type="text/javascript" src="$config->{NonCGIURL}/jquery-1.3.2.min.js"></script>
</head>
<body>
	<p>$text</p>
</body>
</html>
<!-- End -->
STANDARDhtml

		&Exit();
	} # end standardHTML




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Sanity checking subroutines

# If the user has a COPPA cookie, pass them.
# If there's no cookie, bail
# If there's an underage cookie, complain.
	sub checkCOPPACookie {
		my @coppa = cookie("$config->{Script}_COPPA");
		if($coppa[0]) {
			if($coppa[0] eq "under") {
				&noEntry_COPPA;
			} elsif($coppa[0] eq "over") {
				return;
			} else {
				&noEntry_Funky(@coppa);
			} # end if
		} # end if
		return;
	} # end checkCOPPACookie


# Check to see if the user has been banned.
	sub checkKickBanCookie {
		my @bannage = cookie("$config->{Script}_b4nn4g3");
		if(@bannage) {
		# Cookies will always use unmodified time(), which provides UTC seconds
			if($bannage[0] < time()) {
				&printCookie(cookie(
						-name    => "$config->{Script}_b4nn4g3",
						-value   => ["", ],
					));
			} else {
				&noEntry_KickBan(int(($bannage[0] - time()) / 60));
				&Exit;
			} # end if
		} # end if

		return undef;
	} # end checkKickBanCookie


# Check to see if our normal cookie is present. If not, bail.
	sub checkSanityCookie {
		my @sanity = cookie("$config->{Script}_sanity");
		unless(($sanity[0] eq "keeper") && ($sessions->is_valid($sanity[1]))) {
			&noEntry_Insane;
		} # end unless
	} # end checkSanityCookie


# Check to see if the guard script cookie is present.  If not, prompt the user to log in.
	sub checkAuthCookie {
		my @auth = cookie("$config->{Script}_guard");
		if(!@auth) {
			if(exists $in{'username'}) {
				if(exists $guard_list->{$in{'username'}}) {
					if($in{'password'} eq $guard_list->{$in{'username'}}) {
						&printCookie(cookie(
							-name    => "$config->{Script}_guard",
							-value   => [$in{username}, $in{password}],
							));
						return;
					} else {
						# passwd mismatch
						&standardHTML("Wrong password for user '$in{username}'");
					} # end if
				} else {
					# no such user
					&standardHTML("No such user '$in{username}'");
				} # end if
			} else {
				# no form input
				&standardHTML({
					header => "Enter Authorization",
					body => <<FORMBODY
<form id="entrance" method="POST" action="$config->{GuardScript}">
<table border="0" align="center">
<tr><td class="body">Username:</td><td><input type="text" name="username" id="username" class="textbox"></td></tr>
<tr><td class="body">Password:</td><td><input type="password" name="password" id="password" class="textbox"></td></tr>
<tr><td colspan="2"><input type="submit" value="Authorize" class="button"></td></tr>
</table>
</form>
FORMBODY
	,
					footer => "",
				});
			} # end if
		} # end if
	} # end checkAuthCookie


# Check to see if the user is logged in.  If so, return true.
	sub checkAuthCookie2 {
		my @auth = cookie("$config->{Script}_guard");
		if(!@auth) {
			if(exists $in{'username'}) {
				if(exists $guard_list->{$in{'username'}}) {
					if($in{'password'} eq $guard_list->{$in{'username'}}) {
						return 1
					} # end if
				} # end if
			} # end if
		} # end if
		return 0;
	} # end checkAuthCookie2


# Complain that the user's cookies are busted.
	sub noEntry_Insane {
		&standardHTML({
			header => "No Cookie",
			body => "It appears that your web browser did not store the cookie I sent it.  You must enable cookies to chat here.",
			footer => "(For more information on cookies, please refer to your web browser's help function.)",
		});
		&Exit();
	} # end noEntry_Insane


# Complain that the user has been kicked or banned
	sub noEntry_KickBan {
		&standardHTML({
			header => "Kicked or Banned",
			body => "Sorry, you have been kicked or banned from this chat room.  You may enter again in $_[0] minutes.",
			footer => "",
		});
		&Exit();
	} # end noEntry_KickBan


# Complain that the user is underage.
	sub noEntry_COPPA {
		&printCookie(cookie(
				-name    => "$config->{Script}_COPPA",
				-value   => ["under", ],
				-expires => '+1h'
			));
		&standardHTML({
			header => "Sorry",
			body => "Sorry, those under the age of 13 may not chat here.",
			footer => "",
		});
		&Exit();
	} # end noEntry_COPPA

# Complain about bad cookie wtfery
	sub noEntry_Funky {
		&standardHTML({
			header => "Error",
			body => "I've been confused by something your web browser told me.  Perhaps your web browser is rejecting cookies, or your computer's clock is incorrect?",
			footer => "Please try your request again.",
		});
		&Exit();
	} # end noEntry_Funky


# Try to set a cookie to ensure the client supports cookies
	sub decideSanity {
		my @sanity = cookie("$config->{Script}_sanity");
		my $sanein = ($sessions->load_if_valid($sanity[1]) ? $sanity[1] : $sessions->make_new() );
		if($sanein ne $sanity[1]) {
			&printCookie(cookie(
				-name => "$config->{Script}_sanity",
				-value => ["keeper", $sanein],
			));
		} # end if
	} # end sub


# Determine if a user is kicked or banned.  If so, the user is notified
	sub decideBannage {
		$sessions->comp_to_banned(&currentIP);
		my $bannage = $sessions->this_banned();
		if($bannage) {
			&printCookie(cookie(
				-name => "$config->{Script}_b4nn4g3",
				-value => [$bannage],
				-expires => '+1y'
			));
		# Cookies use time(), etc, etc, etc.  This is just a seconds countdown.
			&noEntry_KickBan(sprintf("%d", ($bannage - time()) / 60) + 1);
			&Exit;
		} # end if
	} # end sub


# The Netscape Color Names
    our %color_map = (
        'aliceblue' => '#f0f8ff',
        'antiquewhite' => '#faebd7',
        'aqua' => '#00ffff',
        'aquamarine' => '#7fffd4',
        'azure' => '#f0ffff',
        'beige' => '#f5f5dc',
        'bisque' => '#ffe4c4',
        'black' => '#000000',
        'blanchedalmond' => '#ffebcd',
        'blue' => '#0000ff',
        'blueviolet' => '#8a2be2',
        'brown' => '#a52a2a',
        'burlywood' => '#deb887',
        'cadetblue' => '#5f9ea0',
        'chartreuse' => '#7fff00',
        'chocolate' => '#d2691e',
        'coral' => '#ff7f50',
        'cornflowerblue' => '#6495ed',
        'cornsilk' => '#fff8dc',
        'crimson' => '#dc143c',
        'cyan' => '#00ffff',
        'darkblue' => '#00008b',
        'darkcyan' => '#008b8b',
        'darkgoldenrod' => '#b8860b',
        'darkgray' => '#a9a9a9',
        'darkgreen' => '#006400',
        'darkgrey' => '#a9a9a9',
        'darkkhaki' => '#bdb76b',
        'darkmagenta' => '#8b008b',
        'darkolivegreen' => '#556b2f',
        'darkorange' => '#ff8c00',
        'darkorchid' => '#9932cc',
        'darkred' => '#8b0000',
        'darksalmon' => '#e9967a',
        'darkseagreen' => '#8fbc8f',
        'darkslateblue' => '#483d8b',
        'darkslategray' => '#2f4f4f',
        'darkslategrey' => '#2f4f4f',
        'darkturquoise' => '#00ced1',
        'darkviolet' => '#9400d3',
        'deeppink' => '#ff1493',
        'deepskyblue' => '#00bfff',
        'dimgray' => '#696969',
        'dimgrey' => '#696969',
        'dodgerblue' => '#1e90ff',
        'firebrick' => '#b22222',
        'floralwhite' => '#fffaf0',
        'forestgreen' => '#228b22',
        'fuchsia' => '#ff00ff',
        'gainsboro' => '#dcdcdc',
        'ghostwhite' => '#f8f8ff',
        'gold' => '#ffd700',
        'goldenrod' => '#daa520',
        'gray' => '#808080',
        'green' => '#008000',
        'greenyellow' => '#adff2f',
        'grey' => '#808080',
        'honeydew' => '#f0fff0',
        'hotpink' => '#ff69b4',
        'indianred' => '#cd5c5c',
        'indigo' => '#4b0082',
        'ivory' => '#fffff0',
        'khaki' => '#f0e68c',
        'lavender' => '#e6e6fa',
        'lavenderblush' => '#fff0f5',
        'lawngreen' => '#7cfc00',
        'lemonchiffon' => '#fffacd',
        'lightblue' => '#add8e6',
        'lightcoral' => '#f08080',
        'lightcyan' => '#e0ffff',
        'lightgoldenrod' => '#eedd82',
        'lightgoldenrodyellow' => '#fafad2',
        'lightgray' => '#d3d3d3',
        'lightgreen' => '#90ee90',
        'lightgrey' => '#d3d3d3',
        'lightpink' => '#ffb6c1',
        'lightsalmon' => '#ffa07a',
        'lightseagreen' => '#20b2aa',
        'lightskyblue' => '#87cefa',
        'lightslateblue' => '#8470ff',
        'lightslategray' => '#778899',
        'lightslategrey' => '#778899',
        'lightsteelblue' => '#b0c4de',
        'lightyellow' => '#ffffe0',
        'lime' => '#00ff00',
        'limegreen' => '#32cd32',
        'linen' => '#faf0e6',
        'ltgoldenrodyello' => '#fafad2',
        'magenta' => '#ff00ff',
        'maroon' => '#800000',
        'mediumaquamarine' => '#66cdaa',
        'mediumblue' => '#0000cd',
        'mediumorchid' => '#ba55d3',
        'mediumpurple' => '#9370d8',
        'mediumseagreen' => '#3cb371',
        'mediumslateblue' => '#7b68ee',
        'mediumspringgreen' => '#00fa9a',
        'mediumturquoise' => '#48d1cc',
        'mediumvioletred' => '#c71585',
        'medspringgreen' => '#00fa9a',
        'midnightblue' => '#191970',
        'mintcream' => '#f5fffa',
        'mistyrose' => '#ffe4e1',
        'moccasin' => '#ffe4b5',
        'navajowhite' => '#ffdead',
        'navy' => '#000080',
        'navyblue' => '#000080',
        'oldlace' => '#fdf5e6',
        'olive' => '#808000',
        'olivedrab' => '#6b8e23',
        'orange' => '#ffa500',
        'orangered' => '#ff4500',
        'orchid' => '#da70d6',
        'palegoldenrod' => '#eee8aa',
        'palegreen' => '#98fb98',
        'paleturquoise' => '#afeeee',
        'palevioletred' => '#d87093',
        'papayawhip' => '#ffefd5',
        'peachpuff' => '#ffdab9',
        'peru' => '#cd853f',
        'pink' => '#ffc0cb',
        'plum' => '#dda0dd',
        'powderblue' => '#b0e0e6',
        'purple' => '#800080',
        'red' => '#ff0000',
        'rosybrown' => '#bc8f8f',
        'royalblue' => '#4169e1',
        'saddlebrown' => '#8b4513',
        'salmon' => '#fa8072',
        'sandybrown' => '#f4a460',
        'seagreen' => '#2e8b57',
        'seashell' => '#fff5ee',
        'sienna' => '#a0522d',
        'silver' => '#c0c0c0',
        'skyblue' => '#87ceeb',
        'slateblue' => '#6a5acd',
        'slategray' => '#708090',
        'slategrey' => '#708090',
        'snow' => '#fffafa',
        'springgreen' => '#00ff7f',
        'steelblue' => '#4682b4',
        'tan' => '#d2b48c',
        'teal' => '#008080',
        'thistle' => '#d8bfd8',
        'tomato' => '#ff6347',
        'turquoise' => '#40e0d0',
        'violet' => '#ee82ee',
        'violetred' => '#d02090',
        'wheat' => '#f5deb3',
        'white' => '#ffffff',
        'whitesmoke' => '#f5f5f5',
        'yellow' => '#ffff00',
        'yellowgreen' => '#9acd32',
    );


# Fix a bogus color, using the Netscape 4.x method (hybridized with the IE and Mozilla methods)
    sub fix_color {
        my $color = lc(shift);
    # Is it in the map?
        if($color_map{$color}) {
            return $color_map{$color};
        } # end if
    # Do we even need to process?
        if($color =~ m/^\#?([a-f0-9]{6})$/) {
            return '#' . $1;
        } # end if
    # Cleaning steps
        if(length($color) > 128) {
            $color = substr($color, 0, 128);
        } # end if
        $color =~ s/^\#//;
        $color =~ s/[^a-f0-9]/0/g;
    # Pad out to the nearest multiple of three
        while(length($color) % 3 != 0) {
            $color .= 0;
        } # end while
    # Chop into red, green, blue
        my $len = length($color) / 3;
        my @rgb = (
            substr($color, 0, $len),
            substr($color, $len, $len),
            substr($color, $len * 2, $len),
        );
    # Individual processing first...
        my @new_rgb = ();
        foreach my $chunk (@rgb) {
        # Lob off all but the *right* eight chars
            if(length($chunk) > 8) {
                $chunk = substr($chunk, length($chunk) - 8, 8);
            } # end if
        # Pad with zeros
            if(length($chunk) == 1) {
                $chunk = '0' . $chunk;
            } # end if
        # Mutter mutter never modify an array while iterating mutter mutter
            $new_rgb[scalar(@new_rgb)] = $chunk;
        } # end foreach
        @rgb = @new_rgb;
    # We need to examine all segments at once
        my $seglen = length($rgb[0]);
        while(
          $seglen > 2
          && substr($rgb[0], 0, 1) eq '0'
          && substr($rgb[1], 0, 1) eq '0'
          && substr($rgb[2], 0, 1) eq '0'
          ) {
            $rgb[0] = substr($rgb[0], 1, $seglen - 1);
            $rgb[1] = substr($rgb[1], 1, $seglen - 1);
            $rgb[2] = substr($rgb[2], 1, $seglen - 1);
            $seglen--;
        } # end while
        @new_rgb = ();
    # Final trim!
        foreach my $chunk (@rgb) {
            $new_rgb[scalar(@new_rgb)] = substr($chunk, 0, 2);
        } # end foreach

        return '#' . join('', @new_rgb);
    } # end fix_color

1;
