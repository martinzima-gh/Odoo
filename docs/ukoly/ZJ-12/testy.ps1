# Testy kombinací stavů a uzavřených vzorců nad referenčním modelem.
# Spuštění: powershell -NoProfile -ExecutionPolicy Bypass -File testy.ps1
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'model.ps1')

$failures = New-Object System.Collections.ArrayList
$passed = 0
function Assert-Close([string]$name, [double]$actual, [double]$expected, [double]$tol = 0.005) {
    if ([Math]::Abs($actual - $expected) -gt $tol) {
        [void]$script:failures.Add("$name : očekáváno $expected, vyšlo $actual")
    } else { $script:passed++ }
}
function Assert-True([string]$name, [bool]$ok, [string]$detail = '') {
    if (-not $ok) { [void]$script:failures.Add("$name $detail") } else { $script:passed++ }
}

function New-Scenario($name, $classes, $rc, $hwmA, $f1, $f2, $r, $t) {
    return @{ Name = $name; Classes = $classes; Rc = $rc; HwmA = $hwmA; f1 = $f1; f2 = $f2; r = $r; t = $t;
              s1 = 0; s2 = 0; sp = 0; st = 2 }
}
function Copy-Scenario($sc, $s1, $s2, $sp, $st) {
    $copy = $sc.Clone(); $copy.s1 = $s1; $copy.s2 = $s2; $copy.sp = $sp; $copy.st = $st
    return $copy
}

$two = @(@{ Code = 'A'; Pre = 1000000.0 }, @{ Code = 'B'; Pre = 1000000.0 })
$one = @(@{ Code = 'A'; Pre = 1000000.0 })
$scenarios = @(
    (New-Scenario 'Z1 dvě třídy, zisk' $two 100000.0 1000000.0 0.01 0.002 0.2 0.05),
    (New-Scenario 'Z2 dvě třídy, ztráta' $two -50000.0 1000000.0 0.01 0.002 0.2 0.05),
    (New-Scenario 'Z3 kolem HWM a nuly daně' $two 2000.0 1000000.0 0.01 0.002 0.2 0.05),
    (New-Scenario 'Z4 jedna třída, zisk' $one 100000.0 1000000.0 0.01 0.002 0.2 0.05),
    (New-Scenario 'Z5 zátěž (vysoké sazby)' $two 300000.0 1000000.0 0.05 0.05 0.5 0.3)
)

# --- 1. Všechny kombinace stavů -------------------------------------------------------------------
$combos = 0; $maxSteps = 0; $todayChecked = 0; $maxResidual = 0.0
foreach ($base in $scenarios) {
    foreach ($s1 in 0..3) { foreach ($s2 in 0..3) { foreach ($sp in 0, 1, 3) { foreach ($st in 0..2) {
        $sc = Copy-Scenario $base $s1 $s2 $sp $st
        $label = "$($sc.Name) [F1 S$s1, F2 S$s2, P S$sp, daň S$st]"
        $combos++
        $low = Invoke-Solve $sc (New-Amounts 0 0 0 0)
        $high = Invoke-Solve $sc (New-Amounts 300000 300000 300000 300000)
        Assert-True "$label konverguje z nuly" $low.Converged "poslední rozdíl kroků $($low.Last)"
        Assert-True "$label konverguje ze shora" $high.Converged "poslední rozdíl kroků $($high.Last)"
        $maxSteps = [Math]::Max($maxSteps, [Math]::Max($low.Steps, $high.Steps))
        $x = $low.X
        Assert-True "$label jediné řešení" ((Get-Distance $x $high.X) -lt 1e-6) "rozdíl $(Get-Distance $x $high.X)"
        # Relativní tolerance: 1e-10 × největší částka (částky ve statisících, double má ~16 platných míst).
        $scale = [Math]::Max(1.0, [Math]::Max([Math]::Max($x.F1, $x.F2), [Math]::Max($x.P, $x.T)))
        $residual = Get-Distance (Invoke-Step $sc $x) $x
        $maxResidual = [Math]::Max($maxResidual, $residual / $scale)
        Assert-True "$label konzistence (přepočet z konečných čísel)" ($residual -lt 1e-10 * $scale) "zbytek $residual"
        $n0 = 0.0; foreach ($c in $sc.Classes) { $n0 += $c.Pre }; $n0 += $sc.Rc
        $nav = Get-Nav $sc $x $true $true $true
        Assert-Close "$label NAV = hrubý − úplaty − odměna − daň" $nav ($n0 - $x.F1 - $x.F2 - $x.P - $x.T) 1e-6
        $split = Get-TaxSplit $sc $x $st
        $sum = 0.0; foreach ($v in $split.Values) { $sum += $v }
        Assert-Close "$label součet daně tříd = daň fondu" $sum $x.T 1e-6
        Assert-True "$label částky nezáporné" (($x.F1 -ge -1e-9) -and ($x.F2 -ge -1e-9) -and ($x.P -ge -1e-9) -and ($x.T -ge -1e-9))
        if ($s1 -le 1 -and $s2 -le 1 -and $sp -le 1 -and $st -eq 2) {
            $today = Invoke-Today $sc
            Assert-True "$label shoda s dnešním pevným pořadím" ((Get-Distance $x $today) -lt 1e-6) "rozdíl $(Get-Distance $x $today)"
            $todayChecked++
        }
    } } } }
}

