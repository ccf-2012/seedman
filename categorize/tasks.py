from seedclient.models import CategorizeStep
from seedclient import sclient as SeedClientUtil
from background_task import background


@background(schedule=0)
def backgroundProceedCategorize():
    csList = CategorizeStep.objects.all()
    if len(csList) > 0:
        catconfig = csList[0]
        c = SeedClientUtil.getSeedClientObj(catconfig.sclient)
        c.moveTorrentData(catconfig)
