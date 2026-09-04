#define MyAppName "AI PC Diagnosis"
#define MyAppVersion "1.0.3"
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

; PyInstaller縺ｧ菴懈・縺励◆繧｢繝励Μ譛ｬ菴・
Source: "..\dist\AI_PC_Diagnosis\*"; \
    DestDir: "{app}"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

; 蛻晏屓繧､繝ｳ繧ｹ繝医・繝ｫ譎ゅ・縺ｿconfig.ini繧帝・鄂ｮ
; 譌｢蟄倥・邂｡逅・・ｨｭ螳壹・荳頑嶌縺阪＠縺ｪ縺・

; LibreHardwareMonitor
Source: "..\tools\LibreHardwareMonitor\*"; \
    DestDir: "{app}\tools\LibreHardwareMonitor"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

; smartctl
Source: "..\tools\smartctl\*"; \
    DestDir: "{app}\tools\smartctl"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

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

