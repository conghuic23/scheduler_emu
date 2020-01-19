import sys
import numpy as np
import matplotlib.pyplot as plt

MAX_INT = sys.maxsize
NICE_0_LOAD = 1024

nice_to_weight = [
    # -20
    88761,     71755,     56483,     46273,     36291,
    # -15
    29154,     23254,     18705,     14949,     11916,
    # -10
    9548,      7620,      6100,      4904,      3906,
    # -5
    3121,      2501,      1991,      1586,      1277,
    # 0
    1024,       820,       655,       526,       423,
    # 5
    335,       272,       215,       172,       137,
    # 10
    110,        87,        70,        56,        45,
    # 15
    36,        29,        23,        18,        15,
]

class CThread():
    def __init__(self, name, nice, style):
        self.name = name
        self.vruntime = 0
        self.nice = nice
        self.weight = 0
        self.real = [0]
        self.vruntime_list = [0]
        self.style= style
        self.period = 0

    def nice_2_weight(self):
        if self.nice < -20 or self.nice > 19:
            print("nice is not in range -20:19")
            sys.exit()
        nice = self.nice + 20
        self.weight = nice_to_weight[nice]



# suppose min interval is 1ms
class CScheduler():
    def __init__(self, threads, period):
        self.threads = threads
        self.current = None
        self.total_weight = 0
        self.period = period
        self.min_interv = 0.75

    def __calu_thread_weight(self):
        for idx in range(len(self.threads)):
             self.threads[idx].nice_2_weight()

    def __calu_queue_weight(self):
        total_weight = 0
        for x in self.threads:
            total_weight += x.weight
        self.total_weight = total_weight
        print("total_weight", total_weight)

    def __calu_thread_slice(self):
        min_slice = MAX_INT
        for idx in range(len(self.threads)):
            self.threads[idx].slice = self.period * self.threads[idx].weight / self.total_weight
            if self.threads[idx].slice < min_slice:
                min_slice = self.threads[idx].slice

        if min_slice < self.min_interv:
            expend_rate = self.min_interv / min_slice

            # expend period
            self.period = self.period * expend_rate
            print("new period:", self.period)
            for idx in range(len(self.threads)):
                self.threads[idx].slice = self.period * self.threads[idx].weight / self.total_weight


    def init(self):
        self.__calu_thread_weight()
        self.__calu_queue_weight()
        self.__calu_thread_slice()

    def v_2_r(self, thread, v):
        return (v/NICE_0_LOAD)*thread.weight

    def context_switch(self, t):
        current = self.current
        """
        update the vruntime for current thread
        """
        if current is not None:
            # preemptive conditions:
            #  1. total runtime period > slice
            #  2. vruntime > next thread vruntime

            self.threads[current].vruntime += t * NICE_0_LOAD / self.threads[current].weight
            self.threads[current].real.append(t + self.threads[current].real[-1])
            self.threads[current].vruntime_list.append(self.threads[current].vruntime)

        """
        pick next runable thread
        """
        # find lowest vruntime
        lowest = MAX_INT
        new = None
        for x in range(len(self.threads)):
            if self.threads[x].vruntime < lowest:
                lowest = self.threads[x].vruntime
                new = x
        '''
        # find second lowest vruntime
        sec_lowest = MAX_INT
        for x in range(len(self.threads)):
            if self.threads[x].vruntime < sec_lowest and (self.threads[x].vruntime >= lowest and x != new):
                sec_lowest = self.threads[x].vruntime
        print(sec_lowest, lowest)
        '''

        """
        start new thread
        """
        if self.current is not None and self.current != new:
            # pick the new one
            self.threads[new].real.append(self.threads[current].real[-1])
            self.threads[new].vruntime_list.append(self.threads[new].vruntime_list[-1])

        self.current = new

        t = 0
        '''
        if sec_lowest != MAX_INT:
            t = self.v_2_r(self.threads[self.current], sec_lowest - lowest)
        if t < self.min_interv:
            t = self.min_interv
        elif t > self.threads[self.current].slice:
            t = self.threads[self.current].slice
        '''
        t = self.threads[self.current].slice
        if t < self.min_interv:
            t = self.min_interv

        return t


gcc = CThread('gcc', 8, 'r--')
bigsim = CThread('bigsim', 1, 'b--')
mpeg = CThread('mpeg', 0, 'y--')

threads = [gcc, bigsim, mpeg]
bvt = CScheduler(threads, 6)
bvt.init()

run = 10
t= 0

for x in range(run):
    t = bvt.context_switch(t)
    print("step",t)

for x in threads:
    print(x.real)
    print(x.vruntime_list)
    plt.plot(x.real,x.vruntime_list,x.style,label=x.name)

plt.title('cfs')

plt.legend()
plt.grid(True)
plt.xlabel("time(ms)")
plt.ylabel("vruntime")
plt.savefig('cfs.png')





