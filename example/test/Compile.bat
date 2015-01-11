@echo off

call Cleanup.bat
..\..\bin\twee2sam.exe tw/Simple.txt sam
if errorlevel 1 goto :twee2sam_error

cd sam
call Compile.bat
cd..

goto end

:twee2sam_error

echo twee2sam returned an error
pause

:end