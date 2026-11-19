# Referenční model společného dopočtu úplat, výkonnostní odměny a daně (návrh 2026-11-18, otázky 1–5).
# Nezávislý na kódu Odoo; slouží jako zdroj očekávaných hodnot pro budoucí testy v investra_nav.
#
# Zjednodušení: jedno období (bez krystalizace a více ocenění), měřítko výkonnosti = kapitál třídy,
# HWM = zadaná hodnota, bez příjemců úplat. Pravidla:
#   F1 = časově rozlišená úplata celého fondu ze základu FK          (stav S0..S3)
#   F2 = časově rozlišená úplata třídy A ze základu kapitál třídy A  (stav S0..S3)
#   P  = výkonnostní odměna třídy A                                  (stav S0, S1, S3)
#   T  = očekávaná daň fondu; stav = které náklady snižují základ   (S0, S1, S2)
# Stavy: S0 před úplatami, S1 po úplatách (vč. sebe), S2 po odměně, S3 po dani (= výsledný FK).
# Daňový efekt položek třídy patří třídě (otázka 3): přesun e × (spec_c − ρ_c × Σspec), e = efektivní sazba.

function New-Amounts([double]$f1, [double]$f2, [double]$p, [double]$t) {
    return @{ F1 = $f1; F2 = $f2; P = $p; T = $t }
}

function Get-Ratio($sc, $code) {
    $total = 0.0
    foreach ($c in $sc.Classes) { $total += $c.Pre }
    foreach ($c in $sc.Classes) { if ($c.Code -eq $code) { return $c.Pre / $total } }
    throw "Třída $code neexistuje"
}

# Odpočitatelné náklady podle stavu daně: S0 nic, S1 úplaty, S2 úplaty a odměna.
function Get-TaxDeductions($x, [int]$st) {
    $fund = 0.0; $specA = 0.0
    if ($st -ge 1) { $fund += $x.F1; $specA += $x.F2 }
    if ($st -ge 2) { $specA += $x.P }
    return @{ Fund = $fund; SpecA = $specA }
}

function Get-TaxTotal($sc, $x, [int]$st) {
    $ded = Get-TaxDeductions $x $st
    $base = $sc.Rc - $ded.Fund - $ded.SpecA
    return $sc.t * [Math]::Max(0.0, $base)
}

# Rozdělení daně x.T mezi třídy: poměrem + přesun daňového efektu specifických položek (otázka 3).
function Get-TaxSplit($sc, $x, [int]$st) {
    $ded = Get-TaxDeductions $x $st
    $base = $sc.Rc - $ded.Fund - $ded.SpecA
    $spec = $ded.SpecA
    $e = 0.0
    if ([Math]::Abs($spec) -gt 1e-12) {
        $withoutSpec = $sc.t * [Math]::Max(0.0, $base + $spec)
        $withSpec = $sc.t * [Math]::Max(0.0, $base)
        $e = ($withoutSpec - $withSpec) / $spec
    }
    $split = @{}
    foreach ($c in $sc.Classes) {
        $rho = Get-Ratio $sc $c.Code
        $specC = 0.0
        if ($c.Code -eq 'A') { $specC = $spec }
        $split[$c.Code] = $rho * $x.T - $e * ($specC - $rho * $spec)
    }
    return $split
}

# Hodnota třídy ve stavu, který zahrnuje vybrané vrstvy (úplaty, odměnu, daň).
function Get-ClassValue($sc, $x, $code, [bool]$fees, [bool]$perf, [bool]$tax) {
    $c = $sc.Classes | Where-Object { $_.Code -eq $code }
    $rho = Get-Ratio $sc $code
    $v = $c.Pre + $rho * $sc.Rc
    if ($fees) { $v -= $rho * $x.F1; if ($code -eq 'A') { $v -= $x.F2 } }
    if ($perf -and $code -eq 'A') { $v -= $x.P }
    if ($tax) { $v -= (Get-TaxSplit $sc $x $sc.st)[$code] }
    return $v
}

function Get-Nav($sc, $x, [bool]$fees, [bool]$perf, [bool]$tax) {
    $n = 0.0
    foreach ($c in $sc.Classes) { $n += Get-ClassValue $sc $x $c.Code $fees $perf $tax }
    return $n
}

function Get-StageFlags([int]$stage) {
    # S0 nic, S1 úplaty, S2 úplaty + odměna, S3 úplaty + odměna + daň
    return @{ Fees = ($stage -ge 1); Perf = ($stage -ge 2); Tax = ($stage -ge 3) }
}

