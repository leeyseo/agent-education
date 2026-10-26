param([string]$InFile, [string]$OutFile, [int]$Rate = 2)

# Windows 한국어 음성(Heami)으로 텍스트 파일을 wav로 읽는다 (24kHz, 16bit, mono)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Heami Desktop')
$s.Rate = $Rate
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(24000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
$s.SetOutputToWaveFile($OutFile, $fmt)
$s.Speak((Get-Content -Raw -Encoding UTF8 $InFile))
$s.Dispose()
