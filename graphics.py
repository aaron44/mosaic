import time, math, os
import tkinter as tk
from tkinter import filedialog
from PIL import Image as Img, ImageTk
from random import randrange

##########################################################################
# Module Exceptions

class GraphicsError(Exception):
    """Generic error class for graphics module exceptions."""
    pass

OBJ_ALREADY_DRAWN = "Object currently drawn"
UNSUPPORTED_METHOD = "Object doesn't support operation"
BAD_OPTION = "Illegal option value"
DEAD_THREAD = "Graphics thread quit unexpectedly"

_root = tk.Tk()
_root.withdraw()

def update():
    _root.update()

############################################################################
# Graphics classes start here
        
class GraphWin(tk.Canvas):

    """A GraphWin is a toplevel window for displaying graphics."""

    def __init__(self, title="Graphics Window", width=200, height=200, autoflush=True):
        master = tk.Toplevel(_root)
        master.protocol("WM_DELETE_WINDOW", self.close)
        tk.Canvas.__init__(self, master, width=width, height=height)
        self.master.title(title)
        self.pack()
        master.resizable(0,0)
        self.foreground = "black"
        self.items = []
        self.mouseX = None
        self.mouseY = None
        self.bind("<Button-1>", self._on_click)
        self.height = height
        self.width = width
        self.autoflush = autoflush
        self._mouse_callback = None
        self.trans = None
        self.closed = False
        master.lift()
        if autoflush: _root.update()
     
    def _check_open(self):
        if self.closed:
            raise GraphicsError("window is closed")

    def set_background(self, color):
        """Set background color of the window"""
        self._check_open()
        self.config(bg=color)
        self._autoflush()
        
    def set_coords(self, x1, y1, x2, y2):
        """Set coordinates of window to run from (x1,y1) in the
        lower-left corner to (x2,y2) in the upper-right corner."""
        self.trans = Transform(self.width, self.height, x1, y1, x2, y2)

    def close(self):
        """Close the window"""

        if self.closed: return
        self.closed = True
        self.master.destroy()
        self._autoflush()


    def is_closed(self):
        return self.closed


    def is_open(self):
        return not self.closed


    def _autoflush(self):
        if self.autoflush:
            _root.update()

    
    def plot(self, x, y, color="black"):
        """Set pixel (x,y) to the given color"""
        self._check_open()
        xs,ys = self.to_screen(x,y)
        self.create_line(xs,ys,xs+1,ys, fill=color)
        self._autoflush()
        
    def plot_pixel(self, x, y, color="black"):
        """Set pixel raw (independent of window coordinates) pixel
        (x,y) to color"""
        self._check_open()
        self.create_line(x,y,x+1,y, fill=color)
        self._autoflush()
      
    def flush(self):
        """Update drawing to the window"""
        self._check_open()
        self.update_idletasks()
        
    def get_mouse(self):
        """Wait for mouse click and return Point object representing
        the click"""
        self.update()      # flush any prior clicks
        self.mouseX = None
        self.mouseY = None
        while self.mouseX == None or self.mouseY == None:
            self.update()
            if self.is_closed(): raise GraphicsError("get_mouse in closed window")
            time.sleep(.1) # give up thread
        x,y = self.to_world(self.mouseX, self.mouseY)
        self.mouseX = None
        self.mouseY = None
        return Point(x,y)

    def check_mouse(self):
        """Return last mouse click or None if mouse has
        not been clicked since last call"""
        if self.is_closed():
            raise GraphicsError("check_mouse in closed window")
        self.update()
        if self.mouseX != None and self.mouseY != None:
            x,y = self.to_world(self.mouseX, self.mouseY)
            self.mouseX = None
            self.mouseY = None
            return Point(x,y)
        else:
            return None
            
    def get_height(self):
        """Return the height of the window"""
        return self.height
        
    def get_width(self):
        """Return the width of the window"""
        return self.width
    
    def to_screen(self, x, y):
        trans = self.trans
        if trans:
            return self.trans.screen(x,y)
        else:
            return x,y
                      
    def to_world(self, x, y):
        trans = self.trans
        if trans:
            return self.trans.world(x,y)
        else:
            return x,y
        
    def set_mouse_handler(self, func):
        self._mouse_callback = func
        
    def _on_click(self, e):
        self.mouseX = e.x
        self.mouseY = e.y
        if self._mouse_callback:
            self._mouse_callback(Point(e.x, e.y)) 
                      
