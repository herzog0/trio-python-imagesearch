from src.imagesearch import ImageClick
import trio

images = [f"/home/olivaras/PycharmProjects/trio-python-imagesearch/src/images/{x}.png" for x in range(10)]

if __name__ == '__main__':
    # for image in images:
    #     image_search(image)
    with ImageClick(verbose=True) as ic:
        trio.run(ic.multiple_image_search, *[images])
    # trio.run(multiple_image_search_no_thread, *[images]) # 36.94