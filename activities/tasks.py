from django.utils import timezone
from seedclient.models import SeedClientSetting, SpeedingTorrent, SpeedPoint
from seedclient.sclient import Activities
from seedclient import sclient as SeedClientUtil
from django.db.models import F
from background_task import background
from background_task.models import Task

def torrentMarkSpeed(at, sc):
    stors = SpeedingTorrent.objects.filter(hash=at.torrent_hash)
    if len(stors) > 0:
        stor = stors[0]
        stor.delta_uploaded = at.total_uploaded - stor.last_uploaded
        stor.last_uploaded = at.total_uploaded
        stor.delta_downloaded = at.total_downloaded - stor.last_downloaded
        stor.last_downloaded = at.total_downloaded
        stor.ttl = 1024
    else:
        stor = SpeedingTorrent(sclient=sc,
                               name=at.name,
                               size=at.size,
                               tracker=at.tracker,
                               addedDate=at.added_date,
                               status=at.status,
                               hash=at.torrent_hash,
                               last_uploaded=at.total_uploaded,
                               last_downloaded=at.total_downloaded,
                               delta_uploaded=0,
                               delta_downloaded=0,
                               ttl=1024)
    stor.save()


def addSpeedPoint(stors, sps, sc, trk):
    currTime = timezone.now()
    if len(sps) > 0:
        lastsp = sps.latest('time')
        deltaTime = (currTime - lastsp.time).total_seconds()
        sumDeltaUpload = sum(st.delta_uploaded for st in stors)
        sumUploadSpeed = sumDeltaUpload / deltaTime
        sumDeltaDownload = sum(st.delta_downloaded for st in stors)
        sumDownloadSpeed = sumDeltaDownload / deltaTime
    else:
        sumDeltaUpload = 0
        sumDeltaDownload = 0
        sumUploadSpeed = 0
        sumDownloadSpeed = 0

    sp = SpeedPoint(sclient=sc,
                    tracker=trk,
                    time=currTime,
                    sum_delta_upload=sumDeltaUpload,
                    sum_delta_download=sumDeltaDownload,
                    sum_upload_speed=sumUploadSpeed,
                    sum_download_speed=sumDownloadSpeed)
    sp.save()


def sclientMarkSpeedPoint(sc):
    stors = SpeedingTorrent.objects.filter(sclient=sc)
    sps = SpeedPoint.objects.filter(sclient=sc, tracker='ALL')
    addSpeedPoint(stors, sps, sc, 'ALL')

    trackerDistinctList = SpeedingTorrent.objects.filter(sclient=sc).values('tracker').distinct()
    for tr in trackerDistinctList:
        trstr = tr["tracker"]
        stors = SpeedingTorrent.objects.filter(sclient=sc, tracker=trstr)
        sps = SpeedPoint.objects.filter(sclient=sc, tracker=trstr)
        addSpeedPoint(stors, sps, sc, trstr)


@background(schedule=60)
def GetSpeedingTorrentRoutine():
    for sc in SeedClientSetting.objects.all():        # atScname = sc.name
        client = SeedClientUtil.getSeedClientObj(sc)
        atList = client.loadActiveTorrent()
        for at in atList:
            torrentMarkSpeed(at, sc)

        sclientMarkSpeedPoint(sc)

    SpeedingTorrent.objects.all().update(ttl=F("ttl") - 1)
    SpeedingTorrent.objects.filter(ttl__lte=0).delete()



def checkTaskExists(task_vname):
    tasks = Task.objects.filter(verbose_name=task_vname)
    return len(tasks) > 0