class Transform:

    """Internal class for 2-D coordinate transformations"""
    
    def __init__(self, w, h, xlow, ylow, xhigh, yhigh):
        # w, h are width and height of window
        # (xlow,ylow) coordinates of lower-left [raw (0,h-1)]
        # (xhigh,yhigh) coordinates of upper-right [raw (w-1,0)]
        xspan = (xhigh-xlow)
        yspan = (yhigh-ylow)
        self.xbase = xlow
        self.ybase = yhigh
        self.xscale = xspan/float(w-1)
        self.yscale = yspan/float(h-1)
        
    def screen(self,x,y):
        # Returns x,y in screen (actually window) coordinates
        xs = (x-self.xbase) / self.xscale
        ys = (self.ybase-y) / self.yscale
        return int(xs+0.5),int(ys+0.5)
        
    def world(self,xs,ys):
        # Returns xs,ys in world coordinates
        x = xs*self.xscale + self.xbase
        y = self.ybase - ys*self.yscale
        return x,y


# Default values for various item configuration options. Only a subset of
#  keys may be present in the configuration dictionary for a given item.
DEFAULT_CONFIG = {"fill":"",
      "outline":"black",
      "width":"1",
      "arrow":"none",
      "text":"",
      "justify":"center",
                  "font": ("helvetica", 12, "normal")}

class GraphicsObject:

    """Generic base class for all of the drawable objects"""
    # A subclass of GraphicsObject should override _draw and
    #  and _move methods.
    
    def __init__(self, options):
        # options is a list of strings indicating which options are
        # legal for this object.
        
        # When an object is drawn, canvas is set to the GraphWin(canvas)
        #    object where it is drawn and id is the TK identifier of the
        #    drawn shape.
        self.canvas = None
        self.id = None

        # config is the dictionary of configuration options for the widget.
        config = {}
        for option in options:
            config[option] = DEFAULT_CONFIG[option]
        self.config = config
        
    def set_fill(self, color):
        """Set interior color to color"""
        self._reconfig("fill", color)
        
    def set_outline(self, color):
        """Set outline color to color"""
        self._reconfig("outline", color)
        
    def set_width(self, width):
        """Set line weight to width"""
        self._reconfig("width", width)

    def draw(self, graphwin):

        """Draw the object in graphwin, which should be a GraphWin
        object.  A GraphicsObject may only be drawn into one
        window. Raises an error if attempt made to draw an object that
        is already visible."""

        if self.canvas and not self.canvas.is_closed(): raise GraphicsError(OBJ_ALREADY_DRAWN)
        if graphwin.is_closed(): raise GraphicsError("Can't draw to closed window")
        self.canvas = graphwin
        self.id = self._draw(graphwin, self.config)
        if graphwin.autoflush:
            _root.update()

            
    def undraw(self):

        """Undraw the object (i.e. hide it). Returns silently if the
        object is not currently drawn."""
        
        if not self.canvas: return
        if not self.canvas.is_closed():
            self.canvas.delete(self.id)
            if self.canvas.autoflush:
                _root.update()
        self.canvas = None
        self.id = None


    def move(self, dx, dy):

        """move object dx units in x direction and dy units in y
        direction"""
        
        self._move(dx,dy)
        canvas = self.canvas
        if canvas and not canvas.is_closed():
            trans = canvas.trans
            if trans:
                x = dx/ trans.xscale 
                y = -dy / trans.yscale
            else:
                x = dx
                y = dy
            self.canvas.move(self.id, x, y)
            if canvas.autoflush:
                _root.update()
           
    def _reconfig(self, option, setting):
        # Internal method for changing configuration of the object
        # Raises an error if the option does not exist in the config
        #    dictionary for this object
        if option not in self.config:
            raise GraphicsError(UNSUPPORTED_METHOD)
        options = self.config
        options[option] = setting
        if self.canvas and not self.canvas.is_closed():
            self.canvas.itemconfig(self.id, options)
            if self.canvas.autoflush:
                _root.update()


    def _draw(self, canvas, options):
        """draws appropriate figure on canvas with options provided
        Returns Tk id of item drawn"""
        pass # must override in subclass


    def _move(self, dx, dy):
        """updates internal state of object to move it dx,dy units"""
        pass # must override in subclass

         
