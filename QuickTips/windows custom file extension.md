Custom file extensions on Windows
=================================

In this tutorial I will create a file extension, `.vtxt` that opens in Notepad.

Note: If certain things are not taking effect right away, you may need to restart explorer.exe through the task manager.

1. Open regedit.exe to HKEY_CLASSES_ROOT
2. Right click on HKEY_CLASSES_ROOT and create a new key. I'll refer to this as the "ProgID key".

    ![Screenshot](/../master/.GitImages/quicktips_extension_create.png?raw=true)

3. Name it according to the ProgID standards outlined here: [Programmatic Identifiers - MSDN](https://msdn.microsoft.com/en-us/library/windows/desktop/cc144152(v=vs.85).aspx)

    >The proper format of a ProgID key name is [*Vendor or Application*].[*Component*].[*Version*], separated by periods and with no spaces, as in `Word.Document.6`

    I will call mine `voussoir.vtxt`

4. Right click on HKCR and create another new key, and name it after your extension. For mine, it's `.vtxt`. I'll refer to this as the "Extension key".
5. On your extension key, double-click the `(Default)` value, and enter the name of your ProgID.

    ![Screenshot](/../master/.GitImages/quicktips_extension_extkey.png?raw=true)

6. On your ProgID key, set the `(Default)` value to a description of your file type. This is what you'll see when you hover over the file, or view the Properties dialog of your filetype. According to the MSDN ProgID article, you should also create a value `FriendlyTypeName` with the exact same text.

    ![Screenshot](/../master/.GitImages/quicktips_extension_description.png?raw=true)

7. On your ProgID key, create a subkey `DefaultIcon`, and set its `(Default)` value to the filepath of a .ico file, and specify the icon's index within that file. For example: `C:\mystuff\myextension.ico,0`. My file is `C:\vtxt.ico`. It only contains one image, so I'll use the index 0.

    ![Screenshot](/../master/.GitImages/quicktips_extension_icon.png?raw=true)

8. Lastly, it's time to associate the extension with a program. On your ProgID key, create subkeys `shell\open\command`.

9. On the `open` subkey, you can set the `(Default)` value to be a caption that appears on the context menu to open the file. If you don't, it will just say "Open".

    ![Screenshot](/../master/.GitImages/quicktips_extension_caption.png?raw=true)

10. On the `command` subkey, set the `(Default)` value to a command to launch your file. This can be complex, so for a basic solution, just use something like `notepad.exe "%L"`, where %L will become the filename of your file, so notepad knows what to open. Some more info can be found [here on superuser.com](http://superuser.com/a/473602).

11. Try opening your file!

    ![Screenshot](/../master/.GitImages/quicktips_extension_command.png?raw=true)

That should give you the basics. The MSDN articles go into more detail about the other values your ProgID can have.

You can save this as a `.reg` file if you want:

    Windows Registry Editor Version 5.00

    [HKEY_CLASSES_ROOT\.vtxt]
    @="voussoir.vtxt"


    [HKEY_CLASSES_ROOT\voussoir.vtxt]
    @="voussoir's text type"
    "FriendlyTypeName"="voussoir's text type"


    [HKEY_CLASSES_ROOT\voussoir.vtxt\DefaultIcon]
    @="C:\\vtxt.ico,0"


    [HKEY_CLASSES_ROOT\voussoir.vtxt\shell]


    [HKEY_CLASSES_ROOT\voussoir.vtxt\shell\open]
    @="Let 'er rip"


    [HKEY_CLASSES_ROOT\voussoir.vtxt\shell\open\command]
    @="notepad.exe \"%L\""
