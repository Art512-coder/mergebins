# Quick script to check current upload progress
Write-Host "Checking current D1 database status..." -ForegroundColor Cyan

try {
    $result = wrangler d1 execute bin-search-db --command="SELECT COUNT(*) as total_records FROM bins;"
    Write-Host $result
    
    # Try to extract the number
    if ($result -match "(\d+)") {
        $count = [int]$matches[1]
        $progress = [math]::Round((($count - 209500) / 248551) * 100, 1)
        $remaining_records = 458051 - $count
        
        Write-Host ""
        Write-Host "Current Records: $count" -ForegroundColor Yellow
        Write-Host "Starting Records: 209,500" -ForegroundColor Gray
        Write-Host "Target Records: 458,051" -ForegroundColor Green
        Write-Host "Progress: $progress% of remaining upload" -ForegroundColor Cyan
        Write-Host "Records Still Needed: $remaining_records" -ForegroundColor Yellow
        
        if ($count -ge 458000) {
            Write-Host "STATUS: TARGET ACHIEVED!" -ForegroundColor Green
        } else {
            Write-Host "STATUS: Upload in progress..." -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "Error checking database status: $_" -ForegroundColor Red
}