class Point(GraphicsObject):
    def __init__(self, x, y):
        GraphicsObject.__init__(self, ["outline", "fill"])
        self.set_fill = self.set_outline
        self.x = x
        self.y = y
        
    def _draw(self, canvas, options):
        x,y = canvas.to_screen(self.x,self.y)
        return canvas.create_rectangle(x,y,x+1,y+1,options)
        
    def _move(self, dx, dy):
        self.x = self.x + dx
        self.y = self.y + dy
        
    def clone(self):
        other = Point(self.x,self.y)
        other.config = self.config.copy()
        return other
                
    def getX(self): return self.x
    def getY(self): return self.y

class _BBox(GraphicsObject):
    # Internal base class for objects represented by bounding box
    # (opposite corners) Line segment is a degenerate case.
    
    def __init__(self, p1, p2, options=["outline","width","fill"]):
        GraphicsObject.__init__(self, options)
        self.p1 = p1.clone()
        self.p2 = p2.clone()

    def _move(self, dx, dy):
        self.p1.x = self.p1.x + dx
        self.p1.y = self.p1.y + dy
        self.p2.x = self.p2.x + dx
        self.p2.y = self.p2.y  + dy
                
    def getP1(self): return self.p1.clone()
    def getP2(self): return self.p2.clone()
    
    def get_center(self):
        p1 = self.p1
        p2 = self.p2
        return Point((p1.x+p2.x)/2.0, (p1.y+p2.y)/2.0)
    
class Rectangle(_BBox):
    
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2)
    
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.to_screen(p1.x,p1.y)
        x2,y2 = canvas.to_screen(p2.x,p2.y)
        return canvas.create_rectangle(x1,y1,x2,y2,options)

    def get_width(self):
        return abs(self.p2.getX() - self.p1.getX())
    def get_height(self):
        return abs(self.p2.getY() - self.p1.getY())

    def get_area(self):
        return self.get_width() * self.get_height()
    def get_perimeter(self):
        return 2 * (self.get_width() + self.get_height())
        
    def clone(self):
        other = Rectangle(self.p1, self.p2)
        other.config = self.config.copy()
        return other
        
class Oval(_BBox):
    
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2)
        
    def clone(self):
        other = Oval(self.p1, self.p2)
        other.config = self.config.copy()
        return other
   
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.to_screen(p1.x,p1.y)
        x2,y2 = canvas.to_screen(p2.x,p2.y)
        return canvas.create_oval(x1,y1,x2,y2,options)
    
class Circle(Oval):
    def __init__(self, center, radius):
        p1 = Point(center.x-radius, center.y-radius)
        p2 = Point(center.x+radius, center.y+radius)
        Oval.__init__(self, p1, p2)
        self.radius = radius
        
    def clone(self):
        other = Circle(self.get_center(), self.radius)
        other.config = self.config.copy()
        return other
        
    def get_radius(self):
        return self.radius
              
class Line(_BBox):
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2, ["arrow","fill","width"])
        self.set_fill(DEFAULT_CONFIG['outline'])
        self.set_outline = self.set_fill
   
    def clone(self):
        other = Line(self.p1, self.p2)
        other.config = self.config.copy()
        return other
  
    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1,y1 = canvas.to_screen(p1.x,p1.y)
        x2,y2 = canvas.to_screen(p2.x,p2.y)
        return canvas.create_line(x1,y1,x2,y2,options)
        
    def set_arrow(self, option):
        if not option in ["first","last","both","none"]:
            raise GraphicsError(BAD_OPTION)
        self._reconfig("arrow", option)


