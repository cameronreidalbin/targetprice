from django.shortcuts import render
from django.http import HttpResponse
import openpyxl
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as img
import statistics
matplotlib.use('Agg')
 
book = openpyxl.load_workbook('cmc/Digikey CMC Cleaned.xlsx')
sheet = book['download']
 
def getDistance(i1,i2,m1,m2,q1,q2):
    return ((i1-i2)**2 + (m1-m2)**2 + (q1-q2)**2)**(1/2)
 
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
 
    currents, mm3, quantities, prices = [], [], [], []
    distanceThreshold = 1000
 
    while len(currents) < 8:
        for rowNum in range(2,sheet.max_row+1):
            i = sheet.cell(row=rowNum,column=7).value
            m = sheet.cell(row=rowNum,column=9).value
            q = sheet.cell(row=rowNum,column=10).value
            p = sheet.cell(row=rowNum,column=11).value  
            newPoint = (i not in currents) and (m not in mm3) and (q not in quantities) 
            if getDistance(i,ic,m,mc,q,qc) < distanceThreshold and newPoint == True:
                currents += [i]
                mm3 += [m]
                quantities += [q]
                prices += [p]
        distanceThreshold += 1000
    priceEstimate = round(statistics.median(prices),2)
 
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