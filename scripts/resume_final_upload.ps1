# Resume D1 bulk upload from batch 420 to complete 458K records
param(
    [int]$StartBatch = 420,
    [int]$EndBatch = 917
)

Write-Host "Starting D1 bulk upload resume from batch $StartBatch..."
$remaining = $EndBatch - $StartBatch + 1
Write-Host "Uploading batches $StartBatch to $EndBatch ($remaining remaining batches)"
Write-Host "Estimated time: ~$(([math]::Ceiling($remaining / 25) * 2)) minutes" -ForegroundColor Green
Write-Host ""

$totalBatches = 917
$processed = 0

for ($i = $StartBatch; $i -le $EndBatch; $i++) {
    $batchFile = "batch_migrations\batch_{0:D4}.sql" -f $i
    
    if (Test-Path $batchFile) {
        try {
            wrangler d1 execute bin-search-db --file="$batchFile" 2>$null
            $processed++
            
            # Progress update every 25 batches
            if ($i % 25 -eq 0 -or $i -eq $EndBatch) {
                $progressPct = [math]::Round((($i - $StartBatch + 1) / $remaining) * 100, 1)
                $remainingBatches = $EndBatch - $i
                $etaMinutes = [math]::Ceiling($remainingBatches / 25) * 2
                Write-Host "Progress: $i/$EndBatch ($progressPct%) - ETA: $etaMinutes min" -ForegroundColor Yellow
            }
            
        } catch {
            Write-Host "Error uploading batch $i - $_" -ForegroundColor Red
            # Continue with next batch
        }
    } else {
        Write-Host "Warning: Batch file $batchFile not found" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Upload completed! Processed $processed batches." -ForegroundColor Green
Write-Host "Verifying final record count..." -ForegroundColor Cyan

# Final verification
try {
    $result = wrangler d1 execute bin-search-db --command="SELECT COUNT(*) as total_records FROM bins;" --json 2>$null
    if ($result) {
        $count = ($result | ConvertFrom-Json)[0].results[0].total_records
        Write-Host "Final record count: $count" -ForegroundColor Green
        
        if ($count -ge 458000) {
            Write-Host "SUCCESS: Target of 458K+ records achieved!" -ForegroundColor Green
        } else {
            Write-Host "Note: Still need $([math]::Max(0, 458052 - $count)) more records to reach 458K target" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "Could not verify final count - please check manually" -ForegroundColor Yellow
}
