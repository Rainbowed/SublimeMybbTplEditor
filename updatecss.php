<?php
define("IN_MYBB", 1);
define("NO_ONLINE", 1);
define('THIS_SCRIPT', 'updatecss.php');

$password = ''; # Edit this to your password

if($password == '')
    die('Invalid password');

require_once "./inc/init.php";
require_once "./admin/inc/functions_themes.php";

if((string) $mybb->input['password'] != $password)
    die('Invalid password');

$stylesheet = $mybb->input['stylesheet'];
$tid = intval($mybb->input['tid']);
$name = $mybb->input['name'];

if(empty($tid) || empty($name) || empty($stylesheet))
	exit;

$updated_stylesheet = array(
	"stylesheet" => $db->escape_string(unfix_css_urls($stylesheet)),
	"lastmodified" => TIME_NOW,
);

if($db->update_query("themestylesheets", $updated_stylesheet, "tid='{$tid}' AND name='{$db->escape_string($name)}'"))
	cache_stylesheet($tid, $name, $stylesheet);

echo 'Updated';
