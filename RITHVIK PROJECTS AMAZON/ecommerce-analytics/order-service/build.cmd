@echo off
REM Run Maven inside Docker - no need to install Maven locally!
REM Usage: build.cmd [maven-args]
REM Example: build.cmd clean package -DskipTests

docker run -it --rm ^
  -v "%cd%":/app ^
  -v "%USERPROFILE%\.m2":/root/.m2 ^
  -w /app ^
  maven:3.9.6-eclipse-temurin-11 ^
  mvn %*
