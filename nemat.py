import numpy as np
import math
from Moving_Pose_Descriptor import MP_tools2 as mpt
from Moving_Pose_Descriptor.heatmap import heatmap
from Moving_Pose_Descriptor.heatmap import annotate_heatmap
import matplotlib.pyplot as plt
import os
from munkres import Munkres


# evmat = np.load('evmat_without_self.npy')
evmat = np.load('evmat.npy')
conf = np.load('eval_mat.npy')

pred_gt_conf = np.zeros((11, 11), dtype=int) # rows = predictec, cols = ground truth

# majority vote
ncorrect = 0
for iRow in range(0, 132):
    #conf[iRow][iRow] = 1000000 # remove diagonal

    answers = np.full(12, 11, dtype=int) # response per subject

    subjects = range(0, 12)
    subjects = np.setdiff1d(subjects, np.array([iRow % 12]))

    for iSubject in subjects:
        subscripts = range(iSubject, 132, 12)

        answers[iSubject] = np.argmin(conf[iRow][subscripts])

    counts = np.bincount(answers)
    answer = np.argmax(counts)
    gt = int(np.floor(iRow / 12))

    pred_gt_conf[gt][answer] += 1

    if answer == gt:
        ncorrect += 1

accuracy = float(ncorrect) / 132

precision = np.zeros(11, dtype=float)
recall    = np.zeros(11, dtype=float)
colwise = np.sum(pred_gt_conf, axis=0)

for iAction in range(0, 11):
    precision[iAction] = float(pred_gt_conf[iAction][iAction]) / colwise[iAction]
    recall[iAction]    = float(pred_gt_conf[iAction][iAction]) / 12.0

#exit()

pred_gt_conf = np.zeros((11, 11), dtype=int) # rows = predictec, cols = ground truth

# minimum of average errors
ncorrect = 0
for iRow in range(0, 132):
    #conf[iRow][iRow] = 1000000 # remove diagonal

    avg_err = np.zeros(11, dtype=float)

    # remove currect subject from comparison
    subjects = range(0, 12)
    subjects = np.setdiff1d(subjects, np.array([iRow % 12]))

    for iAction in range(0, 11):
        for iSubject in subjects:
            avg_err[iAction] += conf[iRow][iAction * 12 + iSubject]

    answer = np.argmin(avg_err)
    gt = int(np.floor(iRow / 12))

    pred_gt_conf[gt][answer] += 1

    if answer == gt:
        ncorrect += 1

accuracy = float(ncorrect) / 132

precision = np.zeros(11, dtype=float)
recall    = np.zeros(11, dtype=float)
colwise = np.sum(pred_gt_conf, axis=0)

for iAction in range(0, 11):
    precision[iAction] = float(pred_gt_conf[iAction][iAction]) / colwise[iAction]
    recall[iAction]    = float(pred_gt_conf[iAction][iAction]) / 12.0

#exit()


##
# subjects = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11","S12"]
# actions = ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10", "A11"]
# actinput = []
# goal_dir = os.getcwd() + "/plots/conf_matrix/"
#
# for act in range(0,11):
#     for act2 in range(0,11):
#         act2 = actions[act]
#         actinput.append(act2)
# subjinput = subjects*12
#
# new1 = np.empty((132, 132), dtype=float)
#
# for iRow in range(0, 132):
#     for iCol in range(0, 132):
#         iSub1 = iRow % 12
#         iAct1 = int(math.floor(iRow / 12))
#
#         iSub2 = iCol % 12
#         iAct2 = int(math.floor(iCol / 12))
#
#         new1[iRow][iCol] = evmat[iSub1][iSub2][iAct1][iAct2]



# #Global Optimum
# murk = Munkres()
# total_accuracy = 0
#
# for sub1 in range(0, 12):
#     for sub2 in range(0, 12):
#         associations = murk.compute(evmat[sub1][sub2])
#         nerrors = 0
#
#         for pairing in associations:
#             if pairing[0] != pairing[1]:
#                 nerrors += 1
#         """ Note:
#             We have to keep one pair of best associations ex. if s01a01 associates best with s02a02 then you can't
#             associate s02a02 with s01a02 or any again. """
#         # nerrors=nerrors/2
#         #Running average
#         accuracy = (11 - float(nerrors)) / 11
#         total_accuracy += (1.0/144 * accuracy) * 100
#         print(total_accuracy)
#
# # print(total_accuracy)
#


# np.save('eval_mat.npy',new1)

# axlabel = ["x","y"]  # [x,y]
# # mpt.plot_confusion_matrix(new1, classes=actions, normalize=False, title='confusion matrix', axs=axlabel)
# im, cbar = heatmap(new1, axlabel[0], axlabel[1], cmap='jet')
# plt.axes().set_aspect('auto')
# plt.tight_layout()
# plt.show()

# figname ="Conf_Matrix_Total"
# plt.imshow(new1,cmap='jet')
# plt.title("Confusion Matrix\nMhad Dataset(12 Subjects x 11 Actions)")
# plt.axes().set_aspect('auto')
# plt.xlabel("Actions")
# plt.ylabel("Actions")
# plt.savefig(goal_dir + figname)
# plt.show()


# nums = []
# for j in range(0, 132): nums.append(j)
# partial_matrix = new1[:, nums]
#
# plt.matshow(partial_matrix, fignum=200)
# plt.gca().set_aspect('auto')
# plt.savefig('filename.png', dpi=600)