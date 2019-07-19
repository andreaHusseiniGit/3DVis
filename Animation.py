import yt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rc_context
import matplotlib.animation as anim
import matplotlib.image as mgimg

#yt.enable_parallelism()

def main():
    #file path to images
    image_path = "/Users/andy/Desktop/Summer Projects/Visualization/Data/rotate_center_100_"
    #number of images
    frames = 100
    #name of produced .mp4 file
    anim_name = 'my_animation'

    make_anim(image_path, frames, anim_name)

#animate figures pre-generated somewhere else
def make_anim(image_path, frames, anim_name):
    #specify path to images
    im_path = image_path
    fig = plt.figure()
    images = []
    i = 0

    Writer = anim.writers['ffmpeg']
    writer = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)

    for i in range (0, frames):
        im_name = im_path + str(i) + ".png"
        image = mgimg.imread(im_name)
        im_plot = plt.imshow(image, origin='lower')
        images.append([im_plot])
        i+= 1

    animation = anim.ArtistAnimation(fig, images, interval=100)
    animation.save(str(anim_name) + '.mp4', writer = writer)

main()

