# Resume D1 upload from batch 456 to complete the final 458K target
param(
    [int]$StartBatch = 456,
    [int]$EndBatch = 917
)

Write-Host "Resuming D1 upload from batch $StartBatch to $EndBatch" -ForegroundColor Green
$remaining = $EndBatch - $StartBatch + 1
Write-Host "Batches to upload: $remaining" -ForegroundColor Yellow
Write-Host "Expected records to add: ~$(($remaining * 500) - 449)" -ForegroundColor Cyan
Write-Host "Estimated time: ~$(([math]::Ceiling($remaining / 25) * 2)) minutes"
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
                $errors++
            }
            
            # Progress every 25 batches
            if ($i % 25 -eq 0 -or $i -eq $EndBatch) {
                $progressPct = [math]::Round((($i - $StartBatch + 1) / $remaining) * 100, 1)
                $eta = [math]::Ceiling(($EndBatch - $i) / 25) * 2
                Write-Host "Progress: $i/$EndBatch ($progressPct%) - ETA: $eta min" -ForegroundColor Cyan
            }
            
        } catch {
            $errors++
        }
    }
}

Write-Host ""
Write-Host "Upload batch completed! Processed: $processed, Errors: $errors" -ForegroundColor Green

# Check final count
try {
    Write-Host "Checking final record count..." -ForegroundColor Cyan
    wrangler d1 execute bin-search-db --command="SELECT COUNT(*) as total_records FROM bins;"
} catch {
    Write-Host "Could not verify count" -ForegroundColor Yellow
}
