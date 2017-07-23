#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

; Alt-F11, Alt-F12 = sound down and up
!F11::
{
    SoundSet -5
    return
}
!F12::
{
    SoundSet +5
    SoundGet, sound_mute, Master, mute
    if sound_mute = On
    {
        SoundSet, +1, , mute
    }
    return
}
