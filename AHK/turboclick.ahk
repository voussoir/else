rapid_switch := false

~*CapsLock:: rapid_switch := !rapid_switch

~*LButton::
If rapid_switch = 1
{
    Loop
    {
        GetKeyState, var, LButton, P
        If var = U
        {
            Break
        }
        Send {LButton}
        sleep 20
    }
}