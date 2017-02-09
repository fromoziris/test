from numpy import *
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt


# Simple structures for transmitter and receiver
# The only visible difference is  - transmitter is characterized using
# additional parameter p - transmit power
class Transmitter:
  def __init__(self, x, y, p):
    self.x = x
    self.y = y
    self.p = p

class Receiver:
  def __init__(self, x, y):
    self.x = x
    self.y = y
    
# Randomly place transmitter in a 100x100 square.
# Receiver are places around transmitters in 40x40 square    
def allocateTransmitterAndReceiver(numReceivers):
  transPosX = random.rand()*100
  transPosY = random.rand()*100
  transPower = []
  for i in xrange(numReceivers):
      transPower.append(0.1)
  receivers=[]
  for i in xrange(numReceivers):
    recPosX = transPosX + random.rand()*40
    recPosY = transPosY + random.rand()*40
    receivers.append(Receiver(recPosX, recPosY))
  return (Transmitter(transPosX, transPosY, transPower), receivers)

# Allocate a system of n transmitters and receivers    
def allocateSystem(n, numReceivers):
  transmitters = []
  receivers3 = []
  for i in xrange(n):
    tra, rec = allocateTransmitterAndReceiver(numReceivers)
    transmitters.append(tra)
    receivers3.append(rec)
  return transmitters, receivers3
  
def distance(node1, node2):
  return sqrt((node1.x-node2.x)**2 + (node1.y-node2.y)**2)  


####################################################################################################

# path loss calculation acording to ITU model for indoor propagation
# ITU-R  P.1238-7
def pathLoss(d):
  dd = d
  if d < 1:
    dd = 1
  L = 20*log10(2400)+30*log10(dd) + 14 - 28
  return 1.0/(10.0**(L/10.0))
  
# function calculates SINR for user number k
# transList - list of transmitters in a system
# recList - list of receivers in a system
# sigmaSquared - white noise power at receivers
def sinr(k, transList, recList, sigmaSquared, numReceivers):  
  interf = 0.0
  hkkz=[]
  for j in xrange(len(transList)):
    if j != k:
      for z in xrange(numReceivers):
        hjk = pathLoss(distance(transList[j], recList[k][z]))
      # kanalo perdavimo koeficientas is j-ojo k-tajam
        interf = interf + hjk*transList[j].p[z]
      interf = interf/numReceivers
      
  for z in xrange(numReceivers):
    hkk = pathLoss(distance(transList[k], recList[k][z]))
    hkkz.append(hkk*transList[k].p[z]/(interf + sigmaSquared))
  return hkkz

def systemcapacity_sinr(k, transList, recList, sigmaSquared, numReceivers):  
  interf = 0.0
  hkkz=[]
  for j in xrange(len(transList)):
    if j != k:
      for z in xrange(numReceivers):
        hjk = pathLoss(distance(transList[j], recList[k][z]))
      # kanalo perdavimo koeficientas is j-ojo k-tajam
        interf = interf + hjk*transList[j].p[z]
      interf = interf/numReceivers
      
  for z in xrange(numReceivers):
    hkk = pathLoss(distance(transList[k], recList[k][z]))
    hkkz.append(hkk*transList[k].p[z]/(interf + sigmaSquared))
  return hkkz


# calculate averge system capacity (capacity per user)  
def systemCapacity(transList, recList, sigmaSquared, numReceivers):
  c = 0
  for i in xrange(len(transList)):
    for z in xrange(numReceivers):
      c = c + log2(1+systemcapacity_sinr(i, transList, recList, sigmaSquared, numReceivers)[z])
  return c/(len(transList))

###################################################################################################

# This is somewhat simplified function for power changing for every user
# There is no any threashold of sensitivity, so it is assumed
# that every user changes its power sequentially
# as every change of power by any user results in changed SINR for any other user
# So users update there powers sequantially
# This is the most inportant function in all this simulation and
# it probably could be rewritten for other simulation scenarios
# At every step new powel configuration (new transmitters) are returned
# Names of parameters are self explaining 
def nextPowerConfigurationSequential(transList, recList, sigmaSquared, pMax, c, numReceivers):
  #pirma nukopijuokime sena transList i nauja
  newTransList = range(len(transList))
  for i in xrange(len(transList)):
    newTransList[i] = transList[i]
  
  for i in xrange(len(newTransList)):
    newPw = []
    for z in xrange(numReceivers):
      newP = 1.0/c - 1.0/sinr(i, newTransList, recList, sigmaSquared, numReceivers)[z]*newTransList[i].p[z]
      if newP <= 0:
        newP = 1e-10   #This is somewhat a hack. I dont want power of any transmitter to be exacly zero
      if newP > pMax:
        newP = pMax
      newPw.append(newP)
    newTransList[i] = Transmitter(transList[i].x, transList[i].y, newPw)
  return newTransList
  

def averageSystemCapacity(pMax, c, numUsers, numReceivers):
  sigmaSq = 1e-12
  cap = 0.0
  numSimulation = 1000
  for i in xrange(numSimulation):
    tra, rec = allocateSystem(numUsers, numReceivers) #returns [[1,2,3],[2,3,4]]...
    for iter in xrange(10):
      tra = nextPowerConfigurationSequential(tra, rec, sigmaSq, pMax, c, numReceivers)
    cap = cap + systemCapacity(tra, rec, sigmaSq, numReceivers)
  return cap/numSimulation  

