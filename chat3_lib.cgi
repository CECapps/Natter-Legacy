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

use Fcntl qw(:flock);
use DateTime;
use Socket;
use Digest::MD5;

# CAUTION: Spaghetti code ahead.
our $VERSION = '4.10.0';
our $VERSION_TAG = '"Ingress"';


# Create a "Powered By" HTML blub
	sub createPoweredBy() {
		my $include_copyright = shift;
		my $version_number = $VERSION;
		$version_number .= " <i>$VERSION_TAG</i>" if($VERSION_TAG);
		my $dt = getTime();
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


# Fetch a handle to the local database
	our $dbh;
	sub getDBHandle {
		return $dbh if defined $dbh;
		use DBI;
		my $dbfile = $config->{DBFile};
		$dbh = DBI->connect("dbi:SQLite:dbname=$dbfile", '', '', { RaiseError => 1 , AutoCommit => 1 }) || die "$! / $@ ($dbfile): $DBI::errstr";
		#$dbh->trace(2);
		upgradeDatabase();
		return $dbh;
	} # end getDBHandle


# Upgrade the SQLite database
	sub upgradeDatabase {
	# Creation first.  These table definitions should not be changed once in
	# production.  Any future changes should be through alters, to be taken care
	# of by this subroutine and what it calls.
		createTables();
	# Now, what's our database version?
		my ($version,) = $dbh->selectrow_array('SELECT MAX(version) FROM db_version LIMIT 1');
	# If the database is unversioned, it's version 1.  This won't happen in production.
		if(!$version) {
			$version = 1;
			$dbh->do('INSERT INTO db_version(version) VALUES(1)');
		} # end if
	# Create a list of possible database versions, and their corresponding
	# alter table subroutines.
		my $version_upgrade = {
			1 => \&upgradeDatabase_Version1,
		};
	# Go through the list, skipping upgrades that aren't needed.
		foreach my $upgrade_version (sort { $a <=> $b } keys %$version_upgrade) {
			next if($upgrade_version <= $version);
			$version_upgrade->{$upgrade_version}->();
			$dbh->do('INSERT INTO db_version(version) VALUES(?)', undef, $upgrade_version);
		} # end foreach
	} # end upgradeDatabase


# Dummy sub for the DB version 1 upgrade.
	sub upgradeDatabase_Version1 {
	} # end upgradeDatabase_Version1


# Create tables in the SQLite database
	sub createTables {
		$dbh->do('
			CREATE TABLE IF NOT EXISTS floodcheck (
				ip 			VARCHAR(15) PRIMARY KEY,
				tries 		INT 		UNSIGNED,
				last_try 	INT 		UNSIGNED
			)
		');
		$dbh->do('
			CREATE TABLE IF NOT EXISTS sessions (
				id		VARCHAR(32)	PRIMARY KEY,
				ip		VARCHAR(15)	NOT NULL,
				created	INT			NOT NULL,
				updated	INT			NOT NULL,
				kicked	INT			NULL DEFAULT "0",
				data	TEXT		NULL
			)
		');
	# The right way to do these tables would be to create three -- a table for
	# the ban info (reason, created, lifted, etc), then two others for IPs or
	# sessions.  Unfortunately I'm lazy, and this should work anyway.
		$dbh->do('
			CREATE TABLE IF NOT EXISTS ip_bans (
				id			INTEGER PRIMARY KEY AUTOINCREMENT,
				ip			VARCHAR(15)	NOT NULL,
				reason 		TEXT		NOT NULL,
				created		INT			NOT NULL,
				duration	INT			NOT NULL,
				lifted		INT			NOT NULL,
				cleared		INT			NULL,
				created_by	VARCHAR(32)	NOT NULL,
				lifted_by	VARCHAR(32)	NULL,
				cleared_by	VARCHAR(32)	NULL
			)
		');
		$dbh->do('
			CREATE INDEX IF NOT EXISTS ip_address ON ip_bans(ip)
		');

		$dbh->do('
			CREATE TABLE IF NOT EXISTS session_bans (
				id			INTEGER PRIMARY KEY AUTOINCREMENT,
				session_id	VARCHAR(32),
				reason 		TEXT		NOT NULL,
				created		INT			NOT NULL,
				duration	INT			NOT NULL,
				lifted		INT			NOT NULL,
				cleared		INT			NULL,
				lifted_by	VARCHAR(32)	NULL,
				created_by	VARCHAR(32)	NOT NULL,
				cleared_by	VARCHAR(32)	NULL
			)
		');
		$dbh->do('
			CREATE INDEX IF NOT EXISTS session_id ON session_bans(session_id)
		');

		$dbh->do('
			CREATE TABLE IF NOT EXISTS db_version (
				version		INT		NOT NULL
			)
		');
		$dbh->do('
			CREATE INDEX IF NOT EXISTS version ON db_version(version)
		');

	} # end createTables


# Load the configuration, plus attempt to set defaults for things that have not
# been configured.  This is due to the configuration file not being properly
# updatable in new configs, and a lack of a control panel thing.
	sub getConfigPlusDefaults {
		$config = &getConfig();
	# The lameness filter is enabled by default
		$config->{DisableLamenessFilter} ||= 0;
	# Only reset the COPPA age if it actually has not been defined.
		$config->{COPPAAge} ||= 13 if(!exists $config->{COPPAAge});
	# The old cookie prefix used to be the script name.  This does not work
	# very well when there are multiple instances of the scripts installed.
	# No, using cookie domains or paths isn't a better solution ... for now.
		$config->{CookiePrefix} ||= $config->{Script};
	# Don't look for proxies by default
		$config->{CheckProxyForward} ||= 0;
	# Don't do HttpBL lookups by default
		$config->{HttpBLAPIKey}	||= '',
	# Don't redirect banned users by default
		$config->{BannedRedirect} ||= '',
	# The new database file has to have a name...
		$config->{DBFile} ||= 'database/chat3.sqlite';
	# No password.
		$config->{ChatPassword} ||= '';
		$config->{PasswordAttempts} ||= 3;
		return $config;
	} # end getConfigPlusDefaults


# Determine the current IP address of the remote user.  Trust X-Forwarded-For.
	sub currentIP {
		my $ip = $ENV{REMOTE_ADDR};
		if($config->{CheckProxyForward}) {
			if(exists $ENV{HTTP_X_FORWARDED_FOR}) {
				if($ENV{HTTP_X_FORWARDED_FOR} ne "127.0.0.1") {
					$ip = $ENV{HTTP_X_FORWARDED_FOR};
				} # end if
			} # end if
		} # end if
		if($ENV{HTTP_USER_AGENT} =~ m/RealIP=([\d\.]+)$/) {
			return $1;
		} # end if
		$ip ||= '127.0.0.1';
		return $ip;
	} # end currentIP


# Attempt to determine if the user is coming from a threatening IP address
	sub checkIPThreat {
		return unless $config->{HttpBLAPIKey};
		my $proxy_ip_threat = getHTTPBLThreat($ENV{REMOTE_ADDR});
		my $detected_ip_threat = getHTTPBLThreat(currentIP());
		my $threat = $proxy_ip_threat || $detected_ip_threat;
		return $threat;
	} # end checkIPThreat


# Determine if an IP is threatening under the Http:BL
	sub getHTTPBLThreat {
		my $proxy_ip = shift;
		return unless $config->{HttpBLAPIKey};
		my $proxy_lookup_addr = $config->{HttpBLAPIKey}
			. '.'
			. join('.', reverse split /\./, $proxy_ip)
			. '.dnsbl.httpbl.org';
		my @proxy_lookup = gethostbyname($proxy_lookup_addr);
		$threatening = 0;
		if(scalar @proxy_lookup) {
			my ($n, $a, $t, $l, @addresses) = @proxy_lookup;
			if(scalar @addresses) {
				@addresses = grep /^127\./, map { inet_ntoa($_) } @addresses;
				foreach my $address (@addresses) {
					my($j, $stale, $threat, $type) = split /\./, $address;
				# We'll let old threats in that aren't severe
					next if $stale > 180 && $threat < 25;
				# We'll let minor threats in
					next if $threat < 10;
				# We'll let unclassified threats in, as long as they aren't bad
					next if !$type && $threat < 25;
				# Yeeeup, it's a threat
					$threatening = 1;
				} # end foreach
			} # end if
		} # end if
		return $threatening;
	} # end sub


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
			my $filehandle = makeGlob();
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
			my $filehandle = makeGlob();
			open($filehandle, "+<$_[0]") or die "$! opening $_[0]";
			flock($filehandle, LOCK_EX) or die "$! EXlocking $_[0]";
			return $filehandle;
		} else {
			die "Can't RW $_[0], it doesn't exist or is blank.";
		} # end if
	} # end openFileRW


# Open a file in append mode
	sub openFileAppend {
		my $filehandle = makeGlob();
		my $isnew = (-e $_[0] ? 0 : 1);
		open($filehandle, ">>$_[0]") or die "$! opening $_[0]";
		flock($filehandle, LOCK_EX) or die "$! EXlocking $_[0]";
		return($filehandle, $isnew);
	} # end openFileRW


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
	# If we received a hash of options, it's a complex message.
		my $pbstring = createPoweredBy();
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

		return <<STANDARDhtml;
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
	} # end standardHTML


	sub standardHTMLForErrors {
		my $html = standardHTML(@_);
		if(defined $response && ref $response =~ /Natter::HTTP_Response/ && $response->canOutput()) {
		# If we can, use the HTTP response already being built...
			$response->setBody($html);
		} else {
		# Otherwise, emit the HTML directly.
			print CGI::header();
			print $html;
		} # end if
		&Exit();
	}



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Sanity checking & data fixing

# Fix a bogus color, using the Netscape 4.x method (hybridized with the IE and Mozilla methods)
    sub fix_color {
        my $color = lc(shift);
    # Is it in the map?  Remove whitespace and wtfery so that "yellow green" etc gets mapped properly
		my $color_map_twiddle = $color;
		$color_map_twiddle =~ s/[^a-z0-9]//g;
        if($color_map{$color_map_twiddle}) {
            return $color_map{$color_map_twiddle};
        } # end if
	# Try the broken color map.
        if($broken_color_map{$color_map_twiddle}) {
            return $broken_color_map{$color_map_twiddle};
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
            $color .= '0';
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
    # We need to examine all segments at once and chop off leading zeros if possible
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


# Get a name back from a color code
	sub getColorName {
		my $hex = lc(shift);
		generateReverseColorMap() if(!defined $reverse_color_map);
		return defined $reverse_color_map->{$hex} ? $reverse_color_map->{$hex} : $hex;
	} # end getColorName


# Flip the color maps
	sub generateReverseColorMap {
		$reverse_color_map = {};
	# Simple reverse is easy...
		foreach my $color (sort keys %color_map) {
			my $hex = lc($color_map{$color});
			$reverse_color_map->{$hex} = $color;
		} # end foreach
	# But the broken list is painful.  Colors are repeated multiple times...
		my %multiples;
		foreach my $color (sort keys %broken_color_map) {
			my $hex = lc($broken_color_map{$color});
			if(exists $reverse_color_map->{$hex}) {
			# It's a multiple!  Drop it in the list to look at later...
				my $sec = $multiples{$hex};
				$sec = [] if(!defined $sec);
				$sec->[scalar @$sec] = $color;
				$multiples{$hex} = $sec;
			} else {
			# Woo, clear.
				$reverse_color_map{$hex} = $color;
			} # end if
		} # end foreach
	# Multiples, ARGH!
		foreach my $hex (keys %multiples) {
			$mult = $multiples{$hex};
		# Pull the canonical color back in the list.
			$mult[scalar @$mult] = $reverse_color_map->{$hex};
		# Try to pick names in the official list first.
			my @official = sort grep { exists $color_map{$_} } @$multi;
			if(scalar @official > 0) {
				$reverse_color_map->{$hex} = $official[0];
				next;
			} # end if
		# Try to pick names without numbers second.
			my @nonum = sort grep { !m/\d+$/ } @$mult;
			if(scalar @nonum > 0) {
				$reverse_color_map->{$hex} = $nonum[0];
				next;
			} # end if
		# It's not official, and it has numbers.  Crap on a stick.  Just pick
		# the first sorted name we have and run with it.
			my @mutter = sort @$mult;
			$reverse_color_map->{$hex} = $mutter[0];
		} # end foreach
	} # end generateReverseColorMap

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

	our %broken_color_map = (
		'indianred'		=>	'#B0171F',
		'crimson'		=>	'#DC143C',
		'lightpink'		=>	'#FFB6C1',
		'lightpink1'		=>	'#FFAEB9',
		'lightpink2'		=>	'#EEA2AD',
		'lightpink3'		=>	'#CD8C95',
		'lightpink4'		=>	'#8B5F65',
		'pink'		=>	'#FFC0CB',
		'pink1'		=>	'#FFB5C5',
		'pink2'		=>	'#EEA9B8',
		'pink3'		=>	'#CD919E',
		'pink4'		=>	'#8B636C',
		'palevioletred'		=>	'#DB7093',
		'palevioletred1'		=>	'#FF82AB',
		'palevioletred2'		=>	'#EE799F',
		'palevioletred3'		=>	'#CD6889',
		'palevioletred4'		=>	'#8B475D',
		'lavenderblush'		=>	'#FFF0F5',
		'lavenderblush1'		=>	'#FFF0F5',
		'lavenderblush2'		=>	'#EEE0E5',
		'lavenderblush3'		=>	'#CDC1C5',
		'lavenderblush4'		=>	'#8B8386',
		'violetred1'		=>	'#FF3E96',
		'violetred2'		=>	'#EE3A8C',
		'violetred3'		=>	'#CD3278',
		'violetred4'		=>	'#8B2252',
		'hotpink'		=>	'#FF69B4',
		'hotpink1'		=>	'#FF6EB4',
		'hotpink2'		=>	'#EE6AA7',
		'hotpink3'		=>	'#CD6090',
		'hotpink4'		=>	'#8B3A62',
		'raspberry'		=>	'#872657',
		'deeppink'		=>	'#FF1493',
		'deeppink1'		=>	'#FF1493',
		'deeppink2'		=>	'#EE1289',
		'deeppink3'		=>	'#CD1076',
		'deeppink4'		=>	'#8B0A50',
		'maroon1'		=>	'#FF34B3',
		'maroon2'		=>	'#EE30A7',
		'maroon3'		=>	'#CD2990',
		'maroon4'		=>	'#8B1C62',
		'mediumvioletred'		=>	'#C71585',
		'violetred'		=>	'#D02090',
		'orchid'		=>	'#DA70D6',
		'orchid1'		=>	'#FF83FA',
		'orchid2'		=>	'#EE7AE9',
		'orchid3'		=>	'#CD69C9',
		'orchid4'		=>	'#8B4789',
		'thistle'		=>	'#D8BFD8',
		'thistle1'		=>	'#FFE1FF',
		'thistle2'		=>	'#EED2EE',
		'thistle3'		=>	'#CDB5CD',
		'thistle4'		=>	'#8B7B8B',
		'plum1'		=>	'#FFBBFF',
		'plum2'		=>	'#EEAEEE',
		'plum3'		=>	'#CD96CD',
		'plum4'		=>	'#8B668B',
		'plum'		=>	'#DDA0DD',
		'violet'		=>	'#EE82EE',
		'fuchsia'		=>	'#FF00FF',
		'magenta'		=>	'#FF00FF',
		'magenta2'		=>	'#EE00EE',
		'magenta3'		=>	'#CD00CD',
		'magenta4'		=>	'#8B008B',
		'darkmagenta'		=>	'#8B008B',
		'purple'		=>	'#800080',
		'mediumorchid'		=>	'#BA55D3',
		'mediumorchid1'		=>	'#E066FF',
		'mediumorchid2'		=>	'#D15FEE',
		'mediumorchid3'		=>	'#B452CD',
		'mediumorchid4'		=>	'#7A378B',
		'darkviolet'		=>	'#9400D3',
		'darkorchid'		=>	'#9932CC',
		'darkorchid1'		=>	'#BF3EFF',
		'darkorchid2'		=>	'#B23AEE',
		'darkorchid3'		=>	'#9A32CD',
		'darkorchid4'		=>	'#68228B',
		'indigo'		=>	'#4B0082',
		'blueviolet'		=>	'#8A2BE2',
		'purple1'		=>	'#9B30FF',
		'purple2'		=>	'#912CEE',
		'purple3'		=>	'#7D26CD',
		'purple4'		=>	'#551A8B',
		'mediumpurple'		=>	'#9370DB',
		'mediumpurple1'		=>	'#AB82FF',
		'mediumpurple2'		=>	'#9F79EE',
		'mediumpurple3'		=>	'#8968CD',
		'mediumpurple4'		=>	'#5D478B',
		'darkslateblue'		=>	'#483D8B',
		'lightslateblue'		=>	'#8470FF',
		'mediumslateblue'		=>	'#7B68EE',
		'slateblue'		=>	'#6A5ACD',
		'slateblue1'		=>	'#836FFF',
		'slateblue2'		=>	'#7A67EE',
		'slateblue3'		=>	'#6959CD',
		'slateblue4'		=>	'#473C8B',
		'ghostwhite'		=>	'#F8F8FF',
		'lavender'		=>	'#E6E6FA',
		'blue'		=>	'#0000FF',
		'blue2'		=>	'#0000EE',
		'mediumblue'		=>	'#0000CD',
		'blue3'		=>	'#0000CD',
		'darkblue'		=>	'#00008B',
		'blue4'		=>	'#00008B',
		'navy'		=>	'#000080',
		'midnightblue'		=>	'#191970',
		'cobalt'		=>	'#3D59AB',
		'royalblue'		=>	'#4169E1',
		'royalblue1'		=>	'#4876FF',
		'royalblue2'		=>	'#436EEE',
		'royalblue3'		=>	'#3A5FCD',
		'royalblue4'		=>	'#27408B',
		'cornflowerblue'		=>	'#6495ED',
		'lightsteelblue'		=>	'#B0C4DE',
		'lightsteelblue1'		=>	'#CAE1FF',
		'lightsteelblue2'		=>	'#BCD2EE',
		'lightsteelblue3'		=>	'#A2B5CD',
		'lightsteelblue4'		=>	'#6E7B8B',
		'lightslategray'		=>	'#778899',
		'slategray'		=>	'#708090',
		'slategray1'		=>	'#C6E2FF',
		'slategray2'		=>	'#B9D3EE',
		'slategray3'		=>	'#9FB6CD',
		'slategray4'		=>	'#6C7B8B',
		'dodgerblue'		=>	'#1E90FF',
		'dodgerblue1'		=>	'#1E90FF',
		'dodgerblue2'		=>	'#1C86EE',
		'dodgerblue3'		=>	'#1874CD',
		'dodgerblue4'		=>	'#104E8B',
		'aliceblue'		=>	'#F0F8FF',
		'steelblue'		=>	'#4682B4',
		'steelblue1'		=>	'#63B8FF',
		'steelblue2'		=>	'#5CACEE',
		'steelblue3'		=>	'#4F94CD',
		'steelblue4'		=>	'#36648B',
		'lightskyblue'		=>	'#87CEFA',
		'lightskyblue1'		=>	'#B0E2FF',
		'lightskyblue2'		=>	'#A4D3EE',
		'lightskyblue3'		=>	'#8DB6CD',
		'lightskyblue4'		=>	'#607B8B',
		'skyblue1'		=>	'#87CEFF',
		'skyblue2'		=>	'#7EC0EE',
		'skyblue3'		=>	'#6CA6CD',
		'skyblue4'		=>	'#4A708B',
		'skyblue'		=>	'#87CEEB',
		'deepskyblue'		=>	'#00BFFF',
		'deepskyblue1'		=>	'#00BFFF',
		'deepskyblue2'		=>	'#00B2EE',
		'deepskyblue3'		=>	'#009ACD',
		'deepskyblue4'		=>	'#00688B',
		'peacock'		=>	'#33A1C9',
		'lightblue'		=>	'#ADD8E6',
		'lightblue1'		=>	'#BFEFFF',
		'lightblue2'		=>	'#B2DFEE',
		'lightblue3'		=>	'#9AC0CD',
		'lightblue4'		=>	'#68838B',
		'powderblue'		=>	'#B0E0E6',
		'cadetblue1'		=>	'#98F5FF',
		'cadetblue2'		=>	'#8EE5EE',
		'cadetblue3'		=>	'#7AC5CD',
		'cadetblue4'		=>	'#53868B',
		'turquoise1'		=>	'#00F5FF',
		'turquoise2'		=>	'#00E5EE',
		'turquoise3'		=>	'#00C5CD',
		'turquoise4'		=>	'#00868B',
		'cadetblue'		=>	'#5F9EA0',
		'darkturquoise'		=>	'#00CED1',
		'azure'		=>	'#F0FFFF',
		'azure1'		=>	'#F0FFFF',
		'azure2'		=>	'#E0EEEE',
		'azure3'		=>	'#C1CDCD',
		'azure4'		=>	'#838B8B',
		'lightcyan'		=>	'#E0FFFF',
		'lightcyan1'		=>	'#E0FFFF',
		'lightcyan2'		=>	'#D1EEEE',
		'lightcyan3'		=>	'#B4CDCD',
		'lightcyan4'		=>	'#7A8B8B',
		'paleturquoise1'		=>	'#BBFFFF',
		'paleturquoise'		=>	'#AEEEEE',
		'paleturquoise2'		=>	'#AEEEEE',
		'paleturquoise3'		=>	'#96CDCD',
		'paleturquoise4'		=>	'#668B8B',
		'darkslategray'		=>	'#2F4F4F',
		'darkslategray1'		=>	'#97FFFF',
		'darkslategray2'		=>	'#8DEEEE',
		'darkslategray3'		=>	'#79CDCD',
		'darkslategray4'		=>	'#528B8B',
		'aqua'		=>	'#00FFFF',
		'cyan'		=>	'#00FFFF',
		'cyan2'		=>	'#00EEEE',
		'cyan3'		=>	'#00CDCD',
		'darkcyan'		=>	'#008B8B',
		'cyan4'		=>	'#008B8B',
		'teal'		=>	'#008080',
		'mediumturquoise'		=>	'#48D1CC',
		'lightseagreen'		=>	'#20B2AA',
		'manganeseblue'		=>	'#03A89E',
		'turquoise'		=>	'#40E0D0',
		'coldgrey'		=>	'#808A87',
		'turquoiseblue'		=>	'#00C78C',
		'aquamarine'		=>	'#7FFFD4',
		'aquamarine1'		=>	'#7FFFD4',
		'aquamarine2'		=>	'#76EEC6',
		'mediumaquamarine'		=>	'#66CDAA',
		'aquamarine3'		=>	'#66CDAA',
		'aquamarine4'		=>	'#458B74',
		'mediumspringgreen'		=>	'#00FA9A',
		'mintcream'		=>	'#F5FFFA',
		'springgreen'		=>	'#00FF7F',
		'springgreen1'		=>	'#00EE76',
		'springgreen2'		=>	'#00CD66',
		'springgreen3'		=>	'#008B45',
		'mediumseagreen'		=>	'#3CB371',
		'seagreen1'		=>	'#54FF9F',
		'seagreen2'		=>	'#4EEE94',
		'seagreen3'		=>	'#43CD80',
		'seagreen4'		=>	'#2E8B57',
		'seagreen'		=>	'#2E8B57',
		'emeraldgreen'		=>	'#00C957',
		'mint'		=>	'#BDFCC9',
		'cobaltgreen'		=>	'#3D9140',
		'honeydew'		=>	'#F0FFF0',
		'honeydew1'		=>	'#F0FFF0',
		'honeydew2'		=>	'#E0EEE0',
		'honeydew3'		=>	'#C1CDC1',
		'honeydew4'		=>	'#838B83',
		'darkseagreen'		=>	'#8FBC8F',
		'darkseagreen1'		=>	'#C1FFC1',
		'darkseagreen2'		=>	'#B4EEB4',
		'darkseagreen3'		=>	'#9BCD9B',
		'darkseagreen4'		=>	'#698B69',
		'palegreen'		=>	'#98FB98',
		'palegreen1'		=>	'#9AFF9A',
		'lightgreen'		=>	'#90EE90',
		'palegreen2'		=>	'#90EE90',
		'palegreen3'		=>	'#7CCD7C',
		'palegreen4'		=>	'#548B54',
		'limegreen'		=>	'#32CD32',
		'forestgreen'		=>	'#228B22',
		'lime'		=>	'#00FF00',
		'green1'		=>	'#00FF00',
		'green2'		=>	'#00EE00',
		'green3'		=>	'#00CD00',
		'green4'		=>	'#008B00',
		'green'		=>	'#008000',
		'darkgreen'		=>	'#006400',
		'sapgreen'		=>	'#308014',
		'lawngreen'		=>	'#7CFC00',
		'chartreuse'		=>	'#7FFF00',
		'chartreuse1'		=>	'#7FFF00',
		'chartreuse2'		=>	'#76EE00',
		'chartreuse3'		=>	'#66CD00',
		'chartreuse4'		=>	'#458B00',
		'greenyellow'		=>	'#ADFF2F',
		'darkolivegreen1'		=>	'#CAFF70',
		'darkolivegreen2'		=>	'#BCEE68',
		'darkolivegreen3'		=>	'#A2CD5A',
		'darkolivegreen4'		=>	'#6E8B3D',
		'darkolivegreen'		=>	'#556B2F',
		'olivedrab'		=>	'#6B8E23',
		'olivedrab1'		=>	'#C0FF3E',
		'olivedrab2'		=>	'#B3EE3A',
		'yellowgreen'		=>	'#9ACD32',
		'olivedrab3'		=>	'#9ACD32',
		'olivedrab4'		=>	'#698B22',
		'ivory'		=>	'#FFFFF0',
		'ivory1'		=>	'#FFFFF0',
		'ivory2'		=>	'#EEEEE0',
		'ivory3'		=>	'#CDCDC1',
		'ivory4'		=>	'#8B8B83',
		'beige'		=>	'#F5F5DC',
		'lightyellow'		=>	'#FFFFE0',
		'lightyellow1'		=>	'#FFFFE0',
		'lightyellow2'		=>	'#EEEED1',
		'lightyellow3'		=>	'#CDCDB4',
		'lightyellow4'		=>	'#8B8B7A',
		'lightgoldenrodyellow'		=>	'#FAFAD2',
		'yellow'		=>	'#FFFF00',
		'yellow1'		=>	'#FFFF00',
		'yellow2'		=>	'#EEEE00',
		'yellow3'		=>	'#CDCD00',
		'yellow4'		=>	'#8B8B00',
		'warmgrey'		=>	'#808069',
		'olive'		=>	'#808000',
		'darkkhaki'		=>	'#BDB76B',
		'khaki1'		=>	'#FFF68F',
		'khaki2'		=>	'#EEE685',
		'khaki3'		=>	'#CDC673',
		'khaki4'		=>	'#8B864E',
		'khaki'		=>	'#F0E68C',
		'palegoldenrod'		=>	'#EEE8AA',
		'lemonchiffon'		=>	'#FFFACD',
		'lemonchiffon1'		=>	'#FFFACD',
		'lemonchiffon2'		=>	'#EEE9BF',
		'lemonchiffon3'		=>	'#CDC9A5',
		'lemonchiffon4'		=>	'#8B8970',
		'lightgoldenrod1'		=>	'#FFEC8B',
		'lightgoldenrod2'		=>	'#EEDC82',
		'lightgoldenrod3'		=>	'#CDBE70',
		'lightgoldenrod4'		=>	'#8B814C',
		'banana'		=>	'#E3CF57',
		'gold'		=>	'#FFD700',
		'gold1'		=>	'#FFD700',
		'gold2'		=>	'#EEC900',
		'gold3'		=>	'#CDAD00',
		'gold4'		=>	'#8B7500',
		'cornsilk'		=>	'#FFF8DC',
		'cornsilk1'		=>	'#FFF8DC',
		'cornsilk2'		=>	'#EEE8CD',
		'cornsilk3'		=>	'#CDC8B1',
		'cornsilk4'		=>	'#8B8878',
		'goldenrod'		=>	'#DAA520',
		'goldenrod1'		=>	'#FFC125',
		'goldenrod2'		=>	'#EEB422',
		'goldenrod3'		=>	'#CD9B1D',
		'goldenrod4'		=>	'#8B6914',
		'darkgoldenrod'		=>	'#B8860B',
		'darkgoldenrod1'		=>	'#FFB90F',
		'darkgoldenrod2'		=>	'#EEAD0E',
		'darkgoldenrod3'		=>	'#CD950C',
		'darkgoldenrod4'		=>	'#8B6508',
		'orange'		=>	'#FFA500',
		'orange1'		=>	'#FFA500',
		'orange2'		=>	'#EE9A00',
		'orange3'		=>	'#CD8500',
		'orange4'		=>	'#8B5A00',
		'floralwhite'		=>	'#FFFAF0',
		'oldlace'		=>	'#FDF5E6',
		'wheat'		=>	'#F5DEB3',
		'wheat1'		=>	'#FFE7BA',
		'wheat2'		=>	'#EED8AE',
		'wheat3'		=>	'#CDBA96',
		'wheat4'		=>	'#8B7E66',
		'moccasin'		=>	'#FFE4B5',
		'papayawhip'		=>	'#FFEFD5',
		'blanchedalmond'		=>	'#FFEBCD',
		'navajowhite'		=>	'#FFDEAD',
		'navajowhite1'		=>	'#FFDEAD',
		'navajowhite2'		=>	'#EECFA1',
		'navajowhite3'		=>	'#CDB38B',
		'navajowhite4'		=>	'#8B795E',
		'eggshell'		=>	'#FCE6C9',
		'tan'		=>	'#D2B48C',
		'brick'		=>	'#9C661F',
		'cadmiumyellow'		=>	'#FF9912',
		'antiquewhite'		=>	'#FAEBD7',
		'antiquewhite1'		=>	'#FFEFDB',
		'antiquewhite2'		=>	'#EEDFCC',
		'antiquewhite3'		=>	'#CDC0B0',
		'antiquewhite4'		=>	'#8B8378',
		'burlywood'		=>	'#DEB887',
		'burlywood1'		=>	'#FFD39B',
		'burlywood2'		=>	'#EEC591',
		'burlywood3'		=>	'#CDAA7D',
		'burlywood4'		=>	'#8B7355',
		'bisque'		=>	'#FFE4C4',
		'bisque1'		=>	'#FFE4C4',
		'bisque2'		=>	'#EED5B7',
		'bisque3'		=>	'#CDB79E',
		'bisque4'		=>	'#8B7D6B',
		'melon'		=>	'#E3A869',
		'carrot'		=>	'#ED9121',
		'darkorange'		=>	'#FF8C00',
		'darkorange1'		=>	'#FF7F00',
		'darkorange2'		=>	'#EE7600',
		'darkorange3'		=>	'#CD6600',
		'darkorange4'		=>	'#8B4500',
		'orange'		=>	'#FF8000',
		'tan1'		=>	'#FFA54F',
		'tan2'		=>	'#EE9A49',
		'peru'		=>	'#CD853F',
		'tan3'		=>	'#CD853F',
		'tan4'		=>	'#8B5A2B',
		'linen'		=>	'#FAF0E6',
		'peachpuff'		=>	'#FFDAB9',
		'peachpuff1'		=>	'#FFDAB9',
		'peachpuff2'		=>	'#EECBAD',
		'peachpuff3'		=>	'#CDAF95',
		'peachpuff4'		=>	'#8B7765',
		'seashell'		=>	'#FFF5EE',
		'seashell1'		=>	'#FFF5EE',
		'seashell2'		=>	'#EEE5DE',
		'seashell3'		=>	'#CDC5BF',
		'seashell4'		=>	'#8B8682',
		'sandybrown'		=>	'#F4A460',
		'rawsienna'		=>	'#C76114',
		'chocolate'		=>	'#D2691E',
		'chocolate1'		=>	'#FF7F24',
		'chocolate2'		=>	'#EE7621',
		'chocolate3'		=>	'#CD661D',
		'saddlebrown'		=>	'#8B4513',
		'chocolate4'		=>	'#8B4513',
		'ivoryblack'		=>	'#292421',
		'flesh'		=>	'#FF7D40',
		'cadmiumorange'		=>	'#FF6103',
		'burntsienna'		=>	'#8A360F',
		'sienna'		=>	'#A0522D',
		'sienna1'		=>	'#FF8247',
		'sienna2'		=>	'#EE7942',
		'sienna3'		=>	'#CD6839',
		'sienna4'		=>	'#8B4726',
		'lightsalmon'		=>	'#FFA07A',
		'lightsalmon'		=>	'#FFA07A',
		'lightsalmon2'		=>	'#EE9572',
		'lightsalmon3'		=>	'#CD8162',
		'lightsalmon4'		=>	'#8B5742',
		'coral'		=>	'#FF7F50',
		'orangered'		=>	'#FF4500',
		'orangered1'		=>	'#FF4500',
		'orangered2'		=>	'#EE4000',
		'orangered3'		=>	'#CD3700',
		'orangered4'		=>	'#8B2500',
		'sepia'		=>	'#5E2612',
		'darksalmon'		=>	'#E9967A',
		'salmon1'		=>	'#FF8C69',
		'salmon2'		=>	'#EE8262',
		'salmon3'		=>	'#CD7054',
		'salmon4'		=>	'#8B4C39',
		'coral1'		=>	'#FF7256',
		'coral2'		=>	'#EE6A50',
		'coral3'		=>	'#CD5B45',
		'coral4'		=>	'#8B3E2F',
		'burntumber'		=>	'#8A3324',
		'tomato'		=>	'#FF6347',
		'tomato1'		=>	'#FF6347',
		'tomato2'		=>	'#EE5C42',
		'tomato3'		=>	'#CD4F39',
		'tomato4'		=>	'#8B3626',
		'salmon'		=>	'#FA8072',
		'mistyrose'		=>	'#FFE4E1',
		'mistyrose1'		=>	'#FFE4E1',
		'mistyrose2'		=>	'#EED5D2',
		'mistyrose3'		=>	'#CDB7B5',
		'mistyrose4'		=>	'#8B7D7B',
		'snow'		=>	'#FFFAFA',
		'snow1'		=>	'#FFFAFA',
		'snow2'		=>	'#EEE9E9',
		'snow3'		=>	'#CDC9C9',
		'snow4'		=>	'#8B8989',
		'rosybrown'		=>	'#BC8F8F',
		'rosybrown1'		=>	'#FFC1C1',
		'rosybrown2'		=>	'#EEB4B4',
		'rosybrown3'		=>	'#CD9B9B',
		'rosybrown4'		=>	'#8B6969',
		'lightcoral'		=>	'#F08080',
		'indianred'		=>	'#CD5C5C',
		'indianred1'		=>	'#FF6A6A',
		'indianred2'		=>	'#EE6363',
		'indianred4'		=>	'#8B3A3A',
		'indianred3'		=>	'#CD5555',
		'brown'		=>	'#A52A2A',
		'brown1'		=>	'#FF4040',
		'brown2'		=>	'#EE3B3B',
		'brown3'		=>	'#CD3333',
		'brown4'		=>	'#8B2323',
		'firebrick'		=>	'#B22222',
		'firebrick1'		=>	'#FF3030',
		'firebrick2'		=>	'#EE2C2C',
		'firebrick3'		=>	'#CD2626',
		'firebrick4'		=>	'#8B1A1A',
		'red'		=>	'#FF0000',
		'red1'		=>	'#FF0000',
		'red2'		=>	'#EE0000',
		'red3'		=>	'#CD0000',
		'darkred'		=>	'#8B0000',
		'red4'		=>	'#8B0000',
		'maroon'		=>	'#800000',
		'sgibeet'		=>	'#8E388E',
		'sgislateblue'		=>	'#7171C6',
		'sgilightblue'		=>	'#7D9EC0',
		'sgiteal'		=>	'#388E8E',
		'sgichartreuse'		=>	'#71C671',
		'sgiolivedrab'	=>	'#8E8E38',
		'sgibrightgray'	=>	'#C5C1AA',
		'sgisalmon'		=>	'#C67171',
		'sgidarkgray'	=>		'#555555',
		'sgigray12'		=>	'#1E1E1E',
		'sgigray16'		=>	'#282828',
		'sgigray32'		=>	'#515151',
		'sgigray36'		=>	'#5B5B5B',
		'sgigray52'		=>	'#848484',
		'sgigray56'		=>	'#8E8E8E',
		'sgilightgray'		=>	'#AAAAAA',
		'sgigray72'		=>	'#B7B7B7',
		'sgigray76'		=>	'#C1C1C1',
		'sgigray92'		=>	'#EAEAEA',
		'sgigray96'		=>	'#F4F4F4',
		'white'		=>	'#FFFFFF',
		'gainsboro'		=>	'#DCDCDC',
		'lightgrey'		=>	'#D3D3D3',
		'silver'		=>	'#C0C0C0',
		'darkgray'		=>	'#A9A9A9',
		'gray'		=>	'#808080',
		'black'		=>	'#000000',
		'gray99'		=>	'#FCFCFC',
		'gray98'		=>	'#FAFAFA',
		'gray97'		=>	'#F7F7F7',
		'gray96'		=>	'#F5F5F5',
		'whitesmoke'		=>	'#F5F5F5',
		'gray95'		=>	'#F2F2F2',
		'gray94'		=>	'#F0F0F0',
		'gray93'		=>	'#EDEDED',
		'gray92'		=>	'#EBEBEB',
		'gray91'		=>	'#E8E8E8',
		'gray90'		=>	'#E5E5E5',
		'gray89'		=>	'#E3E3E3',
		'gray88'		=>	'#E0E0E0',
		'gray87'		=>	'#DEDEDE',
		'gray86'		=>	'#DBDBDB',
		'gray85'		=>	'#D9D9D9',
		'gray84'		=>	'#D6D6D6',
		'gray83'		=>	'#D4D4D4',
		'gray82'		=>	'#D1D1D1',
		'gray81'		=>	'#CFCFCF',
		'gray80'		=>	'#CCCCCC',
		'gray79'		=>	'#C9C9C9',
		'gray78'		=>	'#C7C7C7',
		'gray77'		=>	'#C4C4C4',
		'gray76'		=>	'#C2C2C2',
		'gray75'		=>	'#BFBFBF',
		'gray74'		=>	'#BDBDBD',
		'gray73'		=>	'#BABABA',
		'gray72'		=>	'#B8B8B8',
		'gray71'		=>	'#B5B5B5',
		'gray70'		=>	'#B3B3B3',
		'gray69'		=>	'#B0B0B0',
		'gray68'		=>	'#ADADAD',
		'gray67'		=>	'#ABABAB',
		'gray66'		=>	'#A8A8A8',
		'gray65'		=>	'#A6A6A6',
		'gray64'		=>	'#A3A3A3',
		'gray63'		=>	'#A1A1A1',
		'gray62'		=>	'#9E9E9E',
		'gray61'		=>	'#9C9C9C',
		'gray60'		=>	'#999999',
		'gray59'		=>	'#969696',
		'gray58'		=>	'#949494',
		'gray57'		=>	'#919191',
		'gray56'		=>	'#8F8F8F',
		'gray55'		=>	'#8C8C8C',
		'gray54'		=>	'#8A8A8A',
		'gray53'		=>	'#878787',
		'gray52'		=>	'#858585',
		'gray51'		=>	'#828282',
		'gray50'		=>	'#7F7F7F',
		'gray49'		=>	'#7D7D7D',
		'gray48'		=>	'#7A7A7A',
		'gray47'		=>	'#787878',
		'gray46'		=>	'#757575',
		'gray45'		=>	'#737373',
		'gray44'		=>	'#707070',
		'gray43'		=>	'#6E6E6E',
		'gray42'		=>	'#6B6B6B',
		'dimgray'		=>	'#696969',
		'gray40'		=>	'#666666',
		'gray39'		=>	'#636363',
		'gray38'		=>	'#616161',
		'gray37'		=>	'#5E5E5E',
		'gray36'		=>	'#5C5C5C',
		'gray35'		=>	'#595959',
		'gray34'		=>	'#575757',
		'gray33'		=>	'#545454',
		'gray32'		=>	'#525252',
		'gray31'		=>	'#4F4F4F',
		'gray30'		=>	'#4D4D4D',
		'gray29'		=>	'#4A4A4A',
		'gray28'		=>	'#474747',
		'gray27'		=>	'#454545',
		'gray26'		=>	'#424242',
		'gray25'		=>	'#404040',
		'gray24'		=>	'#3D3D3D',
		'gray23'		=>	'#3B3B3B',
		'gray22'		=>	'#383838',
		'gray21'		=>	'#363636',
		'gray20'		=>	'#333333',
		'gray19'		=>	'#303030',
		'gray18'		=>	'#2E2E2E',
		'gray17'		=>	'#2B2B2B',
		'gray16'		=>	'#292929',
		'gray15'		=>	'#262626',
		'gray14'		=>	'#242424',
		'gray13'		=>	'#212121',
		'gray12'		=>	'#1F1F1F',
		'gray11'		=>	'#1C1C1C',
		'gray10'		=>	'#1A1A1A',
		'gray9'		=>	'#171717',
		'gray8'		=>	'#141414',
		'gray7'		=>	'#121212',
		'gray6'		=>	'#0F0F0F',
		'gray5'		=>	'#0D0D0D',
		'gray4'		=>	'#0A0A0A',
		'gray3'		=>	'#080808',
		'gray2'		=>	'#050505',
		'gray1'		=>	'#030303',

	);

	our $reverse_color_map;

1;