# Jeden krok dopočtu: každé pravidlo z aktuálních částek.
function Invoke-Step($sc, $x) {
    $g1 = Get-StageFlags $sc.s1
    $g2 = Get-StageFlags $sc.s2
    $f1 = $sc.f1 * (Get-Nav $sc $x $g1.Fees $g1.Perf $g1.Tax)
    $f2 = $sc.f2 * (Get-ClassValue $sc $x 'A' $g2.Fees $g2.Perf $g2.Tax)
    $p = 0.0
    if ($sc.r -gt 0) {
        # Odměna nikdy po sobě samé: S0 nic, S1 úplaty, S3 úplaty + daň
        $value = Get-ClassValue $sc $x 'A' ($sc.sp -ge 1) $false ($sc.sp -ge 3)
        $p = $sc.r * [Math]::Max(0.0, $value - $sc.HwmA)
    }
    $t = Get-TaxTotal $sc $x $sc.st
    $result = New-Amounts $f1 $f2 $p $t
    # Otázka 12: opravené pravidlo má pevnou výslednou částku (vypočteno bez opravy + oprava).
    if ($sc.Pinned) { foreach ($k in $sc.Pinned.Keys) { $result[$k] = $sc.Pinned[$k] } }
    return $result
}

# Dva průchody: bez oprav (= „Vypočteno“), pak s pevnými částkami opravených pravidel.
function Invoke-SolveWithCorrections($sc, $corrections) {
    $plain = $sc.Clone(); $plain.Pinned = $null
    $base = Invoke-Solve $plain (New-Amounts 0 0 0 0)
    $pinned = $sc.Clone(); $pinned.Pinned = @{}
    foreach ($k in $corrections.Keys) { $pinned.Pinned[$k] = $base.X[$k] + $corrections[$k] }
    $solved = Invoke-Solve $pinned (New-Amounts 0 0 0 0)
    return @{ Base = $base.X; X = $solved.X; Converged = ($base.Converged -and $solved.Converged); Scenario = $pinned }
}

function Get-Distance($a, $b) {
    $d = 0.0
    foreach ($k in 'F1', 'F2', 'P', 'T') { $d = [Math]::Max($d, [Math]::Abs($a[$k] - $b[$k])) }
    return $d
}

# Tolerance je relativní k velikosti částek (1e-12 × max(1, největší částka)): absolutní 1e-10 je u částek
# ve statisících na hranici přesnosti double a krok se pak „chvěje“ v posledních bitech.
function Invoke-Solve($sc, $start, [int]$maxSteps = 500, [double]$relTol = 1e-12) {
    $x = $start
    $last = [double]::PositiveInfinity
    for ($i = 1; $i -le $maxSteps; $i++) {
        $next = Invoke-Step $sc $x
        $scale = 1.0
        foreach ($k in 'F1', 'F2', 'P', 'T') { $scale = [Math]::Max($scale, [Math]::Abs($next[$k])) }
        $last = Get-Distance $next $x
        if ($last -lt $relTol * $scale) { return @{ X = $next; Steps = $i; Converged = $true; Last = $last } }
        $x = $next
    }
    return @{ X = $x; Steps = $maxSteps; Converged = $false; Last = $last }
}

# Dnešní postup (pevné pořadí) pro kombinace, které jde dnes nastavit: úplaty S0/S1, odměna S0/S1, daň S2.
# Úplaty S1 se řeší soustavou dvou lineárních rovnic (Cramer), nezávisle na iteraci modelu.
function Invoke-Today($sc) {
    $rhoA = Get-Ratio $sc 'A'
    $n0 = 0.0; foreach ($c in $sc.Classes) { $n0 += $c.Pre }; $n0 += $sc.Rc
    $a0 = ($sc.Classes | Where-Object { $_.Code -eq 'A' }).Pre + $rhoA * $sc.Rc
    # F1 = f1 * (n0 - [s1] (F1 + F2)),  F2 = f2 * (a0 - [s2] (rhoA F1 + F2))
    $k1 = [double]($sc.s1 -eq 1); $k2 = [double]($sc.s2 -eq 1)
    $m11 = 1 + $sc.f1 * $k1; $m12 = $sc.f1 * $k1
    $m21 = $sc.f2 * $k2 * $rhoA; $m22 = 1 + $sc.f2 * $k2
    $b1 = $sc.f1 * $n0; $b2 = $sc.f2 * $a0
    $det = $m11 * $m22 - $m12 * $m21
    $f1 = ($b1 * $m22 - $m12 * $b2) / $det
    $f2 = ($m11 * $b2 - $m21 * $b1) / $det
    $p = 0.0
    if ($sc.r -gt 0) {
        $value = $a0
        if ($sc.sp -eq 1) { $value -= $rhoA * $f1 + $f2 }
        $p = $sc.r * [Math]::Max(0.0, $value - $sc.HwmA)
    }
    $t = $sc.t * [Math]::Max(0.0, $sc.Rc - $f1 - $f2 - $p)
    return New-Amounts $f1 $f2 $p $t
}