# --- 2. Uzavřené vzorce a příklady z návrhu -------------------------------------------------------
$closed = New-Object System.Collections.ArrayList
function Add-Closed($name, $actual, $expected) {
    Assert-Close $name $actual $expected
    [void]$script:closed.Add([pscustomobject]@{ Případ = $name; Model = [Math]::Round($actual, 4); Vzorec = [Math]::Round($expected, 4) })
}

# C1 test_base_after_all_fees: obě úplaty po úplatách, S = 0,011 F / 1,011 (jedna třída = celý fond)
$sc = Copy-Scenario (New-Scenario 'C1' $one 0.0 0.0 0.01 0.001 0 0) 1 1 0 2
$x = (Invoke-Solve $sc (New-Amounts 0 0 0 0)).X
Add-Closed 'C1 obě úplaty S1: obhospodařování' $x.F1 9891.20
Add-Closed 'C1 obě úplaty S1: administrace' $x.F2 989.12

# C2 test_base_mixed: obhospodařování S0, administrace S1
$sc = Copy-Scenario (New-Scenario 'C2' $one 0.0 0.0 0.01 0.001 0 0) 0 1 0 2
$x = (Invoke-Solve $sc (New-Amounts 0 0 0 0)).X
Add-Closed 'C2 S0 + S1: obhospodařování' $x.F1 10000.00
Add-Closed 'C2 S0 + S1: administrace' $x.F2 989.01

# C3 otázka 2: odměna S3, daň S2, P = r (V − H − t R) / (1 − r t)
$sc = Copy-Scenario (New-Scenario 'C3' @(@{ Code = 'A'; Pre = 1000.0 }) 100.0 1000.0 0 0 0.2 0.05) 0 0 3 2
$x = (Invoke-Solve $sc (New-Amounts 0 0 0 0)).X
Add-Closed 'C3 odměna po dani: odměna' $x.P (0.2 * (100 - 0.05 * 100) / (1 - 0.2 * 0.05))
Add-Closed 'C3 odměna po dani: daň' $x.T (0.05 * (100 - 0.2 * 95 / 0.99))

# C4 otázka 5: úplata S3 (po dani), daň S1, bez odměny: S = f (N − t R) / (1 + f (1 − t))
$sc = Copy-Scenario (New-Scenario 'C4' $one 100000.0 0.0 0.01 0 0 0.05) 3 0 0 1
$x = (Invoke-Solve $sc (New-Amounts 0 0 0 0)).X
$s = 0.01 * (1100000 - 0.05 * 100000) / (1 + 0.01 * 0.95)
Add-Closed 'C4 úplata po dani: úplata' $x.F1 $s
Add-Closed 'C4 úplata po dani: daň' $x.T (0.05 * (100000 - $s))

# C5 otázka 3: A, B po 1 000 000, výsledek 100 000, odměna A 10 000, daň 5 %
$sc = Copy-Scenario (New-Scenario 'C5' $two 100000.0 1000000.0 0 0 0.2 0.05) 0 0 0 2
$x = (Invoke-Solve $sc (New-Amounts 0 0 0 0)).X
Add-Closed 'C5 daňový efekt: odměna A' $x.P 10000
Add-Closed 'C5 daňový efekt: daň fondu' $x.T 4500
Add-Closed 'C5 daňový efekt: kapitál A' (Get-ClassValue $sc $x 'A' $true $true $true) 1038000
Add-Closed 'C5 daňový efekt: kapitál B' (Get-ClassValue $sc $x 'B' $true $true $true) 1047500

# C6 ztráta: daň 0, přesun 0
$sc = Copy-Scenario (New-Scenario 'C6' $two -50000.0 1000000.0 0.01 0.002 0.2 0.05) 0 0 0 2
$x = (Invoke-Solve $sc (New-Amounts 0 0 0 0)).X
$split = Get-TaxSplit $sc $x 2
Add-Closed 'C6 ztráta: daň' $x.T 0
Add-Closed 'C6 ztráta: daň třídy A' $split['A'] 0