class LineSeg(Line):
    def __init__(self, p1, p2): 
        Line.__init__(self, p1, p2)
        self.x = self.p2.getX() - self.p1.getX()
        self.y = self.p2.getY() - self.p1.getY()

    def get_length(self): 
        return round(math.sqrt(self.x**2 + self.y**2), 2)
    def get_slope(self): 
        return round(self.y / self.x, 2)

    def get_midpoint(self):
        x = (self.p1.getX() + self.p2.getX()) /2
        y = (self.p1.getY() + self.p2.getY()) /2
        return Point(x, y)


class Polygon(GraphicsObject):
    def __init__(self, *points):
        # if points passed as a list, extract it
        if len(points) == 1 and type(points[0]) == type([]):
            points = points[0]
        self.points = list(map(Point.clone, points))
        GraphicsObject.__init__(self, ["outline", "width", "fill"])
        
    def clone(self):
        other = Polygon(*self.points)
        other.config = self.config.copy()
        return other

    def get_points(self):
        return list(map(Point.clone, self.points))

    def _move(self, dx, dy):
        for p in self.points:
            p.move(dx,dy)
   
    def _draw(self, canvas, options):
        args = [canvas]
        for p in self.points:
            x,y = canvas.to_screen(p.x,p.y)
            args.append(x)
            args.append(y)
        args.append(options)
        return GraphWin.create_polygon(*args) 


class Triangle(Polygon):
    def __init__(self, p1, p2, p3):
        Polygon.__init__(self, p1, p2, p3)
        self.p1, self.p2, self.p3 = p1, p2, p3
        self.side1 = self.getSideLength(p1, p2)
        self.side2 = self.getSideLength(p2, p3)
        self.side3 = self.getSideLength(p3, p1)

    def get_area(self):
        a, b, c = self.side1, self.side2, self.side3
        s = (a+b+c) / 2
        return round(math.sqrt(s*((s-a)*(s-b)*(s-c))),2)

    def get_perimeter(self):
        return round(self.side1 + self.side2 + self.side3, 2)

    def get_side_length(self, p1, p2):
        return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)


class Text(GraphicsObject):
    def __init__(self, p, text):
        GraphicsObject.__init__(self, ["justify","fill","text","font"])
        self.set_text(text)
        self.anchor = p.clone()
        self.set_fill(DEFAULT_CONFIG['outline'])
        self.set_outline = self.set_fill
        
    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.to_screen(p.x,p.y)
        return canvas.create_text(x,y,options)
        
    def _move(self, dx, dy):
        self.anchor.move(dx,dy)
        
    def clone(self):
        other = Text(self.anchor, self.config['text'])
        other.config = self.config.copy()
        return other

    def set_text(self,text):
        self._reconfig("text", text)
        
    def get_text(self):
        return self.config["text"]
            
    def get_anchor(self):
        return self.anchor.clone()

    def set_face(self, face):
        if face in ['helvetica','arial','courier','times roman']:
            f,s,b = self.config['font']
            self._reconfig("font",(face,s,b))
        else:
            raise GraphicsError(BAD_OPTION)

    def set_size(self, size):
        if 5 <= size <= 36:
            f,s,b = self.config['font']
            self._reconfig("font", (f,size,b))
        else:
            raise GraphicsError(BAD_OPTION)

    def set_style(self, style):
        if style in ['bold','normal','italic', 'bold italic']:
            f,s,b = self.config['font']
            self._reconfig("font", (f,s,style))
        else:
            raise GraphicsError(BAD_OPTION)

    def set_color(self, color):
        self.set_fill(color)


