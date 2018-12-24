import numpy as np
# from scipy.spatial import distance as dst
from Moving_Pose_Descriptor import FrameWiseClassify as FrameWiseClassify
from Moving_Pose_Descriptor import databaseModify
from Moving_Pose_Descriptor import WeightedDistance as wd
from Moving_Pose_Descriptor import db_filter_window
import functools
import time

# @filter_func function used to filter train, expecting two arguments (train, age, action)
def benchmark(train, filter_func, test, k, metric):
    nCorrect = 0.0
    score = 0.0

    for iFrame in range(0, test.shape[0]):
        # TODO: Once ids have been added to db change above line into:
        db = filter_func(train, test[iFrame][3])

        frame = test[iFrame]
        classconf = FrameWiseClassify.classifyKNN(frame[0], db, k, metric)

        if classconf[0] == frame[2]:
            nCorrect += 1
            score += classconf[1]
        else:
            score -= classconf[1]

    return (
        nCorrect / test.shape[0],
        score / test.shape[0]
    )


database = np.load("db_frame_subject_action_age.npy")

train, test = databaseModify.reduceDatabase(database, 25000, 1000)

results = []
# iRow = 0
#
# for wpos in range(1, 11):
#     for wvel in range(1, 11):
#         print("%d percent done" % (10 * wpos + wvel - 11))
#         for wacc in range(1, 11):
#             for k in range(5, 21, 5):
#                 wp = wpos * 0.1
#                 wv = wvel * 0.1
#                 wa = wacc * 0.1
#

for wsize in range(5, 1000, 5):

                print("%d percent done" % (wsize/10))

                wvec = wd.wvector(0.9, 0.1, 0.45)

                filter = functools.partial(db_filter_window.db_window, wsize)

                metric = functools.partial(wd.wdistance, wvec)

                start_time = time.time()
                result = benchmark(train, filter, test, 6, metric)

                print("--- %s seconds ---" % (time.time() - start_time))
                # exit()

                res = [result[0], wsize]
                results.append(res)


results = np.array(results)
np.save('best_windowSize.npy',results)
print()