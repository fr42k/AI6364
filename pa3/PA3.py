import re
import random

class BayesianNetwork:
    def __init__(self):
        self.CPT = {'B':[[], [], .001], 'E':[[], [], .002], 'A':[['B','E'], [['t', 't'], ['t', 'f'], ['f', 't'],
        ['f', 'f']],[.95, .94, .29, .001]], 'J':[['A'], [['t'], ['f']], [.9, .05]], 'M':[['A'], [['t'], ['f']], [.7, .01]]}
        self.parents = {'B': [], 'E': [], 'A': ['B', 'E'], 'J': ['A'], 'M': ['A']}
        self.sons = {'B':['A'], 'E':['A'], 'A':['J', 'M'], 'J': [], 'M': []}

    def parse_input(self, s):
        s = s.split('][')
        ret_values = re.sub('\W+', ' ', s[0]).split()
        ret_queries = re.sub('\W+', ' ', s[1]).split()
        return ret_values, ret_queries

    def enumeration_ask(self, s):
        conditions, infers = self.parse_input(s)
        cons = {'B':'unknown', 'E':'unknown', 'A':'unknown','J':'unknown','M':'unknown'}
        status = cons.copy()
        for i in range(0, len(conditions), 2):
            cons[conditions[i]] = conditions[i + 1]
        ret = '['
        for i in infers:
            cons[i] = 't'
            t1 = self.enumeration_all(['B', 'E', 'A', 'J', 'M'], cons, status.copy())
            cons[i] = 'f'
            t2 = self.enumeration_all(['B', 'E', 'A', 'J', 'M'], cons, status.copy())
            cons[i] = 'unknown'
            ret += '<' + i + ',' + str(t1 / (t1 + t2)) + '>'
        ret += ']'
        return ret

    def enumeration_all(self, nodes, cons, status):
        if len(nodes) == 0: return 1.0
        v = nodes[0]
        par, tf, pb = self.CPT[v]
        t = 0
        f = 0
        if len(par) == 0:
            t = pb
            f = 1 - pb
        else:
            for i in range(len(tf)):
                flag = True
                for j in range(len(tf[i])):
                    if status[par[j]] != tf[i][j]:
                        flag = False
                        break
                if flag:
                    t = pb[i]
                    f = 1 - pb[i]
        if cons[v] == 'unknown':
            s1 = status.copy()
            s1[v] = 't'
            s2 = status.copy()
            s2[v] = 'f'
            return t * self.enumeration_all(nodes[1:], cons, s1) + f * self.enumeration_all(nodes[1:], cons, s2)
        elif cons[v] == 'f':
            status[v] = 'f'
            return f * self.enumeration_all(nodes[1:], cons, status)
        elif cons[v] == 't':
            status[v] = 't'
            return t * self.enumeration_all(nodes[1:], cons, status)

    def prior_sampling(self, nodes, status):
        if len(nodes) == 0: return
        sons = set()
        for s in nodes:
            if len(self.parents[s]) == 0:
                prob = self.CPT[s][2]
            else:
                prob = 0
                par, tf, pb = self.CPT[s]
                for i in range(len(tf)):
                    flag = True
                    for j in range(len(tf[i])):
                        if status[par[j]] != tf[i][j]:
                            flag = False
                            break
                    if flag:
                        prob = pb[i]
                        break
            p = random.uniform(0, 1)
            status[s] = 't' if p <= prob else 'f'
            for son in self.sons[s]: sons.add(son)
        self.prior_sampling(list(sons), status)

    def reject_sampling(self, nodes, status, cons, target):
        self.prior_sampling(nodes, status)
        flag = True
        for key in status.keys():
            if key == target:continue
            if cons[key] != 'unknown' and cons[key] != status[key]:
                flag = False
                break
        if flag == False: return 0
        if status[target] == cons[target]: return 1
        else: return 2

    def likelihood_weighting(self, nodes, status, cons, w):
        if len(nodes) == 0: return w
        sons = set()
        for s in nodes:
            prob = 0
            if len(self.parents[s]) == 0:
                prob = self.CPT[s][2]
            else:
                prob = 0
                par, tf, pb = self.CPT[s]
                for i in range(len(tf)):
                    flag = True
                    for j in range(len(tf[i])):
                        if status[par[j]] != tf[i][j]:
                            flag = False
                            break
                    if flag:
                        prob = pb[i]
                        break
            if cons[s] == 'unknown':
                p = random.uniform(0, 1)
                status[s] = 't' if p <= prob else 'f'
            else:
                status[s] = cons[s]
                w *= prob if cons[s] == 't' else 1. - prob
            for son in self.sons[s]:
                sons.add(son)
        return self.likelihood_weighting(list(sons), status, cons, w)

    def sampling(self, s, k, mode):
        conditions, infers = self.parse_input(s)
        ret = '['
        for i in infers:
            t1 = .0
            t2 = .0
            ans = .0
            for j in range(k):
                status = {'B':'unknown', 'E':'unknown', 'A':'unknown','J':'unknown','M':'unknown'}
                cons = status.copy()
                for c in range(0, len(conditions), 2):
                    cons[conditions[c]] = conditions[c + 1]
                cons[i] = 't'
                if mode == 'prior':
                    self.prior_sampling(['B','E'], status)
                    flag = True
                    cons[i] = 'unknown'
                    for key in status.keys():
                        if cons[key] != 'unknown' and cons[key] != status[key]:
                            flag = False
                    t2 += 1 if flag else 0
                    flag = True
                    cons[i] = 't'
                    for key in status.keys():
                        if cons[key] != 'unknown' and cons[key] != status[key]:
                            flag = False
                    t1 += 1 if flag else 0
                elif mode == 'reject':
                    v = self.reject_sampling(['B', 'E'], status, cons, i)
                    if v == 1:
                        t1 += 1
                        t2 += 1
                    elif v == 2:
                        t2 += 1

                elif mode == 'likelihood':
                    cons[i] = 'unknown'
                    w = self.likelihood_weighting(['B', 'E'], status, cons, 1.)
                    t2 += w
                    t1 += w if status[i] == 't' else .0
            ans = .0 if t2 == 0 else t1 / t2
            ret += '<' + i + ',' + str(ans) + '>'

        ret += ']'
        return ret

# Sample for P(b|j,m)
bn = BayesianNetwork()
print bn.enumeration_ask('[<J,t>,<M,t>][B]')
print bn.sampling('[<J,t>,<M,t>][B]', 10000, mode='prior')
print bn.sampling('[<J,t>,<M,t>][B]', 10000, mode='reject')
print bn.sampling('[<J,t>,<M,t>][B]', 10000, mode='likelihood')
