# D1 Database Upload Script
# This script uploads all migration batches to D1

$database = 'bin-search-db'
$totalBatches = 917

Write-Host '🚀 Starting D1 upload process...'
Write-Host "📦 Total batches to upload: $totalBatches"

for ($i = 1; $i -le $totalBatches; $i++) {
    $batchFile = 'migrations/batch_{0:D4}.sql' -f $i
    Write-Host "📤 Uploading batch $i of $totalBatches..."
    
    $result = wrangler d1 execute $database --file=$batchFile 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Batch $i uploaded successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Batch $i failed" -ForegroundColor Red
        Write-Host "Error: $result" -ForegroundColor Red
        break
    }
    
    # Small delay to avoid rate limiting
    Start-Sleep -Milliseconds 500
}

Write-Host '🎉 Upload process completed!'
Write-Host 'Verifying data...'
wrangler d1 execute $database --command="SELECT COUNT(*) as total_records FROM bins;"
