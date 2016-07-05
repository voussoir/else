Tkinter Images
==============

When using Tkinter alone, you can only embed .gif images in your interface. PIL provides a `PhotoImage` class that lets you embed other supported file types.

Requires `pip install pillow`

    import PIL.Image
    import PIL.ImageTk
    import tkinter

    t = tkinter.Tk()
    image = PIL.Image.open('filename.png')
    image_tk = PIL.ImageTk.PhotoImage(image)
    label = tkinter.Label(t, image=image_tk)
    label.image_reference = image_tk
    label.pack()

You must store the `image_tk` somewhere, such as an attribute of the label it belongs to. Otherwise, it gets [prematurely garbage-collected](http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm).

![Screenshot](/../master/.GitImages/quicktips_imagetk.png?raw=true)