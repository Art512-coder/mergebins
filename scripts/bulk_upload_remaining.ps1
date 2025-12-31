# Bulk D1 Upload Script - Continue from batch 101
$database = 'bin-search-db'
$startBatch = 101
$endBatch = 917
$totalBatches = $endBatch - $startBatch + 1

Write-Host "🚀 Starting bulk D1 upload..." -ForegroundColor Cyan
Write-Host "📦 Uploading batches $startBatch-$endBatch ($totalBatches batches)" -ForegroundColor Yellow
Write-Host "⏱️ Estimated time: ~$(($totalBatches * 2) / 60) minutes" -ForegroundColor Gray
Write-Host ""

$successCount = 0
$failCount = 0
$startTime = Get-Date

for ($i = $startBatch; $i -le $endBatch; $i++) {
    $batchFile = 'migrations/batch_{0:D4}.sql' -f $i
    
    # Progress indicator every 10 batches
    if ($i % 10 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $rate = ($i - $startBatch + 1) / $elapsed.TotalMinutes
        $remaining = ($endBatch - $i) / $rate
        Write-Host "📊 Progress: $i/$endBatch ($(($i-$startBatch+1)/$totalBatches*100 | % {$_.ToString('F1')})%) - ETA: $([math]::Round($remaining)) min" -ForegroundColor Blue
    }
    
    # Execute wrangler command and capture result
    $result = & wrangler d1 execute $database --file=$batchFile 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $successCount++
        if ($i % 50 -eq 0) {
            Write-Host "✅ Batch $i completed successfully" -ForegroundColor Green
        }
    } else {
        $failCount++
        Write-Host "❌ Batch $i failed: $result" -ForegroundColor Red
        
        # Ask user if they want to continue on error
        $continue = Read-Host "Continue with remaining batches? (y/n)"
        if ($continue -ne 'y') {
            break
        }
    }
    
    # Small delay to avoid overwhelming the API
    Start-Sleep -Milliseconds 100
}

$endTime = Get-Date
$totalTime = $endTime - $startTime

Write-Host ""
Write-Host "🎉 Bulk upload completed!" -ForegroundColor Green
Write-Host "✅ Successful: $successCount batches" -ForegroundColor Green
Write-Host "❌ Failed: $failCount batches" -ForegroundColor Red
Write-Host "⏱️ Total time: $($totalTime.ToString('hh\:mm\:ss'))" -ForegroundColor Blue
Write-Host ""

Write-Host "🔍 Verifying final record count..." -ForegroundColor Cyan
& wrangler d1 execute $database --command="SELECT COUNT(*) as total_records FROM bins;"

Write-Host ""
Write-Host "📊 Database statistics:" -ForegroundColor Cyan
& wrangler d1 execute $database --command="SELECT COUNT(DISTINCT brand) as unique_brands, COUNT(DISTINCT country) as unique_countries, COUNT(DISTINCT type) as card_types FROM bins;"
