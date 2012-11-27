from random import randrange
from PIL import Image

def color_rgb(r,g,b): return "#%02x%02x%02x" % (r,g,b)
def colorize():       return color_rgb(randrange(256), randrange(256), randrange(256))

def resize(img, box, fit):
    """Downsample the image.
    @param img: Image - an Image object
    @param box: tuple(x, y) - the bounding box of the result image
    @param fit: boolean - crop the image to fill the box
    
    Code based on http://unitedcoders.com/christian-harms/image-resizing-tips-general-and-for-python
    """

    # preresize image with factor 2, 4, 8, and fast algorithm
    factor = 1

    while img.size[0]/factor > 2*box[0] and img.size[1]*2/factor > 2*box[1]:
        factor *= 2

    if factor > 1:
        img.thumbnail((img.size[0]/factor, img.size[1]/factor), Image.NEAREST)

    # calculate the cropping box and get the cropped part
    if fit:
        x1 = y1 = 0
        x2, y2 = img.size
        wRatio = 1.0 * x2/box[0]
        hRatio = 1.0 * y2/box[1]
        if hRatio > wRatio:
            y1 = int(y2/2-box[1]*wRatio/2)
            y2 = int(y2/2+box[1]*wRatio/2)
        else:
            x1 = int(x2/2-box[1]*hRatio/2)
            x2 = int(x2/2+box[1]*hRatio/2)
        img = img.crop((x1,y1,x2,y2))

    # Resize the image with best quality algorithm
    return img.resize(box, Image.ANTIALIAS)


def pixelize_squares(img, psize, canvas):
    # Uses the graphics library to draw rectangles all over the image
    rad = psize//2
    width, height = img.size
    for x in range(0, width, psize):
        for y in range(0, height, psize):
            rgba = img.getpixel((x+rad, y+rad))
            if len(rgba) is 3: r,g,b = rgba
            elif len(rgba) is 4: r,g,b,a = rgba
            else: break
            canvas.create_rectangle(x,y, x+psize,y+psize, fill=color_rgb(r,g,b), width=0)

