#define MyAppName "AI PC Diagnosis"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "AI PC Diagnosis"

[Setup]

AppId={{7F4E16D2-9B68-4B39-A18D-4C7D1B3E8A52}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\AI_PC_Diagnosis
DefaultGroupName=AI PC Diagnosis

OutputDir=.\output
OutputBaseFilename=AI_PC_Diagnosis_Setup_{#MyAppVersion}

Compression=lzma
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Files]

; PyInstallerで作成したアプリ本体
Source: "..\dist\AI_PC_Diagnosis\*"; \
    DestDir: "{app}"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

; 初回インストール時のみconfig.iniを配置
; 既存の管理者設定は上書きしない
Source: "..\config.ini"; \
    DestDir: "{commonappdata}\AI_PC_Diagnosis"; \
    Flags: onlyifdoesntexist uninsneveruninstall

[Dirs]

Name: "{commonappdata}\AI_PC_Diagnosis"
Name: "{commonappdata}\AI_PC_Diagnosis\reports"
Name: "{commonappdata}\AI_PC_Diagnosis\logs"
Name: "{commonappdata}\AI_PC_Diagnosis\logs\diagnosis"

[Icons]

Name: "{group}\AI PC Diagnosis"; \
    Filename: "{app}\AI_PC_Diagnosis.exe"; \
    WorkingDir: "{app}"

Name: "{autodesktop}\AI PC Diagnosis"; \
    Filename: "{app}\AI_PC_Diagnosis.exe"; \
    WorkingDir: "{app}"