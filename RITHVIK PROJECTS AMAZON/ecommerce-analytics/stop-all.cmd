@echo off
REM Kill all Java service processes (matches only order/inventory/analytics-service JARs)
for /f "tokens=2" %%p in ('wmic process where "commandline like '%%order-service-1.0.0.jar%%' or commandline like '%%inventory-service-1.0.0.jar%%' or commandline like '%%analytics-service-1.0.0.jar%%'" get processid ^| findstr [0-9]') do (
    echo Killing PID %%p
    taskkill /F /PID %%p >nul 2>&1
)
echo All services stopped.
