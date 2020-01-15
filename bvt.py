import sys
import numpy as np
import matplotlib.pyplot as plt

MAX_INT = sys.maxsize

class CThread():
    def __init__(self, name, weight, warp, w, style):
        self.name = name
        self.evt = 0
        self.avt = 0
        self.weight = weight
        self.m = int(7/weight)
        self.warp = warp
        self.w = w
        self.real = [0]
        self.evt_list = [0]
        self.style= style

class CScheduler():
    def __init__(self, c, threads):
        self.c = c
        self.threads = threads
        self.current = None

    def context_switch(self, t):
        current = self.current
        print("switch to",current, t)
        if current is not None:
            self.threads[current].avt += t * self.threads[current].m
            self.threads[current].evt = self.threads[current].avt - (self.threads[current].w if self.threads[current].warp else 0)
            self.threads[current].real.append(t + self.threads[current].real[-1])
            self.threads[current].evt_list.append(self.threads[current].evt)
            print("current",self.threads[current].name, self.threads[current].avt,  self.threads[current].evt)

        # find lowest evt
        lowest = MAX_INT
        new = None
        for x in self.threads:
            if x.evt < lowest:
                lowest = x.evt
                new = self.threads.index(x)

        if self.current is not None and self.current != new:
            # pick the new one
            self.threads[new].real.append(self.threads[current].real[-1])
            self.threads[new].evt_list.append(self.threads[new].evt_list[-1])

        self.current = new

        # find second lowest evt
        sec_lowest = MAX_INT
        for x in self.threads:
            if x.evt < sec_lowest and x.evt > lowest:
                sec_lowest = x.evt

        if sec_lowest == MAX_INT:
            t = self.c
        else:
            t = round((sec_lowest - lowest)/self.threads[self.current].m) + self.c
        return t


gcc = CThread('gcc', 0.2, False, 0, 'r--')
bigsim = CThread('bigsim', 0.3, False, 0, 'b--')
mpeg = CThread('mpeg', 0.5, False, 0, 'y--')

threads = [gcc, bigsim, mpeg]
bvt = CScheduler(2, threads)

run = 20
t= 0

for x in range(run):
    t = bvt.context_switch(t)
    print("step",t)

for x in threads:
    print(x.real)
    print(x.evt_list)
    plt.plot(x.real,x.evt_list,x.style,label=x.name)

plt.title('bvt')

plt.legend()
plt.grid(True)
plt.savefig('bvt.png')





