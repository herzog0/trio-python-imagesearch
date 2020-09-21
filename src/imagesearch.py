import cv2.cv2 as cv2
import numpy as np
import pyautogui
import random
import platform
import subprocess
import os
import trio
import threading
from loguru import logger

lock = threading.Lock()

pyautogui.FAILSAFE = False

is_retina = False
if platform.system() == "Darwin":
    is_retina = subprocess.call("system_profiler SPDisplaysDataType | grep 'retina'", shell=True)

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


def save_screenshot(name):
    img = pyautogui.screenshot()
    img.save(name + ".png")


def r(num, rand):
    return num + rand * random.random()


class _ScreenHandler:
    click_scope: bool

    def __init__(self, click_scope_config: bool, verbose: bool):
        self.click_scope = click_scope_config
        self.verbose = verbose
        self.click_blocked = False
        self.run_until_found_one = True

    def report(self, image, pos):
        if self.verbose:
            message = f"Found and clicked {image} in position {pos}" \
                if self.click_scope and not self.click_blocked \
                else f"Found {image} in position {pos}"
            logger.info(message)

    def block_clicks(self):
        self.click_blocked = True
        logger.warning("Click blocked!")

    """
    Returns the most probable location of the image:
    """

    def most_probable_location(self, pil, image, precision):
        img_rgb = np.array(pil)
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
        height, width = template.shape
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if max_val < precision:
            return None
        if self.click_scope:
            with lock:
                if not self.click_blocked:
                    self.click(pos=max_loc, action="left", sluggishness=0, offset=5, height=height, width=width)
                    self.report(image, max_loc)
                    if self.run_until_found_one:
                        self.block_clicks()
                else:
                    self.report(image, max_loc)
        else:
            self.report(image, max_loc)
        return max_loc

    """
    Searches for an image within an area
    
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
   """

    def most_probable_location_within_area(self, image, x1, y1, x2, y2, precision=0.8, im=None):
        if im is None:
            im = region_grabber(region=(x1, y1, x2, y2))
            if is_retina:
                im.thumbnail((round(im.size[0] * 0.5), round(im.size[1] * 0.5)))

        return self.most_probable_location(im, image, precision)

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

    @staticmethod
    def click(pos, action, sluggishness, offset=5, height=0, width=0):
        if height and width:
            y, x = (pos[1] + r(height // 2, offset), pos[0] + r(width // 2, offset))
        else:
            y, x = (pos[1], pos[0])
        pyautogui.moveTo(x, y, sluggishness)
        pyautogui.click(button=action)

    '''
    Searches for an image on the screen
    
    input :
    
    image : path to the image file (see opencv imread for supported types)
    precision : the higher, the lesser tolerant and fewer false positives are found default is 0.8
    im : a PIL image, useful if you intend to search the same unchanging region for several elements
    
    returns :
    the top left corner coordinates of the element if found as an array [x,y] or [-1,-1] if not
    
    '''

    def image_search_monothread(self, image, precision=0.8, pil=None):
        if pil is None:
            pil = pyautogui.screenshot()
        if is_retina:
            pil.thumbnail((round(pil.size[0] * 0.5), round(pil.size[1] * 0.5)))
        return self.most_probable_location(pil, image, precision)

    async def image_search_to_thread(self, *args):
        # This can't be cancelled! So whatever you put running on this function won't be
        # cancelled by a cancel scope.
        await trio.to_thread.run_sync(self.image_search_monothread, *args)

    async def multiple_image_search(self, images, search_times=1, interval=0, precision=0.8):
        while search_times:
            search_times -= 1
            pil = pyautogui.screenshot()
            logger.info("Took Screenshot!")
            async with trio.open_nursery() as nursery:
                for image in images:
                    nursery.start_soon(self.image_search_to_thread, *[image, precision, pil])
            await trio.sleep(interval)

    '''
    Searchs for an image on screen continuously until it's found.
    
    input :
    image : path to the image file (see opencv imread for supported types)
    time : Waiting time after failing to find the image 
    precision : the higher, the lesser tolerant and fewer false positives are found default is 0.8
    
    returns :
    the top left corner coordinates of the element if found as an array [x,y] 
    
    '''

    async def image_search_loop(self, image, interval=0.1, precision=0.8, filename='', pil=None):
        while not (pos := self.image_search_monothread(image, precision, pil)):
            logger.info("\n" + filename + " not found, waiting\n")
            await trio.sleep(interval)
        return pos

    async def multiple_image_search_no_thread(self, images, interval=0.1, precision=0.8):
        while True:
            pil = pyautogui.screenshot()
            print("took screenshot")
            for image in images:
                self.image_search_monothread(image, precision, pil)
                # click(pos, "left", 0, image=image)
            await trio.sleep(interval)

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

    async def image_search_num_loop(self, image, interval, max_samples, precision=0.8, filename=""):
        count = 0
        while (count := count + 1) <= max_samples and not (pos := self.image_search_monothread(image, precision)):
            logger.info("\n" + filename + " not found, waiting \n")
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

    # async def image_search_region_loop(self, image, interval, max_samples, x1, y1, x2, y2, precision=0.8, filename=""):
    #     count = 0
    #     while (count := count + 1) <= max_samples and not (pos := self.ima(image, x1, y1, x2, y2,
    #                                                                                      precision)):
    #         logger.info("\n" + filename + " not found, waiting \n")
    #         await trio.sleep(interval)
    #     return pos

    '''
    Searches for an image on the screen and counts the number of occurrences.
    
    input :
    image : path to the target image file (see opencv imread for supported types)
    precision : the higher, the lesser tolerant and fewer false positives are found default is 0.9
    
    returns :
    the number of times a given image appears on the screen.
    optionally an output image with all the occurrences boxed with a red outline.
    
    '''

    def image_search_count(self, image, precision=0.9):
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

    def image_search_from_folder(self, path, precision):
        print(path)
        images_pos = {}
        path = path if path[-1] == '/' or '\\' else path + '/'
        valid_images = [".jpg", ".gif", ".png", ".jpeg"]
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and os.path.splitext(f)[1].lower()
                 in valid_images]
        for file in files:
            pos = self.image_search(path + file, precision)
            images_pos[path + file] = pos
        return images_pos


class ImageClick:
    def __init__(self, verbose: bool):
        self.verbose = verbose

    def __enter__(self):
        logger.info("Entering an ImageClick scope")
        return _ScreenHandler(True, self.verbose)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error("ImageClick scope exited with an error!")
            logger.trace(exc_tb)
        else:
            logger.success("ImageClick scope concluded")


class ImageSearch:
    def __init__(self, verbose: bool):
        self.verbose = verbose

    def __enter__(self):
        logger.info("Entering an ImageSearch scope")
        return _ScreenHandler(False, self.verbose)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error("ImageSearch scope exited with an error!")
            logger.trace(exc_tb)
        else:
            logger.success("ImageSearch scope concluded")


if __name__ == '__main__':
    print("nothing")
