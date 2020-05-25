from src.python_imagesearch.imagesearch import image_search

pos = image_search("./github.png")
if pos[0] != -1:
    print("position : ", pos[0], pos[1])
else:
    print("image not found")