class Entry(GraphicsObject):
    def __init__(self, p, width):
        GraphicsObject.__init__(self, [])
        self.anchor = p.clone()
        self.width = width
        self.text = tk.StringVar(_root)
        self.text.set("")
        self.fill = "gray"
        self.color = "black"
        self.font = DEFAULT_CONFIG['font']
        self.entry = None

    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.to_screen(p.x,p.y)
        frm = tk.Frame(canvas.master)
        self.entry = tk.Entry(frm,
                              width=self.width,
                              textvariable=self.text,
                              bg=self.fill,
                              fg=self.color,
                              font=self.font)
        self.entry.pack()
        #self.set_fill(self.fill)
        return canvas.create_window(x,y,window=frm)

    def get_text(self):
        return self.text.get()

    def _move(self, dx, dy):
        self.anchor.move(dx,dy)

    def get_anchor(self):
        return self.anchor.clone()

    def clone(self):
        other = Entry(self.anchor, self.width)
        other.config = self.config.copy()
        other.text = tk.StringVar()
        other.text.set(self.text.get())
        other.fill = self.fill
        return other

    def set_text(self, t):
        self.text.set(t)

            
    def set_fill(self, color):
        self.fill = color
        if self.entry:
            self.entry.config(bg=color)

            
    def _set_font_component(self, which, value):
        font = list(self.font)
        font[which] = value
        self.font = tuple(font)
        if self.entry:
            self.entry.config(font=self.font)


    def set_face(self, face):
        if face in ['helvetica','arial','courier','times roman']:
            self._set_font_component(0, face)
        else:
            raise GraphicsError(BAD_OPTION)

    def set_size(self, size):
        if 5 <= size <= 36:
            self._set_font_component(1,size)
        else:
            raise GraphicsError(BAD_OPTION)

    def set_style(self, style):
        if style in ['bold','normal','italic', 'bold italic']:
            self._set_font_component(2,style)
        else:
            raise GraphicsError(BAD_OPTION)

    def set_color(self, color):
        self.color=color
        if self.entry:
            self.entry.config(fg=color)


class Spin(Entry):
    def __init__(self, p, width, range):
        Entry.__init__(self, p, width)
        self.small, self.large = range

    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.to_screen(p.x,p.y)
        frm = tk.Frame(canvas.master)
        self.entry = tk.Spinbox(frm,
                                width=self.width,
                                textvariable=self.text,
                                to=self.large,
                                from_=self.small,    
                                bg=self.fill,
                                fg=self.color,
                                font=self.font)
        self.entry.pack()
        return canvas.create_window(x,y,window=frm)


class Image(GraphicsObject):

    idCount = 0
    imageCache = {} # tk photoimages go here to avoid GC while drawn 
    
    def __init__(self, p, *pixmap):
        GraphicsObject.__init__(self, [])
        self.anchor = p.clone()
        self.imageId = Image.idCount
        Image.idCount = Image.idCount + 1
        if len(pixmap) == 1: # file name provided
            self.img = tk.PhotoImage(file=pixmap[0], master=_root)
        else: # width and height provided
            width, height = pixmap
            self.img = tk.PhotoImage(master=_root, width=width, height=height)
                
    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.to_screen(p.x,p.y)
        self.imageCache[self.imageId] = self.img # save a reference  
        return canvas.create_image(x,y,image=self.img)
    
    def _move(self, dx, dy):
        self.anchor.move(dx,dy)
        
    def undraw(self):
        try:
            del self.imageCache[self.imageId]  # allow gc of tk photoimage
        except KeyError:
            pass
        GraphicsObject.undraw(self)

    def get_anchor(self):
        return self.anchor.clone()
        
    def clone(self):
        other = Image(Point(0,0), 0, 0)
        other.img = self.img.copy()
        other.anchor = self.anchor.clone()
        other.config = self.config.copy()
        return other

    def pixelize(self, size=10):
        """Pixelizes the image to the size of `size`"""
        for block in range(0, self.img.get_width(), size):
            pass

    def get_width(self):
        """Returns the width of the image in pixels"""
        return self.img.width() 

    def get_height(self):
        """Returns the height of the image in pixels"""
        return self.img.height()

    def get_pixel(self, x, y):
        """Returns a list [r,g,b] with the RGB color values for pixel (x,y)
        r,g,b are in range(256)

        """
        
        value = self.img.get(x,y) 
        if type(value) ==  type(0):
            return [value, value, value]
        else:
            return list(map(int, value.split())) 

    def set_pixel(self, x, y, color):
        """Sets pixel (x,y) to the given color
        
        """
        self.img.put("{" + color +"}", (x, y))
        

    def save(self, filename):
        """Saves the pixmap image to filename.
        The format for the save image is determined from the filname extension.

        """
        
        path, name = os.path.split(filename)
        ext = name.split(".")[-1]
        self.img.write( filename, format=ext)


