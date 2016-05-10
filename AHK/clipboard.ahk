#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

; CTRL+SPACE pastes the clipboard as if it was typed manually.
^SPACE::  SendInput % RegExReplace(Clipboard, "\r\n?|\n\r?", "`n")

