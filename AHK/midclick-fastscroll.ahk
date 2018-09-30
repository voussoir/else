#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

; Shift-T causes the mousewheel to scroll down.
; I used this to throw lots of dosh in Killing Floor.
MButton::
    While GetKeyState("MButton", "P")
    {
        Click WheelDown
        Sleep 20
    }
Return
