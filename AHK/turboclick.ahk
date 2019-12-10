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

~*RButton::
If rapid_switch = 1
{
    Loop
    {
        GetKeyState, var, RButton, P
        If var = U
        {
            Break
        }
        Send {RButton}
        sleep 20
    }
}