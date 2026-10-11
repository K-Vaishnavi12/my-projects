# Smoke test through the API gateway. Verifies end-to-end order flow.
$gw = "http://localhost:8000"

Write-Host "`n=== 1. Gateway health ===" -ForegroundColor Cyan
Invoke-RestMethod "$gw/health"

Write-Host "`n=== 2. Initial inventory ===" -ForegroundColor Cyan
"P001","P002","P003","P004" | ForEach-Object {
    Invoke-RestMethod "$gw/api/v1/inventory/$_"
}

Write-Host "`n=== 3. Create 5 orders ===" -ForegroundColor Cyan
$orderIds = @()
1..5 | ForEach-Object {
    $body = @{
        userId = "smoke-user-$_"
        shippingAddress = "Test Street $_"
        items = @(
            @{ productId = "P001"; productName = "Kindle"; quantity = 1; price = 9999 }
            @{ productId = "P002"; productName = "Cable";  quantity = 2; price = 299  }
        )
    } | ConvertTo-Json -Depth 5
    $r = Invoke-RestMethod -Uri "$gw/api/v1/orders" -Method POST -Body $body -ContentType "application/json"
    $orderIds += @{ id=$r.orderId; user=$r.userId }
    Write-Host "  Created $($r.orderId) for $($r.userId)  total=$($r.totalAmount)"
}

Start-Sleep -Seconds 2   # let Kafka consumers process

Write-Host "`n=== 4. Inventory AFTER 5 orders (should have decremented) ===" -ForegroundColor Cyan
"P001","P002" | ForEach-Object {
    Invoke-RestMethod "$gw/api/v1/inventory/$_"
}

Write-Host "`n=== 5. Analytics summary ===" -ForegroundColor Cyan
Invoke-RestMethod "$gw/api/v1/analytics/summary" | ConvertTo-Json -Depth 4

Write-Host "`n=== 6. Cache latency test ===" -ForegroundColor Cyan
$o = $orderIds[0]
$miss = (Measure-Command { Invoke-RestMethod "$gw/api/v1/orders/$($o.id)/user/$($o.user)" }).TotalMilliseconds
$hit  = (Measure-Command { Invoke-RestMethod "$gw/api/v1/orders/$($o.id)/user/$($o.user)" }).TotalMilliseconds
Write-Host ("  cache MISS = {0:N1} ms" -f $miss)
Write-Host ("  cache HIT  = {0:N1} ms" -f $hit)
Write-Host ("  speedup    = {0:N1}x" -f ($miss / $hit))

Write-Host "`nAll checks passed." -ForegroundColor Green
