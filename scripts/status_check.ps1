# Simple progress checker for D1 upload
Write-Host "=== D1 Database Upload Progress ===" -ForegroundColor Cyan
Write-Host "Target: 458,051 BIN records"
Write-Host ""

try {
    $result = wrangler d1 execute bin-search-db --command="SELECT COUNT(*) as total_records FROM bins;"
    Write-Host $result
    
    # Simple regex to find any number in the output
    if ($result -match "(\d+)") {
        $count = [int]$matches[1]
        $progress_pct = [math]::Round(($count / 458051) * 100, 2)
        $remaining = 458051 - $count
        
        Write-Host ""
        Write-Host "Current Records: $count" -ForegroundColor Yellow
        Write-Host "Progress: $progress_pct%" -ForegroundColor Cyan
        Write-Host "Records Remaining: $remaining" -ForegroundColor Yellow
        
        if ($count -ge 458000) {
            Write-Host ""
            Write-Host "TARGET ACHIEVED!" -ForegroundColor Green
            Write-Host "You now have the largest free BIN database in the world!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "Status: Upload in progress..." -ForegroundColor Yellow
            
            # Estimate batches completed  
            $batches_done = [math]::Floor($count / 500)
            $batches_remaining = 917 - $batches_done
            Write-Host "Estimated batches completed: ~$batches_done/917" -ForegroundColor Gray
            Write-Host "Estimated batches remaining: ~$batches_remaining" -ForegroundColor Gray
        }
    } else {
        Write-Host "Could not find record count in result" -ForegroundColor Red
    }
} catch {
    Write-Host "Error checking database: $($_.Exception.Message)" -ForegroundColor Red
}
