# -*- coding: utf-8 -*-
"""
Created on Sat Nov 25 13:31:52 2015

@author: NathanLvzs
"""

from zhihu import Question
from zhihu import Answer
from zhihu import User
from zhihu import Collection
from crawluser import QuestionTopic
import multiprocessing as mp
from datetime import datetime
import sys
import os
import Queue
import time
import requests


# control parameters, change them accordingly
# ===========================================================
# number of processes
processNum = 12
# names of files containing question id
filenames = ['data/question_Process-'+str(x) for x in range(2, 6)]
# filenames = ['data/question_test']# for test
# ===========================================================


def crawlTopic(queue, equeue):
    pname = mp.current_process().name
    fh_topic = open('data/topic/topic_' + pname, 'w')
    emptyCnt = 0
    while True:
        try:
            task = queue.get(False)
            emptyCnt = 0
        except Queue.Empty as inst:
            emptyCnt += 1
            if(emptyCnt >= 240):
                print '%s %s while loop breaks\n' % (str(datetime.now()), pname)
                break
            else:
                time.sleep(50.0 / 1000)
                continue
        print "%s %s question: %s\n" % (str(datetime.now()), pname, task)

        otherErrCnt, flagbreak = 0, False
        while True:
            try:
                qtopic = QuestionTopic(task)
                break
            except requests.ConnectionError as inst:
                print ("%s: " % pname) + repr(inst)
                otherErrCnt = 0
                time.sleep(50.0 / 1000)
                continue
            except: # try 5 times, if all failed, add to error queue and move on...
                print "%s: other error when processing question %s" % (pname, task) + str(sys.exc_info()) + '\n'
                otherErrCnt += 1
                if otherErrCnt < 5:
                    time.sleep(otherErrCnt * 30.0 / 1000)
                    continue
                else:
                    equeue.put(task)# add to the error queue
                    queue.task_done()
                    print "%s: stopped %s, already maximum attempts" % (pname, task) + '\n'
                    flagbreak = True
                    break
        if flagbreak:
            continue
        # write to file
        fh_topic.write(qtopic.tostring() + '\n')
        # mark the taskitem as done
        queue.task_done()
        time.sleep(10.0 / 1000)
    fh_topic.close()
    print "%s %s finished.\n" % (str(datetime.now()), pname)
    return

def mainTopic():
    print "---%s start loading data ---" % str(datetime.now())
    if not os.path.exists('data/topic'):
        os.makedirs('data/topic')
    start_time = time.time()
    qidset = set()
    for fname in filenames:
        with open(fname, 'r') as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.replace('\n', '')
                seps = line.split('\t')
                map(lambda x: qidset.add(x), seps[1:])
    print 'number of distinct elements: %s' % len(qidset)
    print("---%s elapsed %s seconds ---" % (str(datetime.now()), time.time() - start_time))

    print "---%s start crawling ---" % str(datetime.now())
    start_time = time.time()
    manager = mp.Manager()
    taskqueue = mp.JoinableQueue()
    errorItemQueue = mp.Queue()# collect error items
    map(lambda x: taskqueue.put(x, False), qidset)

    # multiprocessing
    processes = [mp.Process(target=crawlTopic, args=(taskqueue, errorItemQueue)) for x in range(0, processNum)]
    # start processes
    for p in processes:
        p.start()
    # wait until all the items in taskqueue are processed
    taskqueue.join()
    # terminate processes
    for p in processes:
        p.join()
    # output error items, if any
    if not errorItemQueue.empty():
        with open('data/topic/topicerrors', 'w') as tempFH:
            while not errorItemQueue.empty():
                tempFH.write(errorItemQueue.get() + '\n')

    print("---%s elapsed %s seconds ---" % (str(datetime.now()), time.time() - start_time))

def check():
    print "---%s start loading data ---" % str(datetime.now())
    if not os.path.exists('data/topic'):
        os.makedirs('data/topic')
    start_time = time.time()
    qidset = set()
    for fname in filenames:
        with open(fname, 'r') as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.replace('\n', '')
                seps = line.split('\t')
                map(lambda x: qidset.add(x), seps[1:])
    print 'number of distinct elements: %s' % len(qidset)
    print("---%s elapsed %s seconds ---" % (str(datetime.now()), time.time() - start_time))

    crawledset = set()
    topicfilenames = ['data/topic/topic_Process-'+str(x) for x in range(2, 14)]
    for fname in topicfilenames:
        with open(fname, 'r') as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.replace('\n', '')
                seps = line.split('\t', 1)
                crawledset.add(seps[0])
    print 'number of crawled elements: %s' % len(crawledset)

    interset = qidset.intersection(crawledset)
    print 'number of common elements: %s' % len(interset)

    uncrawledset = qidset.difference(interset)
    print 'number of uncrawled elements: %s' % len(uncrawledset)
    print uncrawledset

if __name__ == '__main__':
    mainTopic()
    # check()
