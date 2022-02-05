 	
$param1=$args[0]

echo "Sending file $($param1)"
ampy --port COM5 put $param1
