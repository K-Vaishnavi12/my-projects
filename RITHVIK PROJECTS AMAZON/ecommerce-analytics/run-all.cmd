@echo off
REM Starts all three microservices in the background using Java.
REM Assumes build-all.cmd has already produced the JARs.

setlocal
set JAVA_OPTS=-Xms256m -Xmx512m

start "order-service"     cmd /c java %JAVA_OPTS% -jar order-service\target\order-service-1.0.0.jar     ^> order-service\app.log 2^>^&1
start "inventory-service" cmd /c java %JAVA_OPTS% -jar inventory-service\target\inventory-service-1.0.0.jar ^> inventory-service\app.log 2^>^&1
start "analytics-service" cmd /c java %JAVA_OPTS% -jar analytics-service\target\analytics-service-1.0.0.jar ^> analytics-service\app.log 2^>^&1

echo Started 3 services in background windows.
echo   order-service      : http://localhost:8081
echo   inventory-service  : http://localhost:8082
echo   analytics-service  : http://localhost:8083
echo   API gateway        : http://localhost:8000
echo   Kafka UI           : http://localhost:8090
echo   Prometheus         : http://localhost:9090
echo   Grafana            : http://localhost:3000
