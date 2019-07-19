import yt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rc_context
import matplotlib.animation as anim
import matplotlib.image as mgimg
from decimal import Decimal
import scipy.constants

#parallel computation
#yt.enable_parallelism()

def main():
    #------ Define parameters in CODE ------
    #pathway to where program is saved
    program_path = "/Users/andy/Desktop/Summer Projects/Visualization/"
    #pathway to where data is saved
    data_path = "/Users/andy/Desktop/L100_N256/snapdir_015/snapshot_015.0.hdf5"
    #pathway to rockstar catalog & corresponding snaphost .bin file
    rockstar_path = '/Users/andy/Desktop/Summer Projects/Visualization/rockstar/halos_015.0.bin'
    #how many frames to generate for animation
    frames = 100
    #animation type: zoom, rotate, move camera or rotzoom (rotate while zooming in)
    anim_type = 'zoom'
    #angle to rotate camera by over the course of the whole animation (multiple of pi)
    #define for rotate and rotzoom
    angle = 2
    #total magnification to achieve by end of animation
    #define for zoom and rotzoom
    magnif = 10.0
    #which point to center animation at, options: max, min, box_middle
    #to center animation at arbitrary point, enter anim_center_req = [xcoord, ycoord, zcoord]
    #to center at given halo, enter halo_id
    anim_center_req = 'max'
    #name of animation .mp4 file to be saved at the end (without extension)
    anim_name = '512rotzoom'
    #resolution of each frame (in pixels)
    dims = 64
    #sigma_clip: how much to enhance regions of high density
    s_clip = 5.0
    #frames per second (default to 10 fps)
    fps = 10

    """SCRIPT, DO NOT EDIT"""

    ds = yt.load(data_path)

    right_edge = ds.domain_right_edge
    left_edge = ds.domain_left_edge

    grid_ds = grid(ds, right_edge, left_edge, dims)

    sc, cam, box_middle = make_scene(grid_ds)

    name, velocity = generate_frames(grid_ds, anim_type, frames, sc, cam, angle, s_clip, magnif, anim_center_req, box_middle, rockstar_path, fps)

    make_animation(frames, name, anim_name, program_path, fps, velocity, anim_type)


#create arbitrary grid, required for data from particle based simulations
def grid(ds, right_edge, left_edge, dims):
    arb_grid = ds.arbitrary_grid(left_edge, right_edge, [dims,dims,dims])
    #if yt.is_root():
    ds_new = arb_grid.save_as_dataset(fields=[('deposit','PartType1_density')])
    grid_ds = yt.load(ds_new)
    print ('-------- Arbitrary grid dataset created. --------')
    return grid_ds

#generate .png files to be used as frames in animation
def generate_frames(grid_ds, anim_type, frames, sc, cam, angle, s_clip, magnif, anim_center_req, box_middle, rockstar_path, fps):
    if anim_type == 'rotate':
        anim_center, center_name = create_anim_center(anim_center_req, grid_ds, box_middle, rockstar_path)
        name, velocity = rotate(grid_ds, frames, anim_center, sc, cam, center_name, angle, s_clip, fps)
    elif anim_type == 'move':
        anim_center, center_name = create_anim_center(anim_center_req, grid_ds, box_middle, rockstar_path)
        name, velocity = move(grid_ds, frames, anim_center, sc, cam, center_name, s_clip)
    elif anim_type == 'zoom':
        anim_center, center_name = create_anim_center(anim_center_req, grid_ds, box_middle, rockstar_path)
        name, velocity = zoom(grid_ds, frames, anim_center, sc, cam, center_name, s_clip, magnif)
    elif anim_type == 'rotzoom':
        anim_center, center_name = create_anim_center(anim_center_req, grid_ds, box_middle, dict)
        name, velocity = rotate_zoom(grid_ds, frames, anim_center, sc, cam, center_name, s_clip, magnif, angle, fps)
    print ('-------- Frames created. --------')
    return name, velocity

#find maximum of a given field
def find_max(grid_ds):
    v, c = grid_ds.find_max(('gas', 'PartType1_density'))
    print ('-------- Density maximum located at ' + str(c) + ' with value ' + str(v) + '. --------')
    return c

#find minomum of a given field
def find_min(grid_ds):
    v, c = grid_ds.find_min(('gas', 'PartType1_density'))
    print ('-------- Density minimum located at ' + str(c) + ' with value ' + str(v) + '. --------')
    return c

#center animation at a requested point
def create_anim_center(anim_center_req, grid_ds, box_middle, rockstar_path):
    if anim_center_req == 'max':
        anim_center = find_max(grid_ds)
        center_name = 'max_'
    elif anim_center_req == 'min':
        anim_center = find_max(grid)
        center_name = 'min_'
    elif anim_center_req == 'box_middle':
        anim_center = box_middle
        center_name = 'middle_'
    elif type(anim_center_req) == int:
        dict = make_catalog(rockstar_path)
        anim_center = grid_ds.arr(dict[anim_center_req])
        center_name = 'halo_' + str(anim_center_req) + '_'
    else:
        anim_center = grid_ds.arr(anim_center_req)
        center_name = 'arb_' + str(anim_center_req) + '_'
    return anim_center, center_name

#create dictionary to access information about halos using their id only
def make_catalog(rockstar_path):
    data = yt.load('/Users/andy/Desktop/Summer Projects/Visualization/rockstar/halos_015.0.bin')
    rockstar = data.all_data()
    dictionary = {}
    for i in range(len(rockstar['halos', 'particle_identifier'])):
        dictionary[i] = [rockstar['halos', 'particle_position_x'].in_units('code_length')[i], 
        rockstar['halos', 'particle_position_y'].in_units('code_length')[i],
        rockstar['halos', 'particle_position_z'].in_units('code_length')[i]]
    np.arange(0, len(rockstar['halos', 'particle_identifier']))
    return dictionary

#create Scene (yt object) and add camera, can change type of camera from 'perspective'
def make_scene(grid_ds):
    sc = yt.create_scene(grid_ds, field=('gas','PartType1_density'))
    cam = sc.add_camera(grid_ds, lens_type='perspective')
    focus = cam.focus
    print ('-------- Scene created. --------')
    return sc, cam, focus

#rotate camera by total angle theta around rot_center in frames number of steps
def rotate(grid_ds, frames, anim_center, sc, cam, center_name, angle, s_clip, fps):
    theta = np.pi * angle
    for i in cam.iter_rotate(theta, frames, rot_center=anim_center):
        cam.set_focus(anim_center)
        sc.render()
        #if yt.is_root():
        sc.save("rot_" + str(center_name) + str(i) + ".png", sigma_clip=s_clip)
    name = 'rot_' + str(center_name)
    velocity = calc_velocity(cam, sc, anim_center, frames, fps, angle)
    return name, velocity

#move camera to anim_center in frames number of steps
def move(grid_ds, frames, anim_center, sc, cam, center_name, s_clip):
    for i in cam.iter_move(anim_center, frames):
        cam.set_focus(anim_center)
        sc.render()
        sc.save("move_"+ str(center_name) + str(i) + ".png", sigma_clip=s_clip)
    name = 'move_' + str(center_name)
    velocity = 'N/A'
    return name, velocity

#zoom in by a total of magnif in frames number of steps centered at anim_center
def zoom(grid_ds, frames, anim_center, sc, cam, center_name, s_clip, magnif):
    for i in cam.iter_zoom(magnif, frames):
        cam.set_focus(anim_center)
        sc.render()
        sc.save('zoom_' + str(center_name) + str(i) + '.png', sigma_clip=s_clip)
    name = 'zoom_' + str(center_name)
    velocity = 'N/A'
    return name, velocity

#rotate around a given point while zooming in on it
def rotate_zoom(grid_ds, frames, anim_center, sc, cam, center_name, s_clip, magnif, angle, fps):
    theta = np.pi * angle
    magnif_step = magnif**(1./frames)
    #magnif_step = 1.25
    for i in cam.iter_rotate(theta, frames, rot_center=anim_center):
        cam.set_focus(anim_center)
        cam.zoom(magnif_step)
        sc.render()
        sc.save("rotzoom_" + str(center_name) + str(i) +".png", sigma_clip=s_clip)
    name = 'rotzoom_' + str(center_name)
    velocity = calc_velocity(cam, sc, anim_center, frames, fps, angle)
    return name, velocity

#calculate rotation velocity, assuming box length in Mpc
def calc_velocity(cam, sc, anim_center, frames, fps, angle):
    to_meter = 3.086 * 10**6
    c = scipy.constants.c
    radius = np.linalg.norm(np.array(cam.get_position() - anim_center))
    omega = float((np.pi * angle) / (frames / fps))
    velocity = '%.3E' % Decimal((omega * radius * to_meter * 10**6)/c)
    return velocity

#create animation from rendered .png files
def make_animation(frames, name, anim_name, program_path, fps, velocity, anim_type):
    fig = plt.figure()
    images = []
    i = 0

    Writer = anim.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='Me'), bitrate=1800)

    for i in range (0, frames):
        im_name = '/Users/andy/Desktop/Summer Projects/Visualization/CuillinData/rotzoom_max_' + str(i) + '.png'
        #im_name = program_path + str(name) + str(i) + ".png"
        image = mgimg.imread(im_name)
        im_plot = plt.imshow(image, origin='lower')
        images.append([im_plot])
        i+= 1
    plt.xticks([])
    plt.yticks([])
    if 'rot' in anim_type:
        plt.xlabel('rotation velocity: ' + str(velocity) + 'c')
    animation = anim.ArtistAnimation(fig, images, interval=1000)
    #save animation with requested name
    animation.save(str(anim_name) + '.mp4', writer = writer)
    print ('-------- Animation saved with name ' + str(anim_name) + '.mp4 --------')

    
    

main()
