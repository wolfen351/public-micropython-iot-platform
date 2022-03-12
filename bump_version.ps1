# increment the version 
$raw = Get-Content -Path .\version -Raw
$v = [version]$raw
$nv = [version]::New($v.Major,$v.Minor,$v.Build+1,0)
$newVersion = "$($nv)";
$newVersion = $newVersion.Substring(0, $newVersion.Length - 2)
Write-Output "Version is now: $newVersion"
Write-Output $newVersion | Out-File -encoding ascii .\version