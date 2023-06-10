<?php

function substr_startswith($haystack, $needle) {
    return substr($haystack, 0, strlen($needle)) === $needle;
}

header('Content-Type: application/json');

$dir          = $_GET["dir"];

$basepath = __DIR__;
$realBase = realpath($basepath);

$userpath = $basepath . DIRECTORY_SEPARATOR . $_GET['dir'];
$realUserPath = realpath($userpath);

if ($realUserPath === false || !substr_startswith($realUserPath, $realBase)) {
    //Directory Traversal!
    header('HTTP/1.0 401 Unauthorized');
    echo '{ "Error" : "Directory Traversal Detected" }';
    exit;
}

$list = array(); //main array

if(is_dir($dir)){
    if($dh = opendir($dir)){
        while(($file = readdir($dh)) != false){

            if ($file == "." or $file == ".." or pathinfo($file, PATHINFO_EXTENSION) != 'bin') {
                // ignored file
            } else {
                array_push($list, $file);
            }
        }
    }

    $return_array = array('files'=> $list);

    echo json_encode($return_array);
}
else
{
  echo json_encode("Not a dir: $dir");
}

?>
