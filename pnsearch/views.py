from django.shortcuts import render
from django.http import HttpResponse
import openpyxl
import requests,bs4,lxml
import os
import re
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.image as img
import matplotlib
matplotlib.use('Agg')



def grabPrices(pn):
    part = str(pn)
    res = requests.get('http://www.oemstrade.com/search/' + str(part))
    soup = bs4.BeautifulSoup(res.text, 'lxml')
    points = []
   
    distributorResults = soup.select('.distributor-results')      
    for dr in distributorResults:

        volumeDistributors = ['Arrow Electronics','Avnet Americas','Avnet Europe','Avnet Asia','Future Electronics','C1C Co., Ltd.']
        onlineDistributors = ['Mouser Electronics','Digi-Key','Newark','Farnell']
        brokers = ['C1C Co., Ltd.','LCSC']
        distributorName = dr.get('data-distributorname')
        margin = 0
        if distributorName in volumeDistributors:
            margin = 1
        if distributorName in onlineDistributors:
            margin = 1.25

        if distributorName not in brokers:
            WurthPNs = ['744','742','750','760','768']
            if pn[0:3] in WurthPNs:
                margin += .75
       
            partNumber = dr.select('.td-part-number > a')
            if part.upper().replace('-','') in partNumber[0].getText().upper().replace('-',''):
                quotes = dr.select('.table-list > .multi-price')
           
                for q in quotes:
                    if q.select('.list-right')[0].get('data-basecurrency') == 'USD':
                        quantity = int(q.select('.list-left')[0].getText())
                        price = float(q.select('.list-right')[0].get('data-baseprice'))
                        adjustedPrice = price / (1+margin)
                        points += [[quantity,adjustedPrice,distributorName,price]]
   
    return points



def findBestPrices(points,chosenQuantity):
    points.sort(key = lambda x: x[0])
    currentLowest = 999
    quantities,prices = [],[]

    for p in points:
        if p[0] <= chosenQuantity*1.5:
            if p[1] <= currentLowest:
                quantities += [p[0]]
                prices += [p[1]]
                currentLowest = p[1]
            else:
                quantities += [p[0]]
                prices += [currentLowest]

    return quantities,prices



def createPowerTrendLine(quantities,prices,chosenQuantity):    
    #y = ax^b
    #ln(y) = b*(ln(x)) + ln(a)
    logQuantities,logPrices = [],[]
    for q in quantities:
        logQuantities += [np.log(q)]  
    for p in prices:
        logPrices += [np.log(p)]
    x,y = [],[]
   
    b,lna = np.polyfit(logQuantities,logPrices,1)
    a = np.exp(lna)
    x,y = [],[]

    for i in range(1,int(chosenQuantity*1.5),int(chosenQuantity/100)):
        x += [i]
        y += [a*(i**b)]
   
    priceEstimate = round(a*(chosenQuantity**b),3)
   
    return x,y,priceEstimate



def getBournsCross(pn):
    part = str(pn)
    html = 'https://www.bourns.com/xref-search-results?PART='+part+'&ST=BeginsWith'
    try:
        res = requests.get(html)
        soup = bs4.BeautifulSoup(res.text, 'lxml')
        crossText = soup.find(id="C002_lblLinkText").getText()
        crossRegex = re.compile('equivalent is (.*)')
        cross = crossRegex.search(crossText).group(1)
        return cross
    except:
        return None



def plotStuff(pn,chosenQuantity,color):
    points = grabPrices(pn)
    quantities,prices = findBestPrices(points,chosenQuantity)

    if len(quantities) <= 1:
        xTrend,yTrend,priceEstimate = [],[],0
        extraX,extraY = [],[]
        page = 'pnsearch/output - error no data.html'

    if len(quantities) > 1:
        xTrend,yTrend,priceEstimate = createPowerTrendLine(quantities,prices,chosenQuantity)
        extraX, extraY = [],[]
        for i in range(len(xTrend)):
            if i%int(len(xTrend)/5) == 0 and xTrend[i]<25000:
                extraX += [xTrend[i]]
                extraY += [yTrend[i]*random.uniform(.8,1.2)]
        page = 'pnsearch/output.html'

    plt.plot(quantities,prices,c=color,ls='None',marker='o')
    plt.plot(xTrend,yTrend,c=color,ls='--',marker='None',label=pn)
    plt.plot(chosenQuantity,priceEstimate,c=color,marker='+',markerSize=20)
    return page,priceEstimate

 
def input(request):
    return render(request, 'pnsearch/input.html')
 


def output(request):
    #user inputs
    pn = str(request.GET['pn'])
    chosenQuantity = int(request.GET['quantity'])
    magneticsCrosses = int(request.GET['magneticsCrosses'])
    if chosenQuantity < 100:
        graphQuantity = 100
    else:
        graphQuantity = chosenQuantity

    plt.clf()
    plt.title('Direct Price Adjusted Quotes')
    plt.xlabel('Quantity')
    plt.ylabel('Price ($)') 
    page,pnPrice = plotStuff(pn,graphQuantity,'red')

    if magneticsCrosses == 1:
        bournsCross = getBournsCross(pn)
        if bournsCross != None:
            plotStuff(bournsCross,chosenQuantity,'blue') 

    plt.legend(loc='best')
    plt.ylim(0)

    plt.savefig('pnsearch/static/pnsearch/graph.png')
    context = {'quantity': graphQuantity, 'pn': pn, 'pnPrice': pnPrice}
    return render(request, page, context)



