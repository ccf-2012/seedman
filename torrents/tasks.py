from background_task import background
from seedclient import sclient as SeedClientUtil
from seedclient.models import SeedClientSetting


@background(schedule=5)
def backgroundRestatus(clientName, dbid, hashstr):
    sc = SeedClientSetting.objects.get(name=clientName)
    client = SeedClientUtil.getSeedClientObj(sc)
    if client.connect():
        client.reStatusTorrent(dbid, hashstr)