# Plot graphs of power allocation for every user
# This function is esefull to assure yourself that system is really converging :)
def testSystemConvergence(pMax, c, numUsers):
  sigmaSq = 1e-12
  iterToConvergence = 1000
  powerData = zeros((numUsers, iterToConvergence+1))
  tra, rec = allocateSystem(numUsers)
  for i in xrange(numUsers):
    powerData[i][0] = tra[i].p
  print systemCapacity(tra, rec, sigmaSq)
  for iterr in xrange(iterToConvergence):
    tra = nextPowerConfigurationSequential(tra, rec, sigmaSq, pMax, c)
    for i in xrange(numUsers):
      powerData[i][iterr+1] = tra[i].p
  print systemCapacity(tra, rec, sigmaSq)
  P.figure()
  for i in xrange(numUsers):
    P.plot(powerData[i, :])
  P.show()

# change number of users and observe the change of full or average system capacity
def systemCapacityVsNumberOfUsers(c):
  numReceivers=4
  users = arange(2, 5, 1)
  cap1 = []
  cap2 = []
  cap3 = []
  cap4 = []
  cap0 = []
  _cap1 = []
  _cap2 = []
  _cap3 = []
  _cap4 = []
  _cap0 = []  
  for u in users:
    cap1.append(averageSystemCapacity(0.1, c, u, numReceivers)*u)   #multiplication by u should be removes if we are interested in
    cap0.append(averageSystemCapacity(0.2, c, u, numReceivers)*u)
    cap2.append(averageSystemCapacity(1.0, c, u, numReceivers)*u)   #averaged capacity for one user
    cap3.append(averageSystemCapacity(2.0, c, u, numReceivers)*u)
    cap4.append(averageSystemCapacity(4.0, c, u, numReceivers)*u)

    _cap1.append(averageSystemCapacity(0.1, c, u, numReceivers))   #multiplication by u should be removes if we are interested in
    _cap0.append(averageSystemCapacity(0.2, c, u, numReceivers))
    _cap2.append(averageSystemCapacity(1.0, c, u, numReceivers))   #averaged capacity for one user
    _cap3.append(averageSystemCapacity(2.0, c, u, numReceivers))
    _cap4.append(averageSystemCapacity(4.0, c, u, numReceivers))
    print u
    
##  P.figure()
##  P.plot(users, cap1, "k*-", label = "Pmax = 0.1 W")
##   P.plot(users, cap0, "k*-", label = "Pmax = 0.2 W")
##  P.plot(users, cap2, "ko-", label = "Pmax = 1 W")
##  P.plot(users, cap3, "k+-", label = "Pmax = 2 W")
##  P.plot(users, cap4, "k.-", label = "Pmax = 4 W")
##  P.legend(loc='upper left')
##  P.xlabel("Number of users")
##  P.ylabel("Full system capacity, bits/s/Hz")
##  P.show()

  fig, axes = plt.subplots(ncols=2, sharey=False)
  axes[0].plot(users, cap0, linestyle="-", linewidth=3, color='grey', label = "Pmax = 0.1 W")
  axes[0].plot(users, cap1, linestyle="-.", linewidth=3, color='grey', label = "Pmax = 0.2 W")
  axes[0].plot(users, cap2, linestyle=" ", linewidth=3, color='grey', label = "Pmax = 1 W")
  axes[0].plot(users, cap3, linestyle="--", linewidth=3, color='grey', label = "Pmax = 2 W")
  axes[0].plot(users, cap4, linestyle=":", linewidth=3, color='grey', label = "Pmax = 4 W")
  axes[0].set_title('a) Full system capacity, bits/s/Hz', fontsize=10)
  axes[0].set_xlabel('Number of users')
  axes[0].set_ylabel('Full system capacity, bits/s/Hz')
  axes[1].plot(users, _cap0, linestyle="-", linewidth=3, color='grey', label = "Pmax = 0.1 W")
  axes[1].plot(users, _cap1, linestyle="-.", linewidth=3, color='grey',  label = "Pmax = 0.2 W")
  axes[1].plot(users, _cap2, linestyle=" ", linewidth=3, color='grey',  label = "Pmax = 1 W")
  axes[1].plot(users, _cap3, linestyle="--", linewidth=3, color='grey', label = "Pmax = 2 W")
  axes[1].plot(users, _cap4, linestyle=":", linewidth=3, color='grey', label = "Pmax = 4 W")
  axes[1].set_title('b) Average Users capacity, bits/s/Hz', fontsize=10)
  axes[1].set_xlabel('Number of users')
  axes[1].set_ylabel('Average Users capacity, bits/s/Hz')
  axes[0].legend(prop={'size':10}, loc='best')
  axes[1].legend(prop={'size':10}, loc='best')
  axes[0].grid(b=True, which='major', color='k', linestyle='-')
  axes[0].minorticks_on()
  axes[1].grid(b=True, which='major', color='k', linestyle='-')
  axes[1].minorticks_on()
  
  plt.savefig('system_capacity.pdf', format='pdf', dpi=1000)

#testSystemConvergence(2, 0.5, 10)  
systemCapacityVsNumberOfUsers(0.25)










