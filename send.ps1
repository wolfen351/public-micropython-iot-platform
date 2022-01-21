 	
$param1=$args[0]

echo "Sending file $($param1)"
ampy --port COM4 put $param1
