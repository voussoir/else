#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

; I don't like any of Windows's provided IME key layouts because they use key
; combinations that I already have mapped.
; vk15 is latin/hangul toggle.
; vk19 is hanja convert.
; AppsKey is the context menu button, so combining it with right alt and ctrl is convenient for me.

>!AppsKey:: sendInput, {vk15}
>^AppsKey:: sendInput, {vk19}
