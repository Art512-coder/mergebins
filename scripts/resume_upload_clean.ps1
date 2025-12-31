# Resume D1 Bulk Upload - Batches 266-917
# This will complete the upload to reach 458K+ records

$startBatch = 266
$endBatch = 917
$totalBatches = $endBatch - $startBatch + 1

Write-Host "Starting D1 bulk upload resume..." -ForegroundColor Yellow
Write-Host "Uploading batches $startBatch to $endBatch ($totalBatches remaining batches)" -ForegroundColor Cyan
Write-Host "Estimated time: ~$([math]::Ceiling($totalBatches * 2 / 60)) minutes" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failedBatches = @()
$startTime = Get-Date

for ($i = $startBatch; $i -le $endBatch; $i++) {
    $batchFile = "migrations/batch_{0:D4}.sql" -f $i
    
    if (-not (Test-Path $batchFile)) {
        Write-Host "ERROR: Batch file $batchFile not found" -ForegroundColor Red
        $failedBatches += $i
        continue
    }
    
    try {
        $result = wrangler d1 execute bin-search-db --file=$batchFile 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $successCount++
            
            # Progress updates every 25 batches
            if ($i % 25 -eq 0) {
                $elapsed = (Get-Date) - $startTime
                $progress = (($i - $startBatch + 1) / $totalBatches) * 100
                $eta = $elapsed.TotalMinutes * (100 / $progress) - $elapsed.TotalMinutes
                Write-Host "Progress: $i/$endBatch ($([math]::Round($progress, 1))pct) - ETA: $([math]::Round($eta)) min" -ForegroundColor Green
            }
        } else {
            Write-Host "ERROR: Batch $i failed: $result" -ForegroundColor Red
            $failedBatches += $i
        }
    } catch {
        Write-Host "ERROR: Batch $i exception: $($_.Exception.Message)" -ForegroundColor Red
        $failedBatches += $i
    }
    
    # Small delay to avoid overwhelming the service
    Start-Sleep -Milliseconds 100
}

$endTime = Get-Date
$totalTime = ($endTime - $startTime).TotalMinutes

Write-Host ""
Write-Host "Upload completion summary:" -ForegroundColor Yellow
Write-Host "Successful batches: $successCount" -ForegroundColor Green
Write-Host "Failed batches: $($failedBatches.Count)" -ForegroundColor Red
Write-Host "Total time: $([math]::Round($totalTime, 1)) minutes" -ForegroundColor Cyan

if ($failedBatches.Count -gt 0) {
    Write-Host "Failed batch numbers: $($failedBatches -join ', ')" -ForegroundColor Red
}

Write-Host ""
Write-Host "Verifying final record count..." -ForegroundColor Yellow
wrangler d1 execute bin-search-db --command="SELECT COUNT(*) as total_records FROM bins;"

Write-Host ""
Write-Host "Target: 458,052 records" -ForegroundColor Cyan
Write-Host "Upload resumed from batch $startBatch to $endBatch" -ForegroundColor Cyan
