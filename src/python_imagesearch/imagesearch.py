import cv2.cv2 as cv2
import numpy as np
import pyautogui
import random
import platform
import subprocess
import logging
import os
import trio

logging.basicConfig(level=logging.INFO)

pyautogui.FAILSAFE = False

is_retina = False
if platform.system() == "Darwin":
    is_retina = subprocess.call("system_profiler SPDisplaysDataType | grep 'retina'", shell=True)


def save_screenshot(name):
    img = pyautogui.screenshot()
    img.save(name+".png")


'''

grabs a region (topx, topy, bottomx, bottomy)
to the tuple (topx, topy, width, height)

input : a tuple containing the 4 coordinates of the region to capture

output : a PIL image of the area selected.

'''


def region_grabber(region):
    if is_retina:
        region = [n * 2 for n in region]
    x1 = region[0]
    y1 = region[1]
    width = region[2] - x1
    height = region[3] - y1

    return pyautogui.screenshot(region=(x1, y1, width, height))


'''
Returns the most probable location of the image:
'''


def most_probable_location(pil, image, precision):
    img_rgb = np.array(pil)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
    # height, width = template.shape
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val < precision:
        return None
    return max_loc


'''

Searchs for an image within an area

input :

image : path to the image file (see opencv imread for supported types)
x1 : top left x value
y1 : top left y value
x2 : bottom right x value
y2 : bottom right y value
precision : the higher, the lesser tolerant and fewer false positives are found default is 0.8
im : a PIL image, usefull if you intend to search the same unchanging region for several elements

returns :
the top left corner coordinates of the element if found as an array [x,y] or [-1,-1] if not

'''


def image_search_area(image, x1, y1, x2, y2, precision=0.8, im=None):
    if im is None:
        im = region_grabber(region=(x1, y1, x2, y2))
        if is_retina:
            im.thumbnail((round(im.size[0] * 0.5), round(im.size[1] * 0.5)))

    return most_probable_location(im, image, precision)


'''

Click on the center of an image with a bit of random.
eg, if an image is 100*100 with an offset of 5 it may click at 52,50 the first time and then 55,53 etc
Useful to avoid anti-bot monitoring while staying precise.

This function doesn't search for the image, it's only meant for easy clicking on the images.

input :

image : path to the image file (see opencv imread for supported types)
pos : array containing the position of the top left corner of the image [x,y]
action : button of the mouse to activate : "left" "right" "middle", see pyautogui.click documentation for more info
time : time taken for the mouse to move from where it was to the new position
'''


def click(pos, action, sluggishness, offset=5, image=None):
    if image:
        img = cv2.imread(image)
        height, width, _ = img.shape
        y, x = (pos[1] + r(height / 2, offset), pos[0] + r(width / 2, offset))
    else:
        y, x = (pos[1], pos[0])
    pyautogui.moveTo(x, y, sluggishness)
    pyautogui.click(button=action)


'''
Searchs for an image on the screen

input :

image : path to the image file (see opencv imread for supported types)
precision : the higher, the lesser tolerant and fewer false positives are found default is 0.8
im : a PIL image, usefull if you intend to search the same unchanging region for several elements

returns :
the top left corner coordinates of the element if found as an array [x,y] or [-1,-1] if not

'''


def image_search(image, precision=0.8, pil=None):
    if pil is None:
        pil = pyautogui.screenshot()
    if is_retina:
        pil.thumbnail((round(pil.size[0] * 0.5), round(pil.size[1] * 0.5)))
    return most_probable_location(pil, image, precision)


'''
Searchs for an image on screen continuously until it's found.

input :
image : path to the image file (see opencv imread for supported types)
time : Waiting time after failing to find the image 
precision : the higher, the lesser tolerant and fewer false positives are found default is 0.8

returns :
the top left corner coordinates of the element if found as an array [x,y] 

'''


async def image_search_loop(image, interval=0.1, precision=0.8, filename='', pil=None):
    while not (pos := image_search(image, precision, pil)):
        logging.info("\n" + filename + " not found, waiting\n")
        await trio.sleep(interval)
    return pos


async def multiple_image_search_loop(images, interval=0.1, timeout=None, precision=0.8):
    async def do_search():
        while True:
            pil = pyautogui.screenshot()
            for image in images:
                if pos := image_search(image, precision, pil):
                    return {
                        "position": pos,
                        "image": image
                    }
            await trio.sleep(interval)

    if timeout:
        with trio.fail_after(timeout):
            return await do_search()
    else:
        return await do_search()

'''
Searches for an image on screen continuously until it's found or max number of samples reached.

input :
image : path to the image file (see opencv imread for supported types)
time : Waiting time after failing to find the image
max_samples: maximum number of samples before function times out.
precision : the higher, the lesser tolerant and fewer false positives are found default is 0.8

returns :
the top left corner coordinates of the element if found as an array [x,y] 

'''


async def image_search_num_loop(image, interval, max_samples, precision=0.8, filename=""):
    count = 0
    while (count := count + 1) <= max_samples and not (pos := image_search(image, precision)):
        logging.info("\n" + filename + " not found, waiting \n")
        await trio.sleep(interval)
    return pos


'''
Searches for an image on a region of the screen continuously until it's found.

input :
image : path to the image file (see opencv imread for supported types)
time : Waiting time after failing to find the image 
x1 : top left x value
y1 : top left y value
x2 : bottom right x value
y2 : bottom right y value
precision : the higher, the lesser tolerant and fewer false positives are found default is 0.8

returns :
the top left corner coordinates of the element as an array [x,y] 

'''


async def image_search_region_loop(image, interval, max_samples, x1, y1, x2, y2, precision=0.8, filename=""):
    count = 0
    while (count := count + 1) <= max_samples and not (pos := image_search_area(image, x1, y1, x2, y2, precision)):
        logging.info("\n" + filename + " not found, waiting \n")
        await trio.sleep(interval)
    return pos


'''
Searches for an image on the screen and counts the number of occurrences.

input :
image : path to the target image file (see opencv imread for supported types)
precision : the higher, the lesser tolerant and fewer false positives are found default is 0.9

returns :
the number of times a given image appears on the screen.
optionally an output image with all the occurrences boxed with a red outline.

'''


def image_search_count(image, precision=0.9):
    img_rgb = pyautogui.screenshot()
    if is_retina:
        img_rgb.thumbnail((round(img_rgb.size[0] * 0.5), round(img_rgb.size[1] * 0.5)))
    img_rgb = np.array(img_rgb)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(image, 0)
    w, h = template.shape[::-1]
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.ma.where(res >= precision)
    count = 0
    for pt in zip(*loc[::-1]):  # Swap columns and rows
        cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)  # Uncomment to draw boxes around found
        # occurrences
        count = count + 1
    cv2.imwrite('result.png', img_rgb)  # Uncomment to write output image with boxes drawn around occurrences
    return count


'''
Get all screens on the provided folder and search them on screen.

input :
path : path of the folder with the images to be searched on screen
precision : the higher, the lesser tolerant and fewer false positives are found default is 0.8

returns :
A dictionary where the key is the path to image file and the value is the position where was found.
'''


def image_search_from_folder(path, precision):
    print(path)
    images_pos = {}
    path = path if path[-1] == '/' or '\\' else path+'/'
    valid_images = [".jpg", ".gif", ".png", ".jpeg"]
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and os.path.splitext(f)[1].lower()
             in valid_images]
    for file in files:
        pos = image_search(path + file, precision)
        images_pos[path+file] = pos
    return images_pos


def r(num, rand):
    return num + rand * random.random()


if __name__ == '__main__':
    print("nothing")
