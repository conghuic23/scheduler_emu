import sys
import numpy as np
import matplotlib.pyplot as plt

MIN_INT = -sys.maxsize
CREDIT_INIT = 10000000 # ns
CREDIT_MIN = 500000 # ns

"""
Credit for each unit is the same: MILLISECS(10)
Weight for each unit is equal to domain's weight: svc->weight = svc->sdom->weight
Weight for a domain is CSCHED2_DEFAULT_WEIGHT 256

budget for a dom is sdom->tot_budget = (CSCHED2_BDGT_REPL_PERIOD * op->u.credit2.cap)
budget for each unit is dynamic grub from buget pool of dom.
period for all the dom is the same and equal to  CSCHED2_BDGT_REPL_PERIOD 10ms

run for how long:
    1) run until the uint's credit=0
    2) run until credit ~= next unit's credit,  rt_credit = snext->credit - swait->credit;
        t = rt_credit * weight / max_weight
    3) do not expend the budget
        time = snext->budget < time ? snext->budget : time;
    4) not short than min (0.5ms) or longer than max (10ms)



"""

class Cdomain():
    def __init__(self):
        self.name = "domain"
        self.cap = cap
        self.budget = 0
        self.weight = weight
        self.period = period


class CThread():
    def __init__(self, name, weight, cap, style):
        self.name = name
        self.credit = CREDIT_INIT
        self.budget = 0
        self.cap = cap
        self.weight = weight
        self.residual = 0
        self.period = 10 #ms
        self.real= [0]
        self.credit_list = [CREDIT_INIT]
        self.style= style

    def init(self):
        self.budget = self.period * self.cap


# suppose min interval is 1ms
class CScheduler():
    def __init__(self, threads):
        self.threads = threads
        self.current = None
        self.max_weight = 0
        self.min_interv = 0.5 * 1000000 #ns

    def __find_max_weight(self):
        max_weight = 0
        for x in self.threads:
            if x.weight > max_weight:
                max_weight = x.weight
        self.max_weight = max_weight

    def __c2t(self, thread, credit):
        return credit * thread.weight / self.max_weight

    def __t2c(self, thread, t):
        return t * self.max_weight / thread.weight

    def reset_credit(self, t):
        for idx in range(len(self.threads)):
            if self.threads[idx].credit < 0:
                while self.threads[idx].credit < 0:
                    self.threads[idx].credit += CREDIT_INIT
            else:
                self.threads[idx].credit += CREDIT_INIT
            if self.threads[idx].credit > CREDIT_INIT + CREDIT_MIN: # 10 + 0.5 ms
                self.threads[idx].credit = CREDIT_INIT + CREDIT_MIN
            elif self.threads[idx].credit < CREDIT_MIN:
                self.threads[idx].credit = CREDIT_MIN

            self.threads[idx].real.append(t)
            self.threads[idx].credit_list.append(self.threads[idx].credit)
            print("reset !!!!!",self.threads[idx].name, self.threads[idx].credit)

    def init(self):
        self.__find_max_weight()

    def context_switch(self, t):
        current = self.current
        """
        update the credit for current thread
        """
        if current is not None:
            # preemptive conditions:
            #  1. total runtime period > slice
            #  2. credit > next thread credit

            self.threads[current].credit -= self.__t2c(self.threads[current], t)
            #self.threads[current].credit -= self.__t2c(self.threads[current], t) + self.threads[current].residual
            #self.threads[current].residual = t / self.threads[current].weight
            self.threads[current].real.append(t + self.threads[current].real[-1])
            self.threads[current].credit_list.append(self.threads[current].credit)
            print(self.threads[current].name, self.threads[current].credit)

        """
        pick next runable thread
        """
        # find lowest credit
        largest = MIN_INT
        new = None
        for x in range(len(self.threads)):
            if self.threads[x].credit > largest:
                largest = self.threads[x].credit
                new = x

        """
        reset credit if next credit <= 0
        """
        reset = 0
        if self.threads[new].credit <= 0:
            # pass current time to it
            self.reset_credit(self.threads[current].real[-1])
            reset = 1

        if reset == 1:
            # find lowest credit
            largest = MIN_INT
            new = None
            for x in range(len(self.threads)):
                if self.threads[x].credit > largest:
                    largest = self.threads[x].credit
                    new = x

        # find second largest credit
        sec_largest = MIN_INT
        for x in range(len(self.threads)):
            print(largest, self.threads[x].credit)
            if self.threads[x].credit > sec_largest and (self.threads[x].credit <= largest and x != new):
                sec_lowest = self.threads[x].credit

        """
        start new thread
        """
        if reset !=1 and self.current is not None and self.current != new:
            # pick the new one
            self.threads[new].real.append(self.threads[current].real[-1])
            self.threads[new].credit_list.append(self.threads[new].credit_list[-1])


        self.current = new


        """
        caculate timer interval
        """
        t = 0
        if sec_largest != MIN_INT:
            t = self.__c2t(self.threads[self.current], largest - sec_largest)
        if t < self.min_interv:
            t = self.min_interv
        elif t > CREDIT_INIT + CREDIT_MIN:
            t = CREDIT_INIT + CREDIT_MIN

        return t


gcc = CThread('gcc', 171, 0, 'r--')
bigsim = CThread('bigsim', 512, 0, 'b--')
mpeg = CThread('mpeg', 1024, 0,  'y--')

threads = [gcc, bigsim, mpeg]
bvt = CScheduler(threads)
bvt.init()

run = 80
t= 0

for x in range(run):
    t = bvt.context_switch(t)
    print("step",t)

for x in threads:
    print(x.real)
    print(x.credit_list)
    x_axis = [a/1000000 for a in x.real]
    plt.plot(x_axis,x.credit_list,x.style,label=x.name)

plt.title('credit2')

plt.legend()
plt.grid(True)
plt.xlabel("time(ms)")
plt.ylabel("Credit")
plt.savefig('credit.png')





