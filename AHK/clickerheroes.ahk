#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

CoordMode, Mouse, Screen

Clicks(xx, yy)
{
	SendEvent {Click, %xx%, %yy%}
	sleep 80
}

F4::
{
	MsgBox "Stopped"
	Reload
}

F2::
{
	MsgBox "Hold F4 to stop"
	Loop
	{
		Clicks(630, 507) ; fish
		Clicks(856, 450) ; fish
		Clicks(866, 397) ; fish
		Clicks(978, 530) ; fish
		Clicks(1111, 471) ; fish
		Clicks(1159, 460) ; fish
		Clicks(725, 225) ; clicks
		Clicks(725, 275) ; powersurge
		Clicks(725, 328) ; crits
		Clicks(725, 380) ; metal
		Clicks(725, 432) ; goldclicks
		Clicks(725, 485) ; ritual
		Clicks(725, 640) ; reload
		Clicks(725, 584) ; energy
		Clicks(725, 530) ; superclicks
		Clicks(210, 515) ; buyhero
		Clicks(585, 515) ; over...
		Clicks(585, 150) ; up...
		Clicks(820, 150) ; over...
		Loop 180
		{
			; ...and down
			Clicks(820, 240) ; monster
		}
	}
}