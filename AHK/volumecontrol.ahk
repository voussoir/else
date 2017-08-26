#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

; Alt-F11, Alt-F12 = sound down and up
; WINDOWS 7 USERS: You need
; `Send {Volume_Up}` instead of `SoundSet +5` and
; `Send {Volume_Down}` instead of `SoundSet -5`.
; The `SoundSet, +1, , mute` will still work okay.

vol_down(amount)
{
    SoundSet -%amount%
    return
}

vol_up(amount)
{
    SoundSet +%amount%
    SoundGet, sound_mute, Master, mute
    if sound_mute = On
    {
        SoundSet, +0, , mute
    }
    return
}

!F11::
{
    vol_down(5)
    return
}
+!F11::
{
    vol_down(1)
    return
}

!F12::
{
    vol_up(5)
    return
}
+!F12::
{
    vol_up(1)
    return
}
