@echo off
REM Builds all three Spring Boot services in one shot using dockerized Maven.
setlocal
set MAVEN_IMG=maven:3.9.6-eclipse-temurin-11

for %%S in (order-service inventory-service analytics-service) do (
    echo ==========================================
    echo Building %%S
    echo ==========================================
    docker run --rm -v "%cd%\%%S":/app -v "%USERPROFILE%\.m2":/root/.m2 -w /app %MAVEN_IMG% mvn clean package -DskipTests -q
    if errorlevel 1 (
        echo BUILD FAILED for %%S
        exit /b 1
    )
)
echo.
echo All services built successfully.
