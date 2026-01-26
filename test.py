s = {10,20,30,10,40}
t = {10,50,20,70,80,100}

print(s.union(t))
print(s.intersection(t))
print(s.difference(t))
s.intersection_update(t)
print(s)
s.symmetric_difference(t)
print(s)