import numpy as np
from Moving_Pose_Descriptor import MP_tools2 as mpt
from Moving_Pose_Descriptor import FrameWiseClassify
from Moving_Pose_Descriptor import databaseModify
from Moving_Pose_Descriptor import db_filter_window
from Moving_Pose_Descriptor import WeightedDistance as wd
from Moving_Pose_Descriptor import confmat as cfm
import cv2
import os
# from Moving_Pose_Descriptor import Threshold_Precision_Recall as tpr
import functools
# import json
from scipy.spatial.distance import pdist, squareform
# import itertools
import random

def db_construct(dtpath, landmarks_path, model_name, savefig=None):
    print("Constructing Database from files")
    """FEATURE VECTOR CALCULATION"""
    # Gaussian Filter Parameters
    sigma = 1
    w = 5  # windowSize
    t = (((w - 1) / 2) - 0.5) / sigma  # truncate

    # Feature Vector starting Frame
    StartFrame = 2  # Start from 3rd Frame's 3D coordinates

    # Subjects
    subj_name = mpt.AlpNumSorter(os.listdir(dtpath))  # List of Subjects in the directory
    # print(subj_name)

    #Num of actions in subject's path
    a, a_no_ext = mpt.list_ext(os.path.join(dtpath, subj_name[0]), 'json')
    acts = mpt.AlpNumSorter(a)
    num_of_acts = len(mpt.AlpNumSorter(a_no_ext))

    #Similarity matrix plot


    fv_all = []
    # Feature vector by subject initialiazation
    fv_subj = np.empty((len(subj_name), num_of_acts), np.dtype(np.object))

    for subj in range(0, len(subj_name)):# for every subject
        a, a_no_ext = mpt.list_ext(os.path.join(dtpath, subj_name[subj]), 'json')
        acts = mpt.AlpNumSorter(a)
        acts_no_ext = mpt.AlpNumSorter(a_no_ext)
        for act in range(0, len(acts)):  # for every action of a subject

            dataset_dir = os.path.join(dtpath, subj_name[subj], acts[act])
            # input_dir = os.path.join(landmarks_path, acts_no_ext[act]+"_ldm.json")
            input_dir = os.path.join(landmarks_path, acts_no_ext[act]+"_states_ldm.json")

            ## Load data from Json ##
            dataPoints, dataLim = mpt.load_data(input_dir, dataset_dir)

            init_frame = dataLim['limits'][0]
            last_frame = dataLim['limits'][1]

            ##### Create 3D points array #####

            p3d = mpt.Create3dPoints(init_frame, last_frame, dataPoints)

            ## Gaussian Filter 5 by 1 in time dimension

            p3d_gauss = mpt.GaussFilter3dPoints(p3d, sigma, t)

            # mpt.smoothPlot(p3d,p3d_gauss)
            #### Create Feature Vector ####

            feat_vec, vec, acc = mpt.MovPoseDescriptor(p3d_gauss, StartFrame)

            fv_all.append(feat_vec)

            # Build feature vector by subject
            fv_np = np.array(feat_vec)
            fv_subj[subj][act] = fv_np

    """DATABASE CONSTRUCTION"""
    #Construct and Save database
    database = []

    for iSubject in range(0, len(subj_name)):
        for iAction in range(0, num_of_acts):
            for iframe in range(0, len(fv_subj[iSubject][iAction])):
                dt = tuple((fv_subj[iSubject][iAction][iframe], iSubject, iAction, iframe))
                database.append(dt)

    database = np.array(database)



    np.save('newDatabase', database)

    database = database[0:-1]

    return database, fv_subj


def db_reduce(database, numofSubs, numofActs):
    print("Reducing Database in " + str(numofSubs) + " Subjects / "+ str(numofActs) + " Actions")
    numofActs = numofActs - 1
    numofSubs = numofSubs - 1
    # Reduce database to "Num" subjects "Num" Actions each
    keepframes = []
    for iframe in range(0, database.shape[0]):

        if database[iframe][1] <= numofSubs and database[iframe][2] <= numofActs:
            keepframes.append(iframe)

    data_reduced = database[keepframes]

    return data_reduced

