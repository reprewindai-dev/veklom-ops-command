@echo off
setlocal
cd /d "%~dp0..\runner"
if "%VEKLOM_AGENT_API_KEY%%OPENAI_API_KEY%"=="" (echo Set VEKLOM_AGENT_API_KEY or OPENAI_API_KEY.& exit /b 1)
if "%VEKLOM_AGENT_MODEL%"=="" (echo Set VEKLOM_AGENT_MODEL.& exit /b 1)
node runner.mjs
