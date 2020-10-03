from django.shortcuts import render
from django.http import HttpResponse
import openpyxl
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as img
import statistics, math, random
matplotlib.use('Agg')
 
book = openpyxl.load_workbook('ind/Digikey Ind Cleaned.xlsx')
sheet = book['download']
 
def getDistance(featureSet1, featureSet2):
    distance = 0
    for i in range(len(featureSet1)):
        distance += (featureSet1[i] - featureSet2[i])**2
    return distance

def quantityEstimate(quantity):
    return .98 - .07*math.log(quantity)

def regressionEstimate(shield,inductance,current,quantity):
    estimate = (.79 + .2*shield + .000085*inductance + .035*current)*quantityEstimate(quantity)
    return estimate

def adjustPrice(pInitial,qInitial,qFinal):
    pFinal = pInitial * (quantityEstimate(qFinal)/quantityEstimate(qInitial))
    return pFinal

selectedFeatures = [0,0,0,0,0,0,0,0,0,0] 
 
def input(request):
    return render(request, 'ind/input.html')
 
def output(request):
    chosenShield = int(request.GET['shield'])
    chosenInductance = float(request.GET['inductance'])
    chosenCurrent = float(request.GET['current'])
    chosenVolume = int(request.GET['quantity'])
 
    similarPoints = []
    t = 1
    while len(similarPoints) < 5:
        for rowNum in range(2,sheet.max_row+1):
            shield = sheet.cell(row=rowNum,column=7).value
            inductance = sheet.cell(row=rowNum,column=9).value
            current = sheet.cell(row=rowNum,column=10).value
            volume = sheet.cell(row=rowNum,column=11).value
            price = sheet.cell(row=rowNum,column=12).value
            point = [volume,price]
            if (point not in similarPoints) and (shield==chosenShield):
                if chosenCurrent/t <= current <= chosenCurrent*t:
                    if chosenInductance/t <= inductance <= chosenInductance*t:
                        if chosenVolume/10 <= volume <= chosenVolume*5:
                            similarPoints += [point]
        t += 1

    similarPoints.sort(key = lambda x: x[1])
    u = int(round(len(similarPoints)*.3,0))
    l = int(round(len(similarPoints)*.1,0))
    similarPoints = similarPoints[l:-u]

    volumes,prices = [],[]
    for point in similarPoints:
        volumes += [point[0]]
        prices += [point[1]]

    graphQuantities = range( int(chosenVolume/10), int(chosenVolume*5), int(chosenVolume*(5-.1)/5) )
    volumes += graphQuantities
    for each in graphQuantities:
        p = regressionEstimate(chosenShield,chosenInductance,chosenCurrent,each)*random.uniform(.75,1.25)
        prices += [p]

    v = statistics.median(volumes)
    priceEstimate = round(adjustPrice(statistics.median(prices),v,chosenVolume), 2)
 
    plt.clf()
    plt.plot(volumes,prices,'bo')
    plt.plot(chosenVolume,priceEstimate,'r+',markersize=20)
    plt.xlabel('Quantity')
    plt.ylabel('Price ($)')
    plt.title('Price of Similar Parts')
    plt.savefig('ind/static/ind/graph.png')
#    image = img.imread('ind/static/ind/' + size + '.png')
#    img.imsave('ind/static/ind/chosen.png',image)

    context = {'priceEstimate': priceEstimate, 'quantity': chosenVolume, 'inductance': chosenInductance, 'shield': chosenShield, 'current': chosenCurrent}
    return render(request, 'ind/output.html', context)