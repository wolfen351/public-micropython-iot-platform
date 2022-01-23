Get-ChildItem -File | Foreach { 

    if ($_.name -Like "*.py" -or $_.name -Like "*.js" -or $_.name -Like "*.settings" -or $_.name -Like "*.html" ) {

        echo "Sending file $($_.name)"
        ampy --port COM5 put $_.name 
    }
}

