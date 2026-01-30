[Setup]
AppId={{5B680075-8D4C-4315-99A0-2178C9E7B35C}
AppName=소그룹 자동 편성기
AppVersion=3.0.0
AppPublisher=잠실한빛교회 (윤영천 목사)
AppPublisherURL=https://github.com/theplus2/cell-group
AppSupportURL=https://github.com/theplus2/cell-group
AppUpdatesURL=https://github.com/theplus2/cell-group
DefaultDirName={localappdata}\SmallGroupSorter
DisableProgramGroupPage=yes
OutputBaseFilename=SmallGroupSorter_Setup
PrivilegesRequired=lowest
Compression=lzma
SolidCompression=yes
WizardStyle=modern


[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; --onedir 모드로 빌드된 폴더 전체를 포함
Source: "dist\SmallGroupSorter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\Small Group Sorter"; Filename: "{app}\SmallGroupSorter.exe"
Name: "{autodesktop}\Small Group Sorter"; Filename: "{app}\SmallGroupSorter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SmallGroupSorter.exe"; Description: "{cm:LaunchProgram,Small Group Sorter}"; Flags: nowait postinstall skipifsilent
