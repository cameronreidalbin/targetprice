from django.shortcuts import render
from django.http import HttpResponse
import openpyxl
import requests,bs4,lxml
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
        distributorName = dr.get('data-distributorname')
        margin = .25
        if distributorName not in volumeDistributors:
            margin = 1
       
        partNumber = dr.select('.td-part-number > a')
        if part.upper() in partNumber[0].getText().upper():
            quotes = dr.select('.table-list > .multi-price')
           
            for q in quotes:
                if q.select('.list-right')[0].get('data-basecurrency') == 'USD':
                    quantity = int(q.select('.list-left')[0].getText())
                    price = float(q.select('.list-right')[0].get('data-baseprice')) / (1+margin)
                    points += [[quantity,price]]
   
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


 
def input(request):
    return render(request, 'pnsearch/input.html')
 


def output(request):
    #user inputs
    pn = str(request.GET['pn'])
    chosenQuantity = int(request.GET['quantity'])
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



    #plot all that bullshit    
    plt.clf()
    plt.title('Direct Price Adjusted Quotes')
    plt.xlabel('Quantity')
    plt.ylabel('Price ($)') 
    plt.plot(quantities,prices,'bo')
    plt.plot(xTrend,yTrend,'b--')
    plt.plot(chosenQuantity,priceEstimate,'r+',markerSize=20)

    plt.savefig('pnsearch/static/pnsearch/graph.png')
    context = {'priceEstimate': priceEstimate, 'quantity': chosenQuantity, 'pn': pn}
    return render(request, page, context)