# C7 přechod přes nulu: výsledek 5 000, úplata třídy A 1 % z kapitálu A, daň 0, úspora 250 patří A
$sc = Copy-Scenario (New-Scenario 'C7' $two 5000.0 1000000.0 0 0.01 0 0.05) 0 0 0 1
$x = (Invoke-Solve $sc (New-Amounts 0 0 0 0)).X
$split = Get-TaxSplit $sc $x 1
Add-Closed 'C7 přechod přes nulu: úplata A' $x.F2 10025
Add-Closed 'C7 přechod přes nulu: daň fondu' $x.T 0
Add-Closed 'C7 přechod přes nulu: daň třídy A' $split['A'] -125
Add-Closed 'C7 přechod přes nulu: daň třídy B' $split['B'] 125

# --- 3. Oprava s pevnou částkou (otázka 12) -------------------------------------------------------
# C8 test_correction_lowers_cost_before_after_fees: 1 % po úplatách, oprava −100 → výsledek 9 800,99, FK 990 199,01
$sc = Copy-Scenario (New-Scenario 'C8' $one 0.0 0.0 0.01 0 0 0) 1 0 0 2
$res = Invoke-SolveWithCorrections $sc @{ F1 = -100.0 }
Add-Closed 'C8 oprava úplaty S1: vypočteno bez opravy' $res.Base.F1 (0.01 * 1000000 / 1.01)
Add-Closed 'C8 oprava úplaty S1: výsledek' $res.X.F1 (0.01 * 1000000 / 1.01 - 100)
Add-Closed 'C8 oprava úplaty S1: FK' (Get-Nav $res.Scenario $res.X $true $true $true) (1000000 - (0.01 * 1000000 / 1.01 - 100))

# Všechny kombinace scénářů Z1 a Z4, oprava každého pravidla zvlášť:
# výsledek = vypočteno bez opravy + oprava; ostatní pravidla konzistentní s konečnými čísly; NAV sedí.
$corrChecks = 0
$correctionsByRule = @(@{ F1 = -100.0 }, @{ F2 = -50.0 }, @{ P = -30.0 }, @{ T = -20.0 })
foreach ($base in @($scenarios[0], $scenarios[3])) {
    foreach ($s1 in 0..3) { foreach ($s2 in 0..3) { foreach ($sp in 0, 1, 3) { foreach ($st in 0..2) {
        $sc = Copy-Scenario $base $s1 $s2 $sp $st
        foreach ($corr in $correctionsByRule) {
            $key = @($corr.Keys)[0]
            $label = "$($sc.Name) [F1 S$s1, F2 S$s2, P S$sp, daň S$st] oprava $key"
            $res = Invoke-SolveWithCorrections $sc $corr
            Assert-True "$label konverguje" $res.Converged
            Assert-Close "$label výsledek = vypočteno + oprava" $res.X[$key] ($res.Base[$key] + $corr[$key]) 1e-6
            $next = Invoke-Step $res.Scenario $res.X
            $scale = 1.0; foreach ($k in 'F1', 'F2', 'P', 'T') { $scale = [Math]::Max($scale, [Math]::Abs($res.X[$k])) }
            foreach ($k in 'F1', 'F2', 'P', 'T') {
                if ($k -ne $key) {
                    Assert-True "$label konzistence $k" ([Math]::Abs($next[$k] - $res.X[$k]) -lt 1e-10 * $scale)
                }
            }
            $n0 = 0.0; foreach ($c in $sc.Classes) { $n0 += $c.Pre }; $n0 += $sc.Rc
            Assert-Close "$label NAV" (Get-Nav $res.Scenario $res.X $true $true $true) ($n0 - $res.X.F1 - $res.X.F2 - $res.X.P - $res.X.T) 1e-6
            $corrChecks++
        }
    } } } }
}

# --- Výstup ---------------------------------------------------------------------------------------
"Oprav s pevnou částkou ověřeno: $corrChecks (2 scénáře × 144 kombinací × 4 pravidla)"
"Kombinací: $combos (5 scénářů × 4 × 4 × 3 × 3), ze shody s dnešním pořadím ověřeno: $todayChecked"
"Nejvíc kroků dopočtu: $maxSteps"
"Největší relativní zbytek po dopočtu: $maxResidual"
"Kontrol prošlo: $passed, selhalo: $($failures.Count)"
$closed | Format-Table -AutoSize | Out-String -Width 200
if ($failures.Count) { "SELHÁNÍ:"; $failures | Select-Object -First 40; exit 1 }
