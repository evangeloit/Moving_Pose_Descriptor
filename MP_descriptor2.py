# MP_ :
# 1) Imports (3d) landmarks results from json
# 2) Creates an array of the (3D) landmarks
# 3) Filters all landmarks with a gaussian filter 5by1 in time dimension
# 4) Calculates Feature Vector for every given dataset
# 5) Creates a self Similarity matrix and saves it in a figure on demand (sflag)
# 6) Compares every subject vs all subjects for all actions and saves results in path

import numpy as np
from scipy.spatial.distance import pdist, squareform, cdist
import os
from Moving_Pose_Descriptor import MP_tools2 as mpt
from Moving_Pose_Descriptor import confmat as cfm
from Moving_Pose_Descriptor.heatmap import heatmap
from Moving_Pose_Descriptor.heatmap import annotate_heatmap
import matplotlib.pyplot as plt
from heatmap import heatmap
from heatmap import annotate_heatmap
from munkres import Munkres
import json

# Controllers

#Open mhad dataset jsonfile
with open(os.path.join(os.environ['mvpd'],"dataset.json")) as f:
    dataset_s1 = mpt.AlpNumSorter(list(json.load(f)))

#Paths
dtpath = '/home/evangeloit/Desktop/GitBlit_Master/PythonModel3dTracker/Data/data/'
landmarks_path = "/home/evangeloit/Desktop/GitBlit_Master/PythonModel3dTracker/Data/rs/Human_tracking/results_camera_invariant/"
# os.chdir(dtpath) # Mhad Dataset directory


model_name = 'mh_body_male_customquat'

# Actions
actions = ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10", "A11"]

# Gaussian Filter Parameters
sigma = 1
w = 5  # windowSize
t = (((w - 1) / 2) - 0.5) / sigma  # truncate

# Feature Vector starting Frame
StartFrame = 2  # Start from 3rd Frame's 3D coordinates

# sflag =  0 : Turn off plots , 1: save figures to path. Global parameter
sflag = 0

# Similarity Matrix -- save Figure path
savefig_sim = os.getcwd() + "/plots/conf_matrix/MP_sim_mat/"

# Compare one set with all the other datasets -- save Figure path
savefig_comp = os.getcwd() + "/plots/conf_matrix/MP_comp_mat/"

# DTW figures path
savefig_dtw = os.getcwd() + "/plots/conf_matrix/dtw_res_conf/"
params_dtw = [0, savefig_dtw] # sflag 0 or 1 , savefig_dtw = path to save plot /

# Confusion matrix save figures path
savefig_conf = os.getcwd() + "/plots/conf_matrix/conf/"

# 1 vs all / Average dataset performance save figs path
savefig_avg = os.getcwd() + "/plots/conf_matrix/"
params_avg = [1, savefig_avg]

fv_all = []
#Feature vector by subject initialiazation
fv_subj = np.empty((12, 11), np.dtype(np.object))

#Subjects
subj_name = mpt.AlpNumSorter(os.listdir(dtpath)) # List of Subjects in the directory
# print(subj_name)

c_score = np.empty((len(subj_name), len(subj_name)), np.dtype(np.float32)) # Classification scores totals

for subj in range(0,len(subj_name)):# for every subject
    a, a_no_ext = mpt.list_ext(os.path.join(dtpath, subj_name[subj]), 'json')
    acts = mpt.AlpNumSorter(a)
    acts_no_ext = mpt.AlpNumSorter(a_no_ext)
    for act in range(0, len(acts)):  # for every action of a subject

        dataset_dir = os.path.join(dtpath, subj_name[subj], acts[act])
        input_dir = os.path.join(landmarks_path, acts_no_ext[act]+"_ldm.json")

        ## Load data from Json ##
        dataPoints, dataLim = mpt.load_data(input_dir, dataset_dir)

        init_frame = dataLim['limits'][0]
        last_frame = dataLim['limits'][1]

        ##### Create 3D points array #####

        p3d = mpt.Create3dPoints(init_frame, last_frame, dataPoints, model_name)

        ## Gaussian Filter 5 by 1 in time dimension

        p3d_gauss = mpt.GaussFilter3dPoints(p3d, sigma, t)

        #### Create Feature Vector ####

        feat_vec, vec, acc = mpt.MovPoseDescriptor(p3d_gauss, StartFrame)

        fv_all.append(feat_vec)
        # Build feature vector by subject
        fv_np = np.array(feat_vec)
        fv_subj[subj][act] = fv_np

# Feature Vector Array for all subjects
fv_new = np.array(fv_all).copy() # Don't need to keep a copy!!!

# Feature Vector by subject

## Similarity Matrix ##
for fv in range(0, len(fv_new)):
    sim_f_v = squareform(pdist(fv_new[fv]))

    ## Similarity - Plot ##
    mpt.DistMatPlot(sim_f_v, savefig_sim, name=dataset_s1[fv], flag='similarity', save_flag=0)

ctr = 0
evmat = np.empty((12,12),np.dtype(np.object))
for sub in range(0, len(subj_name)):
    ct = 0
    for sub2 in range(0, len(subj_name)):

        #Subjects from subj_name list
        subject1 = subj_name[sub]
        subject2 = subj_name[ct]

        #Feature Vectors by subject
        fv_1 = fv_subj[sub]
        fv_2 = fv_subj[ct]

        ct = ct + 1
        ctr+=1
        print(ctr)
        #Create confusion matrix for every pair of subjects
        # if subject1 != subject2: # Take out similiraty matrixes
        #     score, class_score, missclass = cfm.Conf2Subject(subject1, subject2, dtpath, fv_1, fv_2, params=params_dtw)
        #
        #     c_score[sub][sub2] = class_score # one vs all subjects for same actions
        #
        #     if sflag == 1:
        #         params_cmf = [score, actions, class_score, missclass, sflag, savefig_conf]
        #         cfm.cfm_savefig(subject1, subject2, params_cmf)
        # else:
        #     c_score[sub][sub2] = 0

        # if subject1 != subject2: # Take out similiraty matrixes
        score, class_score, missclass = cfm.Conf2Subject(subject1, subject2, dtpath, fv_1, fv_2, params=params_dtw)
        evmat[sub][sub2] = score
        c_score[sub][sub2] = class_score # one vs all subjects for same actions

        if sflag == 1:
            params_cmf = [score, actions, class_score, missclass, sflag, savefig_conf]
            cfm.cfm_savefig(subject1, subject2, params_cmf)



# mhad_average class_score
sum_cscore = np.sum(c_score, axis=1, dtype=float)
# avg_cscore = np.divide(sum_cscore, len(subj_name)-1)
avg_cscore = np.divide(sum_cscore, len(subj_name))

np.save('evmat.npy',evmat)

# np.save('c_score.npy',c_score)
new1 = evmat[2][5]
# new2 = new1[0]

#Plots 1 vs All / Average Perforamnce to "params" path
if params_avg[0] == 1:
    cfm.avg_perf_savefig(avg_cscore, c_score, subj_name, params=params_avg)



print() ### checked WORKING till this line!!!

#Optimization -Best Assignemt -class score%

# indexes = mpt.Optimize(score)
# indexes = np.array(mpt.Optimize(score))
# truth_index = np.transpose(np.array(np.diag_indices(11)))
#
# match = 0
# for rr in range(0,indexes.shape[0]):
#         if truth_index[rr][0] == indexes[rr][0] and truth_index[rr][1] == indexes[rr][1] :
#             match = match+1
#
# print(match)
# missclass = float((indexes.shape[0] - match)/2)
# class_score = float((indexes.shape[0] -missclass)/indexes.shape[0])*100
