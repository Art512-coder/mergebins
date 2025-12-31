# Bulk D1 Upload Script - Continue from batch 101
$database = 'bin-search-db'
$startBatch = 101
$endBatch = 917
$totalBatches = $endBatch - $startBatch + 1

Write-Host "Starting bulk D1 upload..." -ForegroundColor Cyan
Write-Host "Uploading batches $startBatch-$endBatch ($totalBatches total batches)" -ForegroundColor Yellow
Write-Host "Estimated time: ~$([math]::Round(($totalBatches * 2) / 60)) minutes" -ForegroundColor Gray
Write-Host ""

$successCount = 0
$failCount = 0
$startTime = Get-Date

for ($i = $startBatch; $i -le $endBatch; $i++) {
    $batchFile = 'migrations/batch_{0:D4}.sql' -f $i
    
    # Progress indicator every 25 batches
    if ($i % 25 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $processed = $i - $startBatch + 1
        $rate = $processed / $elapsed.TotalMinutes
        $remaining = ($endBatch - $i) / $rate
        $progressPct = [math]::Round(($processed / $totalBatches) * 100, 1)
        Write-Host "Progress: $i/$endBatch ($progressPct%) - ETA: $([math]::Round($remaining)) min" -ForegroundColor Blue
    }
    
    # Execute wrangler command
    $null = & wrangler d1 execute $database --file=$batchFile 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $successCount++
        if ($i % 100 -eq 0) {
            Write-Host "Batch $i completed successfully" -ForegroundColor Green
        }
    } else {
        $failCount++
        Write-Host "Batch $i failed" -ForegroundColor Red
        
        # Ask user if they want to continue on error
        $continue = Read-Host "Continue with remaining batches? (y/n)"
        if ($continue -ne 'y') {
            Write-Host "Upload stopped by user at batch $i" -ForegroundColor Yellow
            break
        }
    }
    
    # Small delay to avoid API rate limiting
    Start-Sleep -Milliseconds 50
}

$endTime = Get-Date
$totalTime = $endTime - $startTime

Write-Host ""
Write-Host "Bulk upload completed!" -ForegroundColor Green
Write-Host "Successful: $successCount batches" -ForegroundColor Green
Write-Host "Failed: $failCount batches" -ForegroundColor Red
Write-Host "Total time: $($totalTime.ToString('hh\:mm\:ss'))" -ForegroundColor Blue
Write-Host ""

Write-Host "Verifying final record count..." -ForegroundColor Cyan
& wrangler d1 execute $database --command="SELECT COUNT(*) as total_records FROM bins;"

Write-Host ""
Write-Host "Database statistics:" -ForegroundColor Cyan
& wrangler d1 execute $database --command="SELECT COUNT(DISTINCT brand) as unique_brands, COUNT(DISTINCT country) as unique_countries, COUNT(DISTINCT type) as card_types FROM bins;"
