param([Parameter(Mandatory=$true)][string]$Installer, [string]$ImageDirectory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$assembly = [Reflection.Assembly]::LoadFile((Resolve-Path -LiteralPath $Installer).Path)
$type = $assembly.GetType('Setup')
$flags = [Reflection.BindingFlags]'Instance,NonPublic'
$previous = $env:NAATIK_WINDOWS_PROFILE
$profile = Join-Path ([IO.Path]::GetTempPath()) ('naatik-language-test-' + [guid]::NewGuid().ToString('N'))
$env:NAATIK_WINDOWS_PROFILE = $profile
function New-Setup { return [Activator]::CreateInstance($type,$true) }
function Field($form,$name) { return $type.GetField($name,$flags).GetValue($form) }
function Check($condition,$message) { if (-not $condition) { throw $message } }
function Render($form,$name) {
    if (-not $ImageDirectory) { return }
    New-Item -ItemType Directory -Path $ImageDirectory -Force | Out-Null
    $bitmap = New-Object Drawing.Bitmap($form.Width,$form.Height)
    try {
        $form.ShowInTaskbar = $false
        $form.StartPosition = 'Manual'
        $form.Location = New-Object Drawing.Point(-32000,-32000)
        $form.Show()
        [Windows.Forms.Application]::DoEvents()
        $form.DrawToBitmap($bitmap,(New-Object Drawing.Rectangle(0,0,$form.Width,$form.Height)))
        $bitmap.Save((Join-Path (Resolve-Path $ImageDirectory).Path ($name+'.png')),[Drawing.Imaging.ImageFormat]::Png)
    } finally { $form.Hide(); $bitmap.Dispose() }
}
try {
    $form = New-Setup
    try {
        Check ((Field $form 'languages').SelectedIndex -eq -1) 'New install must require a language selection'
        Check (-not (Field $form 'install').Enabled) 'Install must be disabled before selection'
        Check (-not (Test-Path -LiteralPath $profile)) 'Opening installer must not create the profile'
        Render $form 'installer-choice'
        foreach ($index in @(0,1)) {
            (Field $form 'languages').SelectedIndex = $index
            Check ((Field $form 'install').Enabled) 'Selection should enable Install'
            $expected = if ($index -eq 0) { 'Instalar / reparar' } else { 'Install / repair' }
            Check ((Field $form 'install').Text -eq $expected) 'Install button language mismatch'
            Check (-not (Field $form 'busy')) 'Selecting a language must not start installation'
            Render $form ('installer-'+$index)
        }
    } finally { $form.Dispose() }
    $config=Join-Path $profile 'config'
    New-Item -ItemType Directory -Path $config -Force | Out-Null
    $settings=Join-Path $config 'settings.json'
    $content='{"ocr_language":"jpn","translation_route":["ja","en","es"],"tutorial":{"status":"skipped","step":2}}'
    [IO.File]::WriteAllText($settings,$content)
    foreach ($code in @('es','en')) {
        [IO.File]::WriteAllText((Join-Path $config 'ui-language.txt'),$code)
        $form=New-Setup
        try {
            $expected=if ($code -eq 'es') {0} else {1}
            Check ((Field $form 'languages').SelectedIndex -eq $expected) 'Repair must preselect the existing language'
            Check ([IO.File]::ReadAllText($settings) -eq $content) 'Repair selection altered preferences'
            Check (-not (Field $form 'busy')) 'Repair must not start automatically'
        } finally {$form.Dispose()}
    }
    # Exercise the PowerShell 5 catalog reader, including case-distinct JSON keys.
    $oldLanguage=$env:NAATIK_UI_LANGUAGE
    try {
        foreach ($code in @('es','en')) {
            $env:NAATIK_UI_LANGUAGE=$code
            . (Join-Path (Split-Path -Parent $PSScriptRoot) 'packaging\language.ps1')
            $expected=if ($code -eq 'es') { 'Instalar / reparar' } else { 'Install / repair' }
            Check ((L 'setup.install') -eq $expected) 'PowerShell catalog language mismatch'
        }
    } finally {$env:NAATIK_UI_LANGUAGE=$oldLanguage}
    Write-Output 'PASS: new installer selection, es/en labels, no automatic work, repair preselection and unchanged preferences (automated hidden forms).'
} finally {
    $env:NAATIK_WINDOWS_PROFILE=$previous
    # Keep this small isolated profile as evidence; never touch a habitual profile.
    Write-Output ('Test profile: ' + $profile)
}
