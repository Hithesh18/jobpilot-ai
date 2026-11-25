param([string]$Script)
$body = @{ scriptPath = (Resolve-Path $Script).Path } | ConvertTo-Json
try {
    (Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:9333 -Method POST -Body $body -ContentType 'application/json' -TimeoutSec 300).Content
} catch {
    $r = $_.Exception.Response
    if ($r) {
        $sr = New-Object IO.StreamReader($r.GetResponseStream())
        $t = $sr.ReadToEnd()
        $t.Substring(0, [Math]::Min(1500, $t.Length))
    } else {
        $_.Exception.Message
    }
}
