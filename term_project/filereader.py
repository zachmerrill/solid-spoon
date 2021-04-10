#!/usr/bin/env python3
from mpi4py import MPI
import numpy as np
import time

def calculate_range(rank, n, p):
    # Pigeonhole principal
    result = (n/p)
    number = 0
    # min(rank, mod(n,p)) is added to range
    if(rank < (n % p)):
        number = rank
    else:
        number = n % p
    return int((rank * result) + number)


# Start MPI
comm = MPI.COMM_WORLD
# Find process rank
my_rank = comm.Get_rank()
# Find number of processes
p = comm.Get_size()

n = 15
#n = 28143
# n = 56

file = open("lecture.txt", 'r')
#file = open("ens.matrix", 'r')
# file = open("toy_example.txt", 'r')

lines = file.readlines()
file.close()

if my_rank == 0:
    lower = 0
    upper = calculate_range(my_rank + 1, n, p)
elif my_rank != 0 and my_rank != p - 1:
    lower = calculate_range(my_rank, n, p)
    upper = calculate_range(my_rank + 1, n, p)
else:
    lower = calculate_range(my_rank, n, p)
    upper = n

# Broadcast lower starting range to other processes
lowers = []
# Also broadcast sizes
sizes = []
# We need these for allgatherv later on
for s in range(p):
    lowers.append(comm.bcast(lower, root=s))
    sizes.append(comm.bcast((upper - lower), root=s))
lowers = tuple(lowers) # Need it as a tuple
sizes = tuple(sizes) # Same here

# Synchronize for timing
comm.Barrier()
if my_rank == 0:
    start_time = time.time()

dangle = float(1/n)
a = 0.85
ee = (1-a)*(dangle*1)
array = np.full((n, n), ee, float)
for line in lines:
    l = line.split()
    if len(l) == 3:
        # if int(l[0]) < upper and int(l[0]) >= lower:
        if len(l[0]) != 0 and len(l[1]) != 0 and len(l[2]) != 0:
            if float(l[2]) == -1.0:
                array[int(l[0])] += dangle
            else:
                array[int(l[0])][int(l[1])] = (float(l[2]) * a) + ee
array = array.transpose()

r = np.zeros((n, 1))
prev_r = np.full((n, 1), dangle, float)
count = 0
while not(np.array_equal(prev_r, r)) and count < 100:
    for i in range(lower, upper):
        r[i] = np.dot(array[i], prev_r)
    comm.Allgatherv([r[lower:upper], MPI.DOUBLE], [r, sizes, lowers, MPI.DOUBLE])
    prev_r = r.copy()
    count = count + 1

# Synchronize all done
comm.Barrier()
if my_rank == 0:
    end_time = time.time()
    r = np.around(r, decimals=10)
    sortedList = sorted(((v, i) for i, v in enumerate(r)), reverse=True)
    outFile = open("out.txt", "w")
    outFile.write("Final PageRank vector:\n")
    for i, (value, index) in enumerate(sortedList):
        outFile.write("#{0} -> Site {1}, PageRank {2}\n".format(i+1, index+1, value))
    timing = "Completed in {:.3f} seconds.".format(end_time - start_time)
    print(timing)
    outFile.write(timing)
    outFile.close()

# # Ax = b
# # Each process calculates (upper - lower) amount values of the b vector and broadcasts its to the other processes
# # When calculations are complete, each process should stop and wait for others to complete.
# # When all process are done, each process should reciece all values from the others and build the new x vector.
# x = np.full((n, 1), dangle, float)
