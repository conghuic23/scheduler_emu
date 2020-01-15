import sys
import numpy as np
import matplotlib.pyplot as plt

MAX_INT = sys.maxsize

def lcm(data_list):
    m_data = max(data_list)
    while True:
        for x in data_list:
            if m_data % x !=0 :
                break
        else:
            return m_data
        m_data += 1

class CThread():
    def __init__(self, name, weight, warp, w, style):
        self.name = name
        self.evt = 0
        self.avt = 0
        self.weight = weight
        self.m = 1/weight
        self.warp = warp
        self.w = w
        self.real = [0]
        self.evt_list = [0]
        self.style= style
        self.start = 0
        self.countdown = 0

class CScheduler():
    def __init__(self, c, threads):
        self.c = c
        self.threads = threads
        self.current = None

    def normalizing_m(self):
        acc_m = []
        for x in self.threads:
            acc_m.append(x.m)
        min_m = min(acc_m)
        for idx in range(len(self.threads)):
            self.threads[idx].m = round(self.threads[idx].m / min_m)
            print(self.threads[idx].m)

    def calu_window(self):
        acc_m = []
        for x in self.threads:
            acc_m.append(x.m)
        v_window = self.c * lcm(acc_m)

        p_window = 0
        for x in self.threads:
            p_window += round(v_window / x.m)
        return v_window, p_window

    def tick_hanlder(self, real_time):
        self.threads[self.current].countdown -= 1
        if self.threads[self.current].countdown == 0:
            self.context_switch(real_time)


    def context_switch(self, t):
        current = self.current
        """
        update the avt and evt for current thread
        """
        if current is not None:
            self.threads[current].avt += (t - self.threads[current].start) * self.threads[current].m
            self.threads[current].evt = self.threads[current].avt - (self.threads[current].w if self.threads[current].warp else 0)
            self.threads[current].real.append(t)
            self.threads[current].evt_list.append(self.threads[current].evt)
            print("current",self.threads[current].name, self.threads[current].avt,  self.threads[current].evt)

        """
        pick next runable thread
        """
        # find lowest evt
        lowest = MAX_INT
        new = None
        for x in range(len(self.threads)):
            if self.threads[x].evt < lowest:
                lowest = self.threads[x].evt
                new = x

        # find second lowest evt
        sec_lowest = MAX_INT
        for x in range(len(self.threads)):
            if self.threads[x].evt < sec_lowest and (self.threads[x].evt >= lowest and x != new):
                sec_lowest = self.threads[x].evt
        print(sec_lowest, lowest)

        """
        start new thread
        """
        if self.current is not None and self.current != new:
            # pick the new one
            self.threads[new].real.append(self.threads[current].real[-1])
            self.threads[new].evt_list.append(self.threads[new].evt_list[-1])

        self.current = new


        if sec_lowest == MAX_INT:
            count = self.c
        else:
            count = round((sec_lowest - lowest)/self.threads[self.current].m) + self.c

        self.threads[new].countdown = count
        self.threads[new].start = t
        return count
#######################################
# create threads

gcc = CThread('gcc', 0.1, False, 0, 'r--')
bigsim = CThread('bigsim', 0.3, False, 0, 'b--')

#######################################
# tick
tick = 30

#######################################
# sleep task, per 10ms

task_time=[0 for x in range(0,tick)]
task_time[5]=1
task_time[6]=1

task_time[15]=1
task_time[16]=1

mpeg = CThread('mpeg', 0.6, False, 0, 'y--')

#######################################
# create scheduler
threads = [gcc, bigsim, mpeg]
bvt = CScheduler(1, threads)
bvt.normalizing_m()

#######################################
# run tick 1ms
bvt.context_switch(0)
for x in range(1,tick):
    count = bvt.tick_hanlder(x)

#######################################
# finish
print("\nscheduler windows\n", bvt.calu_window(),
      "\n==============================\n")

for x in threads:
    print(x.real)
    print(x.evt_list)
    plt.plot(x.real,x.evt_list,x.style,label=x.name)

plt.title('bvt')

plt.legend()
plt.grid(True)
plt.savefig('bvt.png')





