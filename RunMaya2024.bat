@echo off

if NOT "%~1" == "" (
    echo Maya Startup -- override %~1
    set wrk_py=%~1/python;
    set rigging_py=%~1/python/;
    set wrk_mel=%~1/mel;
    set wrk_plugin=%~1/plugins/2022;
    set wrk_icon=%~1/icons;
) else ( echo Maya Startup -- default )

echo Setting maya search paths for py, mel, icons, and plugins
set PYTHONPATH=%rigging_py%;%wrk_py%;y:/github;%PYTHONPATH%
set MAYA_SCRIPT_PATH=%wrk_mel%;%MAYA_SCRIPTS_PATH%
set MAYA_PLUG_IN_PATH=%wrk_plugin%;%MAYA_PLUG_IN_PATH%
set XBMLANGPATH=%wrk_icon%;%XBMLANGPATH%

"C:/Program Files/Autodesk/Maya2024/bin/maya.exe"
