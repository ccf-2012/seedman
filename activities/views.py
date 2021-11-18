from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from seedclient.humanbytes import HumanBytes
from seedclient.models import SeedClientSetting, SpeedPoint, SpeedingTorrent
from seedclient import sclient as SeedClientUtil
from seedclient.sclient import Activities
from .tasks import GetSpeedingTorrentRoutine, checkTaskExists
from datetime import timedelta
from django.utils import timezone


class SpeedTrend:
    def __init__(self, tracker, stlist):
        self.tracker = tracker
        self.stlist = stlist


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


@login_required
def activeListSelect(request, pk):
    sclient = get_object_or_404(SeedClientSetting, pk=pk)
    # for one day, extensible
    timeRange = timezone.now() - timedelta(days=1)
    splistAll = SpeedPoint.objects.filter(sclient=sclient,
                                          tracker='ALL',
                                          time__gte=timeRange)
    sumStr = '上传：%s  下载：%s ' % (
        HumanBytes.format(sum(sp.sum_delta_upload for sp in splistAll), True),
        HumanBytes.format(sum(sp.sum_delta_download
                              for sp in splistAll), True),
    )

    trackerDistinctList = SpeedPoint.objects.exclude(tracker='ALL').filter(
        sclient=sclient, time__gte=timeRange).values('tracker').distinct()
    sepspList = []
    for tr in trackerDistinctList:
        sepsp = SpeedPoint.objects.filter(sclient=sclient,
                                        tracker=tr["tracker"],
                                        time__gte=timeRange)
        tsepsp = SpeedTrend(tr["tracker"], sepsp)
        sepspList.append(tsepsp)

    return render(
        request, 'activities/list.html', {
            'sclient_list': SeedClientSetting.objects.all(),
            'speed_list': splistAll,
            'cur_sclient': pk,
            'sepsp_list': sepspList,
            'sumstr': sumStr,
            'refresh': True
        })

@login_required
def ajaxRefreshActiveList(request, pk):
    if pk <= 0:
        return render(request, 'activities/tor_list.html', {
            'active_list_list': None,
            'refresh': False
        })

    sclient = get_object_or_404(SeedClientSetting, pk=pk)
    return render(request, 'activities/tor_list.html', {
        'active_list_list': getOneSclientList(sclient),
        'refresh': False
    })


@login_required
def startSpeedingTorrentTask(request):
    # allClientList = getAllClientListList()
    vname = "task_speeding_torrent"
    if not checkTaskExists(vname):
        GetSpeedingTorrentRoutine(repeat=300, verbose_name=vname)
    return JsonResponse({'Start': '60'})


# def getAllClientList():
#     allClientList = []
#     for sc in SeedClientSetting.objects.all():
#         atScname = sc.name
#         client = SeedClientUtil.getSeedClientObj(sc)
#         atList, num, sumup, sumdown  = client.loadActiveTorrent()
#         allClientList += atList
#     return allClientList

# def actorTableIndex(request):
#     return render(request, 'activities/tablelist.html', {
#         'sclient_list': SeedClientSetting.objects.all()
#     })

# def actorTableAjax(request):
#     # https://stackoverflow.com/questions/68512707/how-to-use-ajax-with-datatable-django
#     allClientList = getAllClientList()
#     data = []
#     for obj in allClientList:
#         item = {
#             'status': obj.status,
#             'name': obj.name,
#             'sizeStr': obj.sizeStr,
#             'size':obj.size,
#             'progress': obj.progress,
#             'upspeed': obj.upload_speed,
#             'upspeedStr': obj.uploadspeedStr,
#             'downspeed': obj.download_speed,
#             'downspeedStr': obj.downloadspeedStr,
#             'tracker': obj.tracker,
#             'added_date': obj.added_date.strftime("%m/%d/%Y, %H:%M:%S"),
#         }
#         data.append(item)
#     # data = serializers.serialize('json', allClientList)
#     # json = serializers.serialize('json', objects)
#     # return HttpResponse(json, content_type='application/json')

#     return JsonResponse({'data': data})
