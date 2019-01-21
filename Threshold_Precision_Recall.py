import numpy as np
# import os
import matplotlib.pyplot as plt
#from sklearn.preprocessing import normalize
from Moving_Pose_Descriptor import ThresPR as classify

# conf_1 = np.load('eval_mat.npy')
# conf = normalize(conf_1, norm='max')
# conf = conf_1 / np.amax(conf_1)

def precision_recall(conf_not,subjects, actions, actions_labels, save_fig_tpr=None):

    conf = conf_not / np.amax(conf_not)#_not normalized
    act_thres_pres_rec = np.zeros((actions, 21, 4), dtype=float)
    # total =(tstep[0]/tstep[1]) + 1

    for label in range(0, actions):
        for t in range(0, 21):
            thres = 0.05 * t

            tp = 0.0
            fp = 0.0
            tn = 0.0
            fn = 0.0

            for iSubject in range(0, subjects):
                for iAction in range(0, actions):
                    answer = classify.belongsto(iSubject, iAction, subjects, label, thres, conf)

                    if answer: # positive
                        if iAction == label:
                            tp += 1
                        else:
                            fp += 1
                    else: # negative
                        if iAction != label:
                            tn += 1
                        else:
                            fn += 1

                    precision = tp / (tp + fp + 0.001)
                    recall    = tp / (tp + fn + 0.001)
                    fpr = fp / (fp + tn + 0.001)
                    Accuracy = (tp + tn) / (tp + tn + fp + fn + 0.001)
                    act_thres_pres_rec[label][t][0] = precision
                    act_thres_pres_rec[label][t][1] = recall
                    act_thres_pres_rec[label][t][2] = fpr
                    act_thres_pres_rec[label][t][3] = Accuracy
                    # print('Action : ',label,
                    #       ' Thres: ',thres,' Accuracy : ',act_thres_pres_rec[label][t][3])


    # Plots
    actions_labels = actions_labels[0:actions]
    thresp = np.linspace(0, 1, 21)

    # TODO: put the directory out of the function
    # goal_dir = os.getcwd() + "/plots/conf_matrix/thres_prec_rec/"

    if save_fig_tpr[0] == 1:
        goal_dir = save_fig_tpr[1]

        for iAction in range(0, actions):
            # create new graph
            recs = []
            precs = []
            fp = []
            acc = []
            for iThres in range(0, 21):
                # add act_thres_pres_rec[iAction][iThres][0/1] to graph
                    r = [act_thres_pres_rec[iAction][iThres][1]]
                    recs.extend(r)
                    p = [act_thres_pres_rec[iAction][iThres][0]]
                    precs.extend(p)
                    f = [act_thres_pres_rec[iAction][iThres][2]]
                    fp.extend(f)
                    ac = [act_thres_pres_rec[iAction][iThres][3]]
                    acc.extend(ac)

            # plt.plot(thresp, recs, linestyle='-', marker='o', color='b', label='recall')
            # plt.plot(thresp, precs, linestyle='-', marker='o', color='g', label='precision')
            # # plt.plot(fp, recs, linestyle='--', marker='o', color='r', label='ROC')
            # plt.plot(thresp, acc, linestyle='-', marker='*', color='m', label='Accuracy')

            fig2, ax2 = plt.subplots()
            ax2.plot(thresp, recs, linestyle='-', marker='o', color='b', label='recall')
            ax2.plot(thresp, precs, linestyle='-', marker='o', color='g', label='precision')
            # ax.plot(fp, recs, linestyle='--', marker='o', color='r', label='ROC')
            ax2.plot(thresp, acc, linestyle='-', marker='*', color='m', label='Accuracy')

            # plt.xlabel('Threshold')
            # plt.ylabel('Precision/Recall')
            # plt.legend(loc='upper right')
            # plt.title("Action: " + actions_labels[iAction] + "\nTHRES: 0:1:0.05")
            # plt.savefig(goal_dir + actions_labels[iAction])


            ax2.set_title("Action: " + actions_labels[iAction] + "\nTHRES: 0:1:0.05")
            ax2.set_xlabel('Threshold')
            ax2.set_ylabel('Precision/Recall')
            ax2.set_aspect(aspect='auto')
            fig2.tight_layout()
            fig2.savefig(goal_dir + actions_labels[iAction])

