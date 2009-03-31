<?


$guard = "";
if(isset($_GET['guard'])) {
	$guard = "&guard=1";
} // end if

if(!isset($_GET['frame'])) {

print <<<HERE

<html>
<head>
<meta name="robots" content="noindex">
</head>
<frameset cols="125, *" border="0">
	<frame src="logs.php?frame=left$guard" name="logleft" scrolling="auto">
	<frame src="logs.php?frame=blank$guard" name="logright" scrolling="auto">
</frameset>
</html>

HERE;
} else if($_GET['frame'] == "left") {

	tehheader(' html { border-right: 1px solid #808080; } ');

	$d = opendir("./logs");
	$files = array();
	while (false !== ($filename = readdir($d))) {
		//messages-2004-03-28-21.html
		if(preg_match("/^messages\-(\d\d\d\d\-\d\d\-\d\d)\-(\d\d)\.html$/", $filename, $matches)) {
			$files[] = $matches;
		} // end if
	} // end while
	closedir($d);

	rsort($files);
	$files = array_slice($files, 0, isset($_GET['guard']) ? 1000 : 200);
	$last_date = "";
	foreach($files as $matches) {
		if($matches[1] != $last_date) {
			print "<hr class=\"hrs\" />Logs for $matches[1]:";
			$last_date = $matches[1];
		} // end if
		print "<br /><a href=\"logs.php?frame=right&date=$matches[1]&time=$matches[2]$guard\" target=\"logright\">$matches[2]:00</a>";
	} // end foreach

	tehfoot();
	exit;
} elseif($_GET['frame'] == "right") {

	$date = "";
	$time = "";
	if(preg_match("/^\d\d\d\d\-\d\d\-\d\d$/", $_GET['date'])) {
		$date = $_GET['date'];
	} // end if
	if(preg_match("/^\d\d$/", $_GET['time'])) {
		$time = $_GET['time'];
	} // end if

	ob_start();
	include("./logs/messages-$date-$time.html");
	$var = ob_get_clean();

	if(isset($_GET['guard'])) {
		print preg_replace("/<\!\-\- ([\d\.]+) -->/", " ^ [$1]", $var);
	} else {
		print preg_replace("/<\!\-\- [\d\.]+ -->/", "", $var);
	} // end if

	exit;

} elseif($_GET['frame'] == "blank") {
	tehheader(); tehfoot();
	exit;
} // end if

function tehfoot () {
	print <<<THEFOOT
</body></html>
THEFOOT;
} // end tehfoot

function tehheader ($style = "") {
	print <<<THEHEAD
<html><head>
<title>CHAT NAME GOES HERE</title>
<link rel="stylesheet" type="text/css" href="style.php" />
<style type="text/css">
$style
</style>
</head><body bgcolor="black" text="white">

THEHEAD;
} // end function

?>
