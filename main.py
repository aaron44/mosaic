from graphics import *
from pixelize import pixelize


def main():
	win = GraphWin("Pixelixer", 800, 500)
	win.set_coords(5,495,795,5)
	win.set_background('gray')

	sidebar = Rectangle(Point(600,0), Point(800,500))
	sidebar.set_fill('white')
	sidebar.draw(win)

	buttons = {
		'load':   Button(Point(700,42.5), 18, "Load Image"),
		'save':   Button(Point(700, 100), 18, "Save Image"),
		'update': Button(Point(700, 300), 18, "Update"),
		'quit':   Button(Point(700, 475), 18, "Quit")
	}
	ptext  = Text(Point(670, 250), "Pixel Size:")
	ptext.set_size(13)
	ptext.draw(win)
	pixels = Spin(Point(730, 250), 4, range=(0, 100))
	pixels.set_fill('white')
	pixels.draw(win)

	for b in buttons:
		buttons[b].set_color('black')
		buttons[b].set_fill('white')
		buttons[b].draw(win)

	# image = Image(Point(50,50), open('./Elephant.jpg', 'r'))
	# image.draw(win)

	win.get_mouse()

if __name__ == '__main__':
	main()
