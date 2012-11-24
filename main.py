from tkinter import *
from tkinter import filedialog as dialog
from PIL import Image, ImageTk


def main():
    root = Tk()
    root.title("Pixelizer")

    cw, ch = imw, imh = 640, 400
    pil_img = Image.open("Elephant.png")
    pil_img = pil_img.resize((imw, imh), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(pil_img)

    c = Canvas(root, width=cw, height=ch)
    c.image = c.create_image((imw/2,imh/2), image=img) # keep tkinter from garbage collecting the photo
    c.grid(row=0, column=0, rowspan=4, sticky=N)


    load = Button(root, text="Load Image", command=dialog.askopenfilename).grid(row=0, column=1, sticky=E)
    save = Button(root, text="Save Image", command=dialog.asksaveasfilename).grid(row=0, column=2, sticky=W)

    size = Spinbox(root, from_=0, to=10).grid(row=1, column=1, columnspan=2)
    run  = Button(root, text="Pixelize Image").grid(row=2, column=1, columnspan=2)

    root.mainloop()


if __name__ == '__main__': main()