class Button(GraphicsObject):
    def __init__(self, center, width, text, command, state="active"):
        GraphicsObject.__init__(self, [])
        self.anchor = center.clone()
        self.width = width
        self.text = tk.StringVar(_root)
        self.text.set(text)
        self.fill = "gray"
        self.color = "black"
        self.state = state
        self.button = None
        self.command = command

    def _draw(self, canvas, options):
        p = self.anchor
        x,y = canvas.to_screen(p.x,p.y)
        frm = tk.Frame(canvas.master)
        self.button = tk.Button(frm,
                                command=self.command,
                                width=self.width,
                                text=self.text,
                                bg=self.fill,
                                state=self.state,
                                fg=self.color)
        self.button.pack()
        return canvas.create_window(x,y,window=frm)

    def get_text(self):
        return self.text.get()

    def _move(self, dx, dy):
        self.anchor.move(dx,dy)

    def get_anchor(self):
        return self.anchor.clone()

    def clone(self):
        other = Button(self.anchor, self.width)
        other.config = self.config.copy()
        other.text = tk.StringVar()
        other.text.set(self.text.get())
        other.fill = self.fill
        return other

    def set_text(self, t):
        self.text.set(t)

    def set_fill(self, color):
        self.fill = color
        if self.button:
            self.button.config(bg=color)

    def set_color(self, color):
        self.color=color
        if self.button:
            self.button.config(fg=color)


        
def color_rgb(r,g,b):
    """r,g,b are intensities of red, green, and blue in range(256)
    Returns color specifier string for the resulting color"""
    return "#%02x%02x%02x" % (r,g,b)

def colorize(): 
    return color_rgb(randrange(256), randrange(256), randrange(256))
def colorize_light(): 
    return color_rgb(randrange(128)+128, randrange(128)+128, randrange(128)+128)
def colorize_dark(): 
    return color_rgb(randrange(128), randrange(128), randrange(128))

def test():
    win = GraphWin()
    win.set_coords(0,0,10,10)
    t = Text(Point(5,5), "Centered Text")
    t.draw(win)
    p = Polygon(Point(1,1), Point(5,3), Point(2,7))
    p.draw(win)
    e = Entry(Point(5,6), 10)
    e.draw(win)
    win.get_mouse()
    p.set_fill("red")
    p.set_outline("blue")
    p.set_width(2)
    s = ""
    for pt in p.get_points():
        s = s + "(%0.1f,%0.1f) " % (pt.getX(), pt.getY())
    t.set_text(e.get_text())
    e.set_fill("green")
    e.set_text("Spam!")
    e.move(2,0)
    win.get_mouse()
    p.move(2,3)
    s = ""
    for pt in p.get_points():
        s = s + "(%0.1f,%0.1f) " % (pt.getX(), pt.getY())
    t.set_text(s)
    win.get_mouse()
    p.undraw()
    e.undraw()
    t.set_style("bold")
    win.get_mouse()
    t.set_style("normal")
    win.get_mouse()
    t.set_style("italic")
    win.get_mouse()
    t.set_style("bold italic")
    win.get_mouse()
    t.set_size(14)
    win.get_mouse()
    t.set_face("arial")
    t.set_size(20)
    win.get_mouse()
    win.close()

if __name__ == "__main__":
    test()
