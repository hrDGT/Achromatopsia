[Setup]
AppName=Achromatopsia
AppVersion=1.0
DefaultDirName={autopf}\Achromatopsia
DefaultGroupName=Achromatopsia
OutputDir=output
OutputBaseFilename=Achromatopsia_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=assets\icon.ico

[Files]
Source: "dist\Achromatopsia.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "scenes\*"; DestDir: "{app}\scenes"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\Achromatopsia"; Filename: "{app}\Achromatopsia.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{autoprograms}\Achromatopsia"; Filename: "{app}\Achromatopsia.exe"; IconFilename: "{app}\assets\icon.ico"

[Run]
Filename: "{app}\Achromatopsia.exe"; Description: "Запустить Achromatopsia"; Flags: postinstall nowait skipifsilent