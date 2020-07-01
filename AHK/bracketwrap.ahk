#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

; Pressing ctrl+[ will surround the currently selected text with square brackets.
; This script was put together quickly so I could get some file renaming done.
; Use at your own risk.

^[::

original_clipboard := ClipboardAll

While(Clipboard := "")
    Sleep 0

Send, ^x
Sleep, 50
ClipWait, 1

SendInput, [
Send, ^v
SendInput, ]

Sleep, 50
ClipBoard := original_clipboard

; This fixes the behavior where the ctrl key is digitally released even though
; you are still holding it down after having pressed ctrl+[.
if GetKeyState("Control")
{
    Send,{CTRLDOWN}
}
else
{
    Send,{CTRLUP}
}

return
