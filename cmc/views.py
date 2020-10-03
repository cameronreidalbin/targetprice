from django.shortcuts import render
from django.http import HttpResponse
import openpyxl
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as img
import statistics, random, math
matplotlib.use('Agg')
 
book = openpyxl.load_workbook('cmc/Digikey CMC Cleaned.xlsx')
sheet = book['download']
 
def getDistance(i1,i2,m1,m2):
    return ( (i1-i2)**2 + (m1-m2)**2 )**(1/2)

def quantityEstimate(quantity):
    return 2.686 * quantity**(-.145)

def adjustPrice(pInitial,qInitial,qFinal):
    pFinal = pInitial * (quantityEstimate(qFinal)/quantityEstimate(qInitial))
    return pFinal

def regressionEstimate(i,m,q):
    return (.6 + .11*i + .000029*m) * quantityEstimate(q)

sizeDict = {'XS': 1680, 'S': 5544, 'M': 11262, 'L': 15960, 'XL': 28934, 'XXL': 59616}

for size in sizeDict:
    image = img.imread('staticfiles/cmc/'+size+'.png')
    img.imsave('cmc/static/cmc/'+size+'.png', image)
 
def input(request):
    return render(request, 'cmc/input.html')
 
def output(request):
    lowFrequencyProblem = request.GET['frequency']
    ic = float(request.GET['current'])
    qc = int(request.GET['quantity'])
 
    if ic < 1.25:
        size = 'XS'
    if 1.25 <= ic < 2.5:
        size = 'S'
    if 2.5 <= ic < 3:
        size = 'M'
    if 3 <= ic < 5:
        size = 'L'
    if 5 <= ic < 9:
        size = 'XL'
    if 9 <= ic:
        size = 'XXL'
    if lowFrequencyProblem == 'yes':
        if size == 'XL':
            size = 'XXL'
        if size == 'L':
            size = 'XL'   
        if size == 'M':
            size = 'L'          
        if size == 'S':
            size = 'M'
        if size == 'XS':
            size = 'S'
    mc = sizeDict[size]
 
    rowNums, similarPoints = [], []
    distanceThreshold = 0
 
    while len(rowNums) < 5:
        for rowNum in range(2,sheet.max_row+1):
            i = sheet.cell(row=rowNum,column=7).value
            m = sheet.cell(row=rowNum,column=9).value
            q = sheet.cell(row=rowNum,column=10).value
            p = sheet.cell(row=rowNum,column=11).value
            if (getDistance(i,ic,m,mc) < distanceThreshold) and (rowNum not in rowNums):
                if qc/5 <= q <= qc*2:
                    rowNums += [rowNum]
                    similarPoints += [[i,m,q,p]]
        distanceThreshold += 100

    similarPoints.sort(key=lambda x: x[3])
    u = int(round(len(similarPoints)*.3,0))
    l = int(round(len(similarPoints)*.1,0))
    similarPoints = similarPoints[l:-u]

    quantities,prices = [],[]
    for point in similarPoints:
        quantities += [point[2]]
        prices += [point[3]]

    graphQuantities = range( int(qc/5), int(qc*2), int((qc*2-qc/5)/5) )
    quantities += graphQuantities
    for each in graphQuantities:
        p = regressionEstimate(ic,mc,each)*random.uniform(.75,1.25)
        prices += [p]

    v = statistics.median(quantities)
    priceEstimate = round(adjustPrice(statistics.median(prices),v,qc),2)
 
    plt.clf()
    plt.plot(quantities,prices,'bo')
    plt.plot(qc,priceEstimate,'r+',markersize=20)
    plt.xlabel('Quantity')
    plt.ylabel('Price ($)')
    plt.title('Price of Similar Parts')
    plt.savefig('cmc/static/cmc/graph.png')
    image = img.imread('cmc/static/cmc/' + size + '.png')
    img.imsave('cmc/static/cmc/chosen.png',image)
 
    context = {'priceEstimate': priceEstimate, 'quantity': qc}
    return render(request, 'cmc/output.html', context)