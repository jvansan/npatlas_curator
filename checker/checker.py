import time
import threading
import queue

class CheckerWorker(object):

    def __init__(self, queue):
        self.progress = 0
        self.queue = queue
        self.isDone = False

    def doWork(self):
        while 1:
            article = self.queue.get()
            self.processArticle(article)
            self.queue.task_done()
        self.isDone = True

    def processArticle(self, article):
        print('%d) This is an article!' % article)

myQ = queue.Queue()
_ = [myQ.put(i) for i in range(100)]

worker = CheckerWorker(myQ)

for _ in range(4):
    workThread = threading.Thread(target=worker.doWork)
    workThread.daemon = True
    workThread.start()

print('Starting')
myQ.join()
print('Done')