def db_lenOfseq(database):
    print("Adding Length of Sequence for every frame in Database...")
    # Add Length of Sequence to Database
    lenOfsequence = [databaseModify.db_lengthOfSequence(database, database[iframe][1], database[iframe][2]) for iframe in range(0, database.shape[0])]
    lenOfsequence = np.array(lenOfsequence)

    database_lenofSeq = np.column_stack((database, lenOfsequence))

    return database_lenofSeq

def db_frameConfidence(database, db_test, relativeWindow, k, wvec):

    # # Assign confidence in every frame / BEST params for mhad : [ 0.93  0.9   0.1   0.45  6.  ]
    # wvec = wd.wvector(1, 0.64, 0.3)

    metric = functools.partial(wd.wdistance, wvec)
    # metric = distance.euclidean
    filter = functools.partial(db_filter_window.db_window_relative, relativeWindow)

    excl_flag = True
    confidence = []
    for iframe in range(0, db_test.shape[0]):

        if db_test[iframe][2] != db_test[iframe - 1][2]:
            excl_flag = True

        # exlude from database current subject's Action
        if excl_flag == True:
            print(db_test[iframe][1], db_test[iframe][2])
            db_exclude_act, excl_flag = databaseModify.db_exclude(database, db_test[iframe][1], db_test[iframe][2])

        # Create a new database restricted to a time window
        db = filter(db_exclude_act, db_test[iframe][3])

        frame = db_test[iframe]
        classconf = FrameWiseClassify.classifyKNN(frame[0], db, k, metric)

        confidence.append(classconf[1])

    confDatabase = np.column_stack((db_test, confidence))

    return confDatabase

def filter_byConfidence(conf_database, confidence):
    # filter frames by confidence
    keep_frames = []
    for iframe in range(0, conf_database.shape[0]):

        if conf_database[iframe][5] >= confidence:
            keep_frames.append(iframe)

    mostConf = conf_database[keep_frames]

    nSubjects = mostConf[-1, 1] + 1
    nActions = mostConf[-1, 2] + 1

    # print(nSubjects)
    # print(nActions)
    #Build Feature vector by subject with most confident frames
    fv_subj = np.zeros((nSubjects, nActions), dtype=object)

    for iSubject in range(0, nSubjects):
        for iAction in range(0, nActions):
            k = mostConf[(np.where((mostConf[:, 1] == iSubject) & (mostConf[:, 2] == iAction)))]
            k2 = []
            for inum in range(0, len(k)):
                k2.append(k[inum][0])
            k2 = np.array(k2)

            fv_subj[iSubject][iAction] = k2

    return mostConf, fv_subj

def computeDTW(fv_subj, dtpath, action_labels, sflag=None,params_dtw=None ,savefig_conf=None):

    # print(fv_subj.shape[0], fv_subj.shape[1])

    nSubjects = fv_subj.shape[0]
    nActions = fv_subj.shape[1]
    SubjectsActions = [nSubjects, nActions]

    # Subjects
    subj_name = mpt.AlpNumSorter(os.listdir(dtpath))  # List of Subjects in the directory
    subj_name = subj_name[0:nSubjects]
    print(subj_name)

    action_labels = action_labels[0: SubjectsActions[1]]
    print(action_labels)

    evmat = np.zeros((nSubjects, nSubjects), np.dtype(np.object))


    for sub in range(0, nSubjects):
        ct = 0
        for sub2 in range(0, nSubjects):

            # Subjects from subj_name list
            subject1 = subj_name[sub]
            subject2 = subj_name[ct]

            # Feature Vectors by subject
            fv_1 = fv_subj[sub]
            fv_2 = fv_subj[ct]

            ct = ct + 1
            # Create confusion matrix for every pair of subjects

            score, class_score, missclass = cfm.Conf2Subject(subject1, subject2, SubjectsActions, dtpath, fv_1, fv_2, params=params_dtw)
            evmat[sub][sub2] = score

            if sflag == 1:
                params_cmf = [score, action_labels, class_score, missclass, sflag, savefig_conf]
                cfm.cfm_savefig(subject1, subject2, params_cmf)

    return evmat

def load_images_from_folder(src , destanation_path ,conf, isub, iact):
    images = []

    # Settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    bottomLeftCornerOfText = (10, 70)
    fontScale = 1
    fontColor = (255, 0, 127)
    lineType = 2

    folder = os.listdir(src)
    folder.sort()
    last = databaseModify.db_lengthOfSequence(conf, isub, iact)
    path = folder[0:last]
    count = 0

    for filename in path:
        img = cv2.imread(os.path.join(src, filename))
        cv2.putText(img, 'Confidence: ' + str(conf[count, 5]),
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    lineType)

        # Display the image
        cv2.imshow("img", img)
        # cv2.waitKey(0)
        # Save image
        count += 1
        cv2.imwrite(os.path.join(destanation_path, str(count) + "_out.jpg"), img)

        if img is not None:
            images.append(img)

    return images

def self_similarity(fv_subj,action_labels, subject_labels, savefig=None):

    # ## Similarity Matrix ##

    for isub in range(0,len(fv_subj)):
        for iact in range(0,len(fv_subj[isub])):

            sim_f_v = squareform(pdist(fv_subj[isub][iact]))

            ## Similarity - Plot ##
            mpt.DistMatPlot(sim_f_v, savefig, name=subject_labels[isub]+'_'+action_labels[iact], flag='similarity', save_flag=1)

def classScore(conf_mat_in, nSubjects):

    confusion_matrix = conf_mat_in.copy()
    np.fill_diagonal(confusion_matrix, float('inf'))
    hits = 0
    for row in enumerate(confusion_matrix):
        answer = np.argmin(row[1], axis=0) / nSubjects
        correct = row[0] / nSubjects

        if answer == correct:
            hits += 1

    class_score = (float(hits) / confusion_matrix.shape[0]) * 100
    print "\n"
    print "Classification Score [Simple/ Multiple training Samples] \n"
    print "Class Score : %f" % class_score
    print "\n"

    return class_score

def accuracy_multipleSample(conf_mat_in, nSubjects, nActions):
    confusion_matrix = conf_mat_in.copy()

    np.fill_diagonal(confusion_matrix, float('inf'))

    perf = []  # Acc/ Prec/ Rec per class
    for classes in range(0, nActions):
        tp = 0.0
        fp = 0.0
        tn = 0.0
        fn = 0.0
        tps = 0
        for row in enumerate(confusion_matrix):

            groundtruth = (classes == row[0] / nSubjects)  # -> true/false (should)

            # correct = row[0] / nSubjects
            ind = np.argmin(row[1], axis=0)
            predict = ((ind / nSubjects) == classes)

            if groundtruth:
                if groundtruth == predict:  # (groundtruth: yes, predictor: yes)
                    tp += 1
                else:  # (groundtruth: yes, predictor: no)
                    fn += 1
            else:  # negative
                if groundtruth != predict:  # (groundtruth: no, predictor: yes)
                    fp += 1
                else:  # (groundtruth: no, predictor: no)
                    tn += 1

        acc = (tp + tn) / (tp + tn + fp + fn)
        prec = tp / (tp + fp)
        rec = tp / (tp + fn)
        tps += tp
        perf.append((acc, prec, rec))


    perClass = np.array(perf)
    perClassRound = np.round(perClass, decimals=3)
    avgPerf = np.mean(perClass, axis=0)
    F1Score = 2 * ((prec * rec) / (prec + rec))

    print "Performance per Class [Multiple Training Samples/ 1 Action repetition]\n"
    print "Action1: ", perClassRound[0, :]
    print "Action2: ", perClassRound[1, :]
    print "Action3: ", perClassRound[2, :]
    print "Action4: ", perClassRound[3, :]

    print"\n"
    print "Average performance: Acc: %.3f" % avgPerf[0], " Prec: %.3f" % avgPerf[1], "Recall: %.3f" % avgPerf[2]

    print "F1_Score: ", F1Score

    return perClass

def accuracy_oneSample(conf_mat_in, nSubjects, nActions, iterations):

    confusion_matrix = conf_mat_in.copy()

    np.fill_diagonal(confusion_matrix, float('inf'))
    class_perf = np.zeros((nActions, 4), dtype=float)
    heatmap = np.zeros((nActions, nActions))
    heatmapBinary = np.zeros(4)

    for iter in range(0, iterations):

        indices = [random.randrange(0, 8), random.randrange(9, 17), random.randrange(18, 26), random.randrange(27, 35)]
        # print "\n New random training Samples"
        # print(indices)
        # print "S%i" %(indices[0] % nSubjects)+"_a1"
        # print "S%i" %(indices[1] % nSubjects)+"_a2"
        # print "S%i" %(indices[2] % nSubjects)+"_a3"
        # print "S%i" %(indices[3] % nSubjects)+"_a4"

        for action in range(0, nActions):
            tp = 0.0
            fp = 0.0
            tn = 0.0
            fn = 0.0

            for row in enumerate(confusion_matrix):

                row_elements = row[1]
                row_index = row[0]

                # Random Elements not include the current row number
                row_rand_elements = row_elements[[indices[0] + (indices[0] == row_index) % nSubjects,
                                                  indices[1] + (indices[1] == row_index) % nSubjects,
                                                  indices[2] + (indices[2] == row_index) % nSubjects,
                                                  indices[3] + (indices[3] == row_index) % nSubjects]]

                running_class = row_index / nSubjects

                predict = np.argmin(row_rand_elements, axis=0)

                # Update Heatmap
                heatmap[running_class][predict] += 1.0

                groundtruth = (action == row_index / nSubjects)  # -> true/false (should)
                predict = (predict == action)

                if predict == groundtruth:
                    heatmapBinary[action] += predict

                # if groundtruth:
                #     if groundtruth == predict: # (groundtruth: yes, predictor: yes)
                #         tp += 1
                #     else:                      # (groundtruth: yes, predictor: no)
                #         fn += 1
                # else:  # negative
                #     if groundtruth != predict: # (groundtruth: no, predictor: yes)
                #         fp += 1
                #     else:                      # (groundtruth: no, predictor: no)
                #         tn += 1

                if groundtruth:
                    if predict:  # (groundtruth: yes, predictor: yes)
                        tp += 1
                    else:  # (groundtruth: yes, predictor: no)
                        fn += 1
                else:  # negative
                    if predict:  # (groundtruth: no, predictor: yes)
                        fp += 1
                    else:  # (groundtruth: no, predictor: no)
                        tn += 1

            acc = (tp + tn) / (tp + tn + fp + fn)
            prec = tp / (tp + fp + 0.001)
            rec = tp / (tp + fn)
            overlap = tp / (tp + fp + fn)

            class_perf[action][0] += acc
            class_perf[action][1] += prec
            class_perf[action][2] += rec
            class_perf[action][3] += overlap

    # Performance per class
    class_perf = class_perf / iter
    class_perf_round = np.round(class_perf, decimals=4)
    # Average performance
    avgPerf = np.mean(class_perf, axis=0)
    F1Score = 2 * ((avgPerf[1] * avgPerf[2]) / (avgPerf[1] + avgPerf[2]))

    print "\n"
    print "Performance per Class [1 Training Sample/ 1 Action repetition]\n"
    print "Average over " + str(iterations) + " iterations\n"

    print "Action1: ", class_perf_round[0, :]
    print "Action2: ", class_perf_round[1, :]
    print "Action3: ", class_perf_round[2, :]
    print "Action4: ", class_perf_round[3, :]

    print"\n"
    print"Average performance: Acc: %.3f" % avgPerf[0], " Prec: %.3f" % avgPerf[1], "Recall: %.3f" % avgPerf[2], "Overlap: %.3f" % avgPerf[3]

    print "\n"
    print "F1_Score: ", F1Score
    return class_perf_round, avgPerf
