import numpy as np

confusion_matrix = np.load('eval_mat_new.npy')

nSubjects = 9
nActions = 4

tp = 0.0
fp = 0.0
tn = 0.0
fn = 0.0


np.fill_diagonal(confusion_matrix, float('inf'))
# hits = 0
#
# for row in enumerate(confusion_matrix):
#     predict = np.argmin(row[1], axis=0) / nSubjects
#     correct = row[0] / nSubjects
#
#     if predict == correct:
#         tp += 1
#     elif predict != correct:
#         fn += 1
#
# accuracy = (tp + tn) / (tp + tn + fp + fn)
# precision = tp / (tp + fp)
# recall = tp / (tp + fn)

perf = []
for classes in range(0, nActions):
    for row in enumerate(confusion_matrix):

        groundtruth = (classes == row[0] / nSubjects) # -> true/false (should)

        # correct = row[0] / nSubjects
        ind = np.argmin(row[1], axis=0)
        predict = ((ind / nSubjects) == classes)

        if groundtruth:
            if groundtruth == predict: # (groundtruth: yes, predictor: yes)
                tp += 1
            else:                      # (groundtruth: yes, predictor: no)
                fn += 1
        else:  # negative
            if groundtruth != predict: # (groundtruth: no, predictor: yes)
                fp += 1
            else:                      # (groundtruth: no, predictor: no)
                tn += 1

    acc = (tp + tn) / (tp + tn + fp + fn)
    prec = tp / (tp + fp)
    rec = tp / (tp + fn)

    perf.append((acc,prec,rec))

print()