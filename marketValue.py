import sys
import getopt
import requests
import itertools
import json
import ast
import os
from progress.bar import IncrementalBar
from gsheetManager import updateMods, updatePrimeParts
from time import sleep

URL = "https://api.warframe.market/v1"

def getItemList():
    r = requests.get(URL+"/items")
    return r.json()
#itemList = [item for item in itertools.islice(getItemList()['payload']['items'],0,100)]
itemList = getItemList()['payload']['items']

def calcOrders(orders, name):
    maxPlatB = -1
    maxPlatS = -1
    minPlatB = 9999999
    minPlatS = 9999999
    avgPlatB = 0
    avgPlatS = 0
    numOfItemB = 0
    numOfItemS = 0
    with IncrementalBar('Calculating price of {}'.format(name), max=len(orders), ) as bar:
        for order in orders:
            if order['order_type'] == 'buy':
                plat = order['platinum']
                quant = order['quantity']
                avgPlatB += plat*quant
                numOfItemB += quant
                if minPlatB > plat: minPlatB = plat
                if maxPlatB < plat: maxPlatB = plat
            if order['order_type'] == 'sell':
                plat = order['platinum']
                quant = order['quantity']
                avgPlatS += plat*quant
                numOfItemS += quant
                if minPlatS > plat: minPlatS = plat
                if maxPlatS < plat: maxPlatS = plat
            bar.next()
    try:
        avgPlatB /= numOfItemB
        avgPlatS /= numOfItemS
    except:
        avgPlatB = 0
        avgPlatS = 0
    bar.finish()
    return maxPlatB, maxPlatS, minPlatB, minPlatS, avgPlatB, avgPlatS

def getItemInfo(itemName,set):
    path = 'data/parts/'+itemName+'.json'
    if set: path = 'data/'+itemName+'.json'
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return ast.literal_eval(f.read())
    else:
        link = URL + '/items/' + itemName
        success = False
        while not success:
            if set:
                try:
                    itemset = requests.get(link).json()['payload']['item']         
                    with open(path,'w', encoding="utf-8") as f:
                        f.write(str(itemset))
                    items = itemset['items_in_set']
                    for item in items:
                        path = 'data/parts/'+item['url_name']+'.json'
                        with open(path,'w', encoding="utf-8") as f:
                            f.write(str(item))
                    success = True
                    return itemset
                except json.decoder.JSONDecodeError as e:
                    sleep(0.2)
            else:
                try:
                    itemset = requests.get(link).json()['payload']['item']
                    items = itemset['items_in_set']
                    for item in items:
                        path = 'data/parts/'+item['url_name']+'.json'
                        with open(path,'w', encoding="utf-8") as f:
                            f.write(str(item))
                        if item['url_name'] == itemName:
                            success = True
                            return item
                except json.decoder.JSONDecodeError as e:
                    sleep(0.2)

                    
                    
            

def getItems(tag):
    list = []
    if not os.path.exists('data'):
        os.mkdir('data')
        os.mkdir('data/parts')
    with IncrementalBar('Processing', max=len(itemList)) as bar:
        for each in itemList:
            items = getItemInfo(each['url_name'], True)['items_in_set']
            for item in items:
                for tags in item['tags']:
                    if tags == tag:
                        success = False
                        while not success:
                            try:
                                orders = requests.get(URL+'/items/'+item['url_name']+'/orders').json()['payload']['orders']
                                maxPlatB, maxPlatS, minPlatB, minPlatS, avgPlatB, avgPlatS = calcOrders(orders,item['en']['item_name'])
                                item['maxPlatB'] = maxPlatB
                                item['maxPlatS'] = maxPlatS
                                item['minPlatB'] = minPlatB
                                item['minPlatS'] = minPlatS
                                item['avgPlatB'] = avgPlatB
                                item['avgPlatS'] = avgPlatS
                                if item not in list:
                                    list.append(item)
                                success = True
                            except json.decoder.JSONDecodeError as e:
                                success = False
                                sleep(0.5)
            bar.next()
    return list




if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            opts, args = getopt.getopt(sys.argv[1:],"mp",["mods","primes"])
        except getopt.GetoptError:
            print('marketValue.py -m -p')
            sys.exit(2)
        for opt, args in opts:
            if opt in ("-m", "--mods"):
                s = ast.literal_eval(str(getItems('mod')))
                rows = []
                for item in s:
                    rows.append([item['en']['item_name'], item['maxPlatB'], item['maxPlatS'], item['minPlatB'], item['minPlatS'], item['avgPlatB'], item['avgPlatS']])
                updateMods(rows)
            elif opt in ("-p", "--primes"):
                s = ast.literal_eval(str(getItems('prime')))
                rows = []
                for item in s:
                    rows.append([item['en']['item_name'], item['maxPlatB'], item['maxPlatS'], item['minPlatB'], item['minPlatS'], item['avgPlatB'], item['avgPlatS']])
                updatePrimeParts(rows)
    else: print("-p (--primes), -m (--mods)")
    print(sys.argv[1:])