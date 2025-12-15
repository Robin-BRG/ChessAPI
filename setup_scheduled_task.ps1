# Script pour créer une tâche planifiée Windows
# Lance update_leaderboard.py tous les jours à 6h du matin

$TaskName = "ChessLeaderboardUpdate"
$ScriptPath = "C:\Users\robin\Code\ChessAPI\update_leaderboard.py"
$PythonPath = "py"  # Utilise py launcher

# Supprimer la tâche existante si elle existe
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "⚠️  Tâche existante trouvée, suppression..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Créer l'action (exécuter le script Python)
$Action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "-3 `"$ScriptPath`"" `
    -WorkingDirectory "C:\Users\robin\Code\ChessAPI"

# Créer le trigger (tous les jours à 6h00)
$Trigger = New-ScheduledTaskTrigger -Daily -At "06:00"

# Créer les paramètres
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Créer la tâche
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Met à jour le leaderboard Chess.com quotidiennement" `
    -RunLevel Highest

Write-Host "`n✅ Tâche planifiée créée avec succès!" -ForegroundColor Green
Write-Host "📅 Nom: $TaskName" -ForegroundColor Cyan
Write-Host "⏰ Heure: 6h00 du matin (quotidien)" -ForegroundColor Cyan
Write-Host "📂 Script: $ScriptPath" -ForegroundColor Cyan
Write-Host "`n💡 Pour tester maintenant:" -ForegroundColor Yellow
Write-Host "   Start-ScheduledTask -TaskName `"$TaskName`"" -ForegroundColor White
Write-Host "`n💡 Pour voir les logs:" -ForegroundColor Yellow
Write-Host "   Get-ScheduledTaskInfo -TaskName `"$TaskName`"" -ForegroundColor White
