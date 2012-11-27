from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import Image, ImageTk
import PIL.ImageFilter as Filter
from pixelize import pixelize_squares as pixelize

def load_image():
    fname = askopenfilename()
    if fname: 
        return Image.open(fname)

def save_image():
    fname = asksaveasfilename()
    if fname: 
        return 

def resize_image(img, w, h):
    return img.resize((w, h), Image.ANTIALIAS)

def draw_ui():
    root = Tk()
    root.title("Pixelizer")

    root.b_load = Button(root, text="Load", command=load_image)
    root.b_save = Button(root, text="Save", command=save_image)
    root.b_size = Spinbox(root, from_=1, to=20, width=8, textvariable=10)
    root.b_pbtn = Button(root, text="Pixelize Image", command=pixelize)
    root.b_load.grid(row=0, column=1, sticky=E)    
    root.b_save.grid(row=0, column=2, sticky=W)
    root.b_size.grid(row=3, column=1, columnspan=2, sticky=S)
    root.b_pbtn.grid(row=4, column=1, columnspan=2, sticky=N)

    root.b_size.insert(0,1) # Make the initial value 11 ('1'+'1')

    return root

def pixelize_filter(img, psize):
    im1 = img.filter(Filter.ModeFilter)
    print(im1)
    return im1

def main():
    root = draw_ui()
    pixel_size = int(root.b_size.get())

    pil_img = load_image()
    # w, h = 640, 400
    o = w, h = pil_img.size
    if (w > 640) or (h > 400):
        while w > 640:
            w = w // 2
        # original width / (width/height ratio) = 
        h = w / (o[0] / o[1])
        pil_img = resize_image(pil_img, w, int(h))

    img = ImageTk.PhotoImage(pil_img)
    c = Canvas(root, width=w, height=h)
    c.image = c.create_image((w/2, h/2), image=img) # keep tkinter from garbage collecting the photo
    c.grid(row=0, column=0, rowspan=8, sticky=N)

    # pixelize(pil_img, pixel_size, c)
    pixelize_filter(pil_img, pixel_size)

    root.mainloop() # Run the window


if __name__ == '__main__': main()
