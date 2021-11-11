from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from seedclient.humanbytes import HumanBytes
from seedclient.models import SeedClientSetting
from seedclient import sclient as SeedClientUtil
from seedclient.sclient import ActiveTorrent
from django.core import serializers


class Activities:
    def __init__(self, scname, atlist):
        self.scname = scname
        self.atlist = atlist
        self.num = len(atlist)
        self.sumup = sum(ac.upload_speed for ac in atlist)
        self.sumdown = sum(ac.download_speed for ac in atlist)
        self.sumstr = '%s 活跃， 上传 %s/s  下载 %s/s' % (
            self.num, 
            HumanBytes.format(self.sumup, True), 
            HumanBytes.format(self.sumdown, True))


def getAllClientActivitiesList():
    allClientList = []
    for sc in SeedClientSetting.objects.all():
        atScname = sc.name
        client = SeedClientUtil.getSeedClientObj(sc)
        atList = client.loadActiveTorrent()
        if atList:
            atList.sort(key=lambda x: x.added_date, reverse=True)
            allClientList.append(Activities(atScname, atList))
    return allClientList

def getAllClientList():
    allClientList = []
    for sc in SeedClientSetting.objects.all():
        atScname = sc.name
        client = SeedClientUtil.getSeedClientObj(sc)
        atList, num, sumup, sumdown  = client.loadActiveTorrent()
        allClientList += atList
    return allClientList

def getOneSclientList(sclient):
    allClientList = []
    atScname = sclient.name
    client = SeedClientUtil.getSeedClientObj(sclient)
    atList = client.loadActiveTorrent()
    if atList:
        atList.sort(key=lambda x: x.added_date, reverse=True)
        allClientList.append(Activities(atScname, atList))
    return allClientList



@login_required
def activeList(request):
    # allClientList = getAllClientListList()
    return render(request, 'activities/list.html', {
        'sclient_list': SeedClientSetting.objects.all(), 
        'refresh': True
    })

def ajaxRefreshActiveList(request, pk):
    if pk <= 0:
        return render(request, 'activities/tor_list.html', {'active_list_list':None,'refresh': False})

    sclient = get_object_or_404(SeedClientSetting, pk=pk)
    return render(request, 'activities/tor_list.html', {
        'active_list_list': getOneSclientList(sclient),
        'refresh': False
    })


def actorTableIndex(request):
    return render(request, 'activities/tablelist.html', {
        'sclient_list': SeedClientSetting.objects.all()
    })


def actorTableAjax(request):
    # https://stackoverflow.com/questions/68512707/how-to-use-ajax-with-datatable-django
    allClientList = getAllClientList()
    data = []
    for obj in allClientList:
        item = {
            'status': obj.status,
            'name': obj.name,
            'sizeStr': obj.sizeStr, 
            'size':obj.size, 
            'progress': obj.progress,
            'upspeed': obj.upload_speed,
            'upspeedStr': obj.uploadspeedStr,
            'downspeed': obj.download_speed,
            'downspeedStr': obj.downloadspeedStr,
            'tracker': obj.tracker,
            'added_date': obj.added_date.strftime("%m/%d/%Y, %H:%M:%S"),
        }
        data.append(item)
    # data = serializers.serialize('json', allClientList)
    # json = serializers.serialize('json', objects)
    # return HttpResponse(json, content_type='application/json')

    return JsonResponse({'data': data})

