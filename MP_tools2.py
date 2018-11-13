import numpy as np
import json
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt
import dpcore

from munkres import Munkres # Optimization Algorithm(Hungarian Algo) / find the global minimum
import itertools

import os
from os.path import join
from os import listdir, rmdir
from shutil import move
import glob
import shutil
import re

def load_data(input_dir, dataset_dir):

    ##### Import json #####
    with open(input_dir) as f:
        data = json.load(f)

    with open(dataset_dir) as l:
        dataLims = json.load(l)

    return data, dataLims


def Create3dPoints(init_frame, last_frame, data, model_name):
    points = []
    for i in range(init_frame, last_frame):
        strnum = str(i)
        frames = []
        for item in data['landmarks'][strnum][model_name]:
            frames.extend(item)

        points.append(frames)

    p3d = np.array(points)

    return p3d


def GaussFilter3dPoints(p3d, sigma, t):
    f_gauss = gaussian_filter1d(p3d[:, 0], sigma=sigma, truncate=t)

    for x in range(1, p3d.shape[1]):
        f_gauss = np.column_stack((f_gauss, gaussian_filter1d(p3d[:, x], sigma=sigma, truncate=t)))

    # Feature Vector with filtered coordinates [1001 x 126]
    p3d_gauss = f_gauss

    # print(p3d.shape)
    # print(p3d_gauss.shape)

    return p3d_gauss


def MovPoseDescriptor(p3d_gauss, StartFrame):
    # f32 = np.dtype(np.float32)
    sz_p3d = p3d_gauss.shape
    pt0 = []
    pt1 = []
    pt2 = []
    ptm1 = []
    ptm2 = []
    for fr in range(StartFrame, sz_p3d[0] - StartFrame):
        Pt0 = []
        Pt1 = []
        Pt2 = []
        Ptm1 = []
        Ptm2 = []
        for cl in range(0, sz_p3d[1]):
            Pt0.extend([p3d_gauss[fr, cl]])
            Pt1.extend([p3d_gauss[fr + 1, cl]])
            Pt2.extend([p3d_gauss[fr + 2, cl]])
            Ptm1.extend([p3d_gauss[fr - 1, cl]])
            Ptm2.extend([p3d_gauss[fr - 2, cl]])

        pt0.append(Pt0)
        pt1.append(Pt1)
        pt2.append(Pt2)
        ptm1.append(Ptm1)
        ptm2.append(Ptm2)

    Pt0 = np.array(pt0)
    Pt1 = np.array(pt1)
    Pt2 = np.array(pt2)
    Ptm1 = np.array(ptm1)
    Ptm2 = np.array(ptm2)

    ## Acc / Vec

    vec = Pt1 - Ptm1
    acc = Pt2 + Ptm2 - 2 * Pt0
    # print(vec.shape)
    # print(acc.shape)

    ## magnitude of vel /  and magnitude of acc
    # magvec = np.ndarray((vec.shape[0], 15), dtype=float)
    # magacc = np.ndarray((vec.shape[0], 15), dtype=float)
    # magvec = np.zeros((vec.shape[0], 15), dtype=float)
    # magacc = np.zeros((vec.shape[0], 15), dtype=float)
    magvec = np.empty((vec.shape[0], 15), np.dtype(np.float32))
    magacc = np.empty((vec.shape[0], 15), np.dtype(np.float32))

    for xf in range(0, vec.shape[0]):
        indx = 0
        for xp in range(0, 43, 3):
            pointv = vec[xf, xp:xp + 3]
            pointa = acc[xf, xp:xp + 3]
            magvec[xf][indx] = np.linalg.norm(pointv)
            magacc[xf][indx] = np.linalg.norm(pointa)
            indx = indx + 1

    ## Feature Vector
    # f_v = np.concatenate((Pt0, vec, acc), axis=1)
    f_v = np.concatenate((Pt0, magvec, magacc), axis=1)
    z = np.copy(f_v[f_v.shape[0] - 1, :])
    z = np.matlib.repmat(z, 4, 1)
    feat_vec = np.vstack((f_v, z))

    print(feat_vec.shape)
    return feat_vec, vec, acc


def smoothPlot(p3d, p3dsmooth):
        # Gaussian Smoothing - Plot ##
        fig1, ax1 = plt.subplots()

        ax1.plot(p3d[:, 3], label='Before Smooth')
        ax1.plot(p3dsmooth[:, 3], label='After Smooth')

        plt.xlabel('frames')
        plt.ylabel('X coord')
        plt.title('X coordinate before &\nafter Gaussian smoothing')
        plt.legend()
        plt.show(ax1)
        plt.close('all')

