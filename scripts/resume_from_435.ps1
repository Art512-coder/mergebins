# Resume D1 bulk upload from batch 435 to complete 458K records
param(
    [int]$StartBatch = 435,
    [int]$EndBatch = 917
)

Write-Host "Resuming D1 bulk upload from batch $StartBatch..." -ForegroundColor Green
$remaining = $EndBatch - $StartBatch + 1
Write-Host "Uploading batches $StartBatch to $EndBatch ($remaining remaining batches)"
Write-Host "Expected new records: ~$($remaining * 500 - 449) (batch 917 has only 51 records)" -ForegroundColor Yellow
Write-Host "Estimated time: ~$(([math]::Ceiling($remaining / 25) * 2)) minutes" -ForegroundColor Green
Write-Host ""

$processed = 0
$errors = 0

for ($i = $StartBatch; $i -le $EndBatch; $i++) {
    $batchFile = "migrations\batch_{0:D4}.sql" -f $i
    
    if (Test-Path $batchFile) {
        try {
            wrangler d1 execute bin-search-db --file="$batchFile" | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $processed++
            } else {
                Write-Host "Error uploading batch $i" -ForegroundColor Red
                $errors++
            }
            
            # Progress update every 25 batches
            if ($i % 25 -eq 0 -or $i -eq $EndBatch) {
                $progressPct = [math]::Round((($i - $StartBatch + 1) / $remaining) * 100, 1)
                $remainingBatches = $EndBatch - $i
                $etaMinutes = [math]::Ceiling($remainingBatches / 25) * 2
                Write-Host "Progress: $i/$EndBatch ($progressPct%) - ETA: $etaMinutes min - Processed: $processed" -ForegroundColor Cyan
            }
            
        } catch {
            Write-Host "Error uploading batch $i - $_" -ForegroundColor Red
            $errors++
        }
    } else {
        Write-Host "Warning: Batch file $batchFile not found" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Upload completed! Processed $processed batches with $errors errors." -ForegroundColor Green
Write-Host "Verifying final record count..." -ForegroundColor Cyan

# Final verification
try {
    $result = wrangler d1 execute bin-search-db --command="SELECT COUNT(*) as total_records FROM bins;"
    Write-Host $result
    
    if ($result -match "(\d+)") {
        $count = [int]$matches[1]
        Write-Host ""
        Write-Host "Final record count: $count" -ForegroundColor Green
        
        if ($count -ge 458000) {
            Write-Host "SUCCESS: Target of 458K+ records achieved!" -ForegroundColor Green
            Write-Host "You now have the largest free database of BINs in the world!" -ForegroundColor Green
        } else {
            $needed = 458051 - $count
            Write-Host "Still need $needed more records to reach 458,051 target" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "Could not verify final count - please check manually" -ForegroundColor Yellow
}
