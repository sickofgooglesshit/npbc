git clone https://github.com/eccentricOrange/npbc.git "%userprofile%\npbc"

if exist "%userprofile%\.npbc" (
    echo "Not updating user directory."
) else (
    xcopy /s "%userprofile%\npbc\data %userprofile%\.npbc"
)

setx path "%PATH%;%userprofile%\npbc\bin"