def dtwC(dist_mat, penalty):
    p, q, C, phi = dpcore.dp(dist_mat, penalty=penalty)
    return p, q, C, phi

def DistMatPlot(f_v, path, q=None, p=None,dtwscore=None, name=None, flag=None, save_flag=None):

    if save_flag == 1:

        goal_dir = os.path.join(path)
        fig, ax = plt.subplots()
        cax = ax.matshow(f_v, interpolation='None')

        ax.grid(True)
        plt.xlabel('frames')
        plt.ylabel('frames')

        if flag == 'similarity':
            fig.colorbar(cax)
            my_file = name + '_sim_mat'
            plt.title('Self Similarity Matrix\n Moving Pose Descriptor')
        elif flag == 'compare':
            fig.colorbar(cax)
            my_file = name + '_comp_mat'
            plt.title('Distance Matrix\n Comparison ' + name)
        elif flag == 'DTW':
            # ax.imshow(f_v, interpolation='nearest', cmap='binary')
            ax.hold(True)
            ax.plot(q, p, '-r')
            ax.hold(False)
            ax.autoscale(enable=True, axis='both', tight=True)
            my_file = name + '_dtw_path'
            plt.title('MP - DTW Score: '+str(dtwscore))

        plt.close('all')
        # print(goal_dir + my_file)
        fig.savefig(goal_dir + my_file, bbox_inches='tight')


    else:
        # print('Passing Plot...')
        pass

def Optimize(score):
    """
    The Munkres module provides an implementation of the Munkres algorithm
    (also called the Hungarian algorithm or the Kuhn-Munkres algorithm),
    useful for solving the Assignment Problem.
    Use it to compute the lowest cost assignment from a cost matrix.
    """
    matrix = score.copy()
    # matrix[10][10]= 100000
    # matrix[1][1]= 500000
    # matrix[6][4]= 80000000
    # matrix[6][6]= 800000
    # matrix[9][4]= 400000
    # matrix[8][8]= 10000000
    # matrix[4][4]= 1000000000
    murk = Munkres()
    indexes = murk.compute(matrix)
    # print (matrix, 'Lowest cost through this matrix:')
    total = 0

    for row, column in indexes:
        value = matrix[row][column]
        total += value
        print '(%d, %d) -> %d' % (row, column, value)
        print 'total cost: %d' % total

    return indexes

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          axs=None,
                          cbarlabel='Score',
                          cmap='jet'):
    # plt.cm.Blues
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    fig, ax = plt.subplots()
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    # print(cm)

    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    # Create colorbar
    cbar = ax.figure.colorbar(im)
    cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.3f' if normalize else '2.1f'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.ylabel(axs[1])
    plt.xlabel(axs[0])
    plt.tight_layout()

    return cbar




def move_dir(top_path, topf, childf=None):
    """
        This function moves files from a child folder to a
        parent folder inside a top folder. top-->parent-->child

        ==Inputs==

        top_path : path out of "top" folder/s
        topf : List of "top" folder/s name/s
        childf : List of "child" folder/s name/s that contains all the files
    """
    os.chdir(top_path)

    for name in topf:
        path = top_path + name

        subdir_names = childf
        filelist = os.listdir(path)
        src = []
        dstn = []

        # Make source and destenation dirs
        for f in filelist:
            dest = os.path.join(path, f)
            dstn.append(dest)
            for file in listdir(dest):
                source = os.path.join(dest, file)
                for n in subdir_names:
                    if n in file: src.append(source)
        # Move Files
        # print(src)
        for num in range(0, len(src)):
            for filename in listdir(join(dstn[num], subdir_names[0])):
                # print(filename)
                move(join(src[num], filename), join(dstn[num], ''))

        # Remove Empty dirs
        for num2 in range(0, len(src)):
            sub_folders_pathname = src[num2]
            sub_folders_list = glob.glob(sub_folders_pathname)
            for sub_folder in sub_folders_list:
                shutil.rmtree(sub_folder)

        # Rename Parent folders
        for xt in os.listdir(path):
            file_name, file_ext = os.path.splitext(xt)

            # match = re.match(r"([A-Z]+)([0-9]+)", file_name, re.I)
            # if match:
            #     items = list(match.groups())
            #
            # # f_num = items[1]
            # # f_word = items[0]

            dt_name = 'mhad'

            # print('{}_{}_{}{}'.format(dt_name,topf[0].lower(),f_word.lower(),f_num))
            new_name = '{}_{}_{}'.format(dt_name, name.lower(), file_name.lower())
            # print(os.getcwd()+'/'+topf[0]+'/'+file_name)
            os.rename((os.getcwd() + '/' + name + '/' + file_name), (os.getcwd() + '/' + name + '/' + new_name))

    print('===files moved to parent folder and parent folder is renamed===')