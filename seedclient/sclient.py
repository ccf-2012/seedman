import qbittorrentapi
import transmission_rpc
import deluge_client
from seedclient.models import GuessCategory, Torrent, LocationCategory, TrackerCategory, CategorizeStep
from seedclient.torguess import GuessCategoryUtils
import urllib.parse
from abc import abstractmethod, ABCMeta
from datetime import datetime
from django.utils import timezone
import pytz
from .humanbytes import HumanBytes


def getSeedClientObj(scsetting):
    if scsetting.clienttype == 'qb':
        scobj = QbSeedClient(scsetting)
    elif scsetting.clienttype == 'tr':
        scobj = TrSeedClient(scsetting)
    elif scsetting.clienttype == 'de':
        scobj = DeSeedClient(scsetting)
    return scobj


class SeedClientBase(metaclass=ABCMeta):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def loadTorrents(self):
        pass

    @abstractmethod
    def moveTorrentData(self, categorizeConfig):
        pass

    def __init__(self, scsetting):
        self.scsetting = scsetting

    def setDbTorGuessCat(self, dbtor, cat):
        if not cat:
            return False
        findcat = GuessCategory.objects.filter(label=cat)
        if findcat:
            dbGuessCat = findcat[0]
            dbGuessCat.count += 1
            dbGuessCat.size += dbtor.size
            dbGuessCat.save()
            dbtor.guess_category = dbGuessCat
            # dbtor.categorized = 1
            return True
        return False

    def categoryLocation(self, dbtor):
        findloc = LocationCategory.objects.filter(scname=dbtor.sclient.name,
                                                  location=dbtor.location)
        if findloc:
            dbLoc = findloc[0]
        else:
            dbLoc = LocationCategory()

        dbLoc.scname = dbtor.sclient.name
        dbLoc.location = dbtor.location
        dbLoc.count += 1
        dbLoc.size += dbtor.size
        dbLoc.save()
        dbtor.location_category = dbLoc
        return True

    def categoryTracker(self, dbtor):
        findcat = TrackerCategory.objects.filter(tracker=dbtor.tracker)
        if findcat:
            dbTracker = findcat[0]
        else:
            dbTracker = TrackerCategory()

        dbTracker.tracker = dbtor.tracker
        dbTracker.count += 1
        dbTracker.size += dbtor.size
        dbTracker.save()
        dbtor.tracker_category = dbTracker
        return True

    def categorized(self, sclient, guessCategory, curLocation):
        if sclient.root_dir.endswith('/'):
            suggestDir = sclient.root_dir + guessCategory + '/'
        else:
            suggestDir = sclient.root_dir + '/' + guessCategory + '/'

        if not curLocation.endswith('/'):
            curLocation = curLocation + '/'

        return suggestDir == curLocation

    def compareParentDir(self, newDir):
        if not newDir.endswith('/'):
            newDir = newDir + '/'
        if len(self.scsetting.root_dir) == 0:
            self.scsetting.root_dir = newDir
        elif self.scsetting.root_dir.startswith(newDir) and (len(newDir) < len(
                self.scsetting.root_dir)):
            self.scsetting.root_dir = newDir

    def addDbTorrent(self, torName, torHash, torSize, torLocation, torTracker,
                     torAdded, torStatus, torCategory):
        dbtor = Torrent()
        dbtor.sclient = self.scsetting
        dbtor.name = torName
        dbtor.hash = torHash
        dbtor.size = torSize
        if torLocation.endswith('/'):
            dbtor.location = torLocation
        else:
            dbtor.location = torLocation + '/'
        # dbtor.tracker = self.abbrevTracker(torTracker)
        dbtor.tracker = torTracker
        dbtor.addedDate = torAdded
        dbtor.status = torStatus
        dbtor.origin_category = torCategory
        cat, dbtor.groupname = GuessCategoryUtils.guessByName(torName)
        self.setDbTorGuessCat(dbtor, cat)

        # if self.categorized(dbtor.sclient, dbtor.guess_category.label,
        #                     dbtor.location):
        #     dbtor.categorized = 1
        # else:
        #     dbtor.categorized = 0

        self.categoryLocation(dbtor)
        self.categoryTracker(dbtor)
        dbtor.save()
        return dbtor

    def getSavedExcludeList(self, categorizeConfig):
        qs = LocationCategory.objects.filter(
            scname=categorizeConfig.sclient.name, exclude=True)
        locationExcludeList = []
        for a in qs:
            locationExcludeList.append(a.location)
        return locationExcludeList

    def getCurrentDir(self, downloadDir):
        if downloadDir.endswith('/'):
            testDir = downloadDir
        else:
            testDir = downloadDir + '/'
        return testDir

    def generateTargetDir(self, sclient, torName):
        catDir, groupDir = GuessCategoryUtils.guessByName(torName)
        if catDir:
            targetDir = sclient.root_dir + catDir + '/'
            return targetDir
        return None

    def getMoveList(self):
        return Torrent.objects.filter(sclient__name=self.scsetting.name,
                                      categorized=0,
                                      location_category__exclude=False)

    def moveTorrentData(self, categorizeConfig):
        if not self.connect():
            return -1
        moveList = self.getMoveList()
        categorizeConfig.totalTorrentNum = len(moveList)
        categorizeConfig.currentProceedingNum = 0
        for dbTor in moveList:
            categorizeConfig.currentProceedingNum += 1
            categorizeConfig.save()
            targetDir = self.generateTargetDir(self.scsetting, dbTor.name)

            self.callRPCMove(dbTor.hash, targetDir)

            dbTor.location = targetDir
            dbTor.categorized = 1
            dbTor.location_category.count -= 1
            dbTor.location_category.save()
            self.categoryLocation(dbTor)
            dbTor.save()

        LocationCategory.objects.filter(count=0).delete()
        categorizeConfig.totalMovedNum = categorizeConfig.currentProceedingNum
        categorizeConfig.save()
        return categorizeConfig.currentProceedingNum


class TrSeedClient(SeedClientBase):
    def connect(self):
        self.trClient = None
        try:
            self.trClient = transmission_rpc.Client(
                host=self.scsetting.host,
                port=self.scsetting.port,
                username=self.scsetting.username,
                password=self.scsetting.password)
        except transmission_rpc.error.TransmissionError as e:
            print(e)
            return None

        return self.trClient

    def loadTorrents(self):
        self.scsetting.online = 2  # processing
        self.scsetting.save()
        trClient = self.connect()
        if not trClient:
            self.scsetting.online = 1
            self.scsetting.save()
            return False
        torList = trClient.get_torrents(arguments=[
            'id', 'name', 'hashString', 'downloadDir', 'totalSize', 'trackers',
            'addedDate', 'status'
        ])
        countSizeTotal = 0
        for trTor in torList:
            self.addDbTorrent(trTor.name,
                              trTor.hashString,
                              trTor.total_size,
                              trTor.download_dir,
                              self.abbrevTracker(trTor.trackers[0]),
                              trTor.date_added,
                              trTor.status,
                              torCategory='')
            countSizeTotal += trTor.total_size
        self.scsetting.num_total = len(torList)
        self.scsetting.size_total = countSizeTotal
        self.scsetting.online = 4
        self.scsetting.save()
        return True

    def abbrevTracker(self, trackerJson):
        hostnameList = urllib.parse.urlparse(
            trackerJson["announce"]).netloc.split('.')
        if len(hostnameList) == 2:
            abbrev = hostnameList[0]
        elif len(hostnameList) == 3:
            abbrev = hostnameList[1]
        else:
            abbrev = ''
        return abbrev

    def callRPCMove(self, tor_hash, targetDir):
        trTor = self.trClient.get_torrent(tor_hash)
        trTor.move_data(targetDir)
        trTor.locate_data(targetDir)

    def loadActiveTorrent(self):
        trClient = self.connect()
        if not trClient:
            return []
        torList = trClient.get_torrents(
            ids='recently-active',
            arguments=[
                'id', 'name', 'hashString', 'downloadDir', 'totalSize',
                'trackers', 'addedDate', 'status', 'percentDone', 'seeders',
                'leechers', 'rateUpload', 'rateDownload', 'uploadedEver',
                'downloadedEver'
            ])
        activeList = []
        for tor in torList:
            at = ActiveTorrent(
                tor.hashString,
                self.scsetting.name,
                tor.name,
                tor.total_size,
                tor.percentDone * 100,
                tor.rateUpload,
                tor.rateDownload,
                tor.seeders,
                tor.leechers,
                self.abbrevTracker(tor.trackers[0]),
                tor.date_added,
                tor.status,
                tor.download_dir,
                tor.uploadedEver,
                tor.downloadedEver,
            )
            activeList.append(at)
        return activeList


class QbSeedClient(SeedClientBase):
    def connect(self):
        self.qbClient = qbittorrentapi.Client(
            host=self.scsetting.host,
            port=self.scsetting.port,
            username=self.scsetting.username,
            password=self.scsetting.password,
            #   VERIFY_WEBUI_CERTIFICATE = False,
        )
        try:
            self.qbClient.auth_log_in()
        except:
            print('Error: check connection settings.')
            return None

        return self.qbClient

    def loadTorrents(self):
        self.scsetting.online = 2  # processing
        self.scsetting.save()
        qbClient = self.connect()
        if not qbClient:
            self.scsetting.online = 1
            self.scsetting.save()
            return False

        countSizeTotal = 0
        torList = qbClient.torrents_info()
        for tor in torList:
            self.addDbTorrent(
                tor.name, tor.hash, tor.size, tor.save_path,
                self.abbrevTracker(tor.tracker),
                datetime.utcfromtimestamp(
                    tor.added_on).replace(tzinfo=pytz.utc),
                tor.trackers[3]['status'], tor.category)
            countSizeTotal += tor.size

        self.scsetting.num_total = len(torList)
        self.scsetting.size_total = countSizeTotal
        self.scsetting.online = 4
        self.scsetting.save()
        return True

    def abbrevTracker(self, trackerstr):
        hostnameList = urllib.parse.urlparse(trackerstr).netloc.split('.')
        if len(hostnameList) == 2:
            abbrev = hostnameList[0]
        elif len(hostnameList) == 3:
            abbrev = hostnameList[1]
        else:
            abbrev = ''
        return abbrev

    def callRPCMove(self, tor_hash, targetDir):
        qbList = self.qbClient.torrents_info(hashs=[tor_hash])
        if len(qbList) > 0:
            qbTor = qbList[0]
            # qbTor.setCategory(GuessCategoryUtils.CATEGORIES[catstr][0])
            # qbTor.setAutoManagement(True)
            qbTor.setLocation(targetDir)

    def loadActiveTorrent(self):
        qbClient = self.connect()
        if not qbClient:
            return []
        torList = qbClient.torrents_info(status_filter='active')
        activeList = []
        for tor in torList:
            at = ActiveTorrent(
                tor.hash,
                self.scsetting.name,
                tor.name,
                tor.size,
                tor.progress * 100,
                tor.upspeed,
                tor.dlspeed,
                tor.num_seeds,
                tor.num_leechs,
                self.abbrevTracker(tor.tracker),
                datetime.utcfromtimestamp(
                    tor.added_on).replace(tzinfo=pytz.utc),
                tor.state,
                tor.save_path,
                tor.total_uploaded,
                tor.total_downloaded,
            )
            activeList.append(at)
        return activeList


class DeSeedClient(SeedClientBase):
    def connect(self):
        self.deClient = deluge_client.DelugeRPCClient(
            host=self.scsetting.host,
            port=self.scsetting.port,
            username=self.scsetting.username,
            password=self.scsetting.password)

        try:
            self.deClient.connect()
        except:
            return None
        else:
            if self.deClient.connected:
                return self.deClient
            else:
                return None

    def loadTorrents(self):
        self.scsetting.online = 2  # processing
        self.scsetting.save()
        client = self.connect()
        if not client:
            self.scsetting.online = 1
            self.scsetting.save()
            return False
        torList = client.call('core.get_torrents_status', {}, [
            'name',
            'hash',
            'download_location',
            'total_size',
            'tracker_host',
            'time_added',
            'state',
        ])
        countSizeTotal = 0
        for deTor in torList.values():
            self.addDbTorrent(
                deTor[b'name'].decode("utf-8"),
                deTor[b'hash'].decode("utf-8"),
                deTor[b'total_size'],
                deTor[b'download_location'].decode("utf-8"),
                self.abbrevTracker(deTor[b'tracker_host'].decode("utf-8")),
                datetime.utcfromtimestamp(
                    deTor[b'time_added']).replace(tzinfo=pytz.utc),
                deTor[b'state'].decode("utf-8"),
                torCategory='')
            countSizeTotal += deTor[b'total_size']
        self.scsetting.num_total = len(torList)
        self.scsetting.size_total = countSizeTotal
        self.scsetting.online = 4
        self.scsetting.save()
        return True

    def abbrevTracker(self, trackerHost):
        hostnameList = trackerHost.split('.')
        if len(hostnameList) == 2:
            abbrev = hostnameList[0]
        elif len(hostnameList) == 3:
            abbrev = hostnameList[1]
        else:
            abbrev = ''
        return abbrev

    def callRPCMove(self, tor_hash, targetDir):
        self.deClient.call('core.move_storage', [tor_hash], targetDir)

    def loadActiveTorrent(self):
        client = self.connect()
        if not client:
            return []
        torList = client.call(
            'core.get_torrents_status', {"state": "Active"}, [
                'name', 'hash', 'download_location', 'total_size',
                'tracker_host', 'time_added', 'state', 'progress', 'num_seeds',
                'num_peers', 'peers', 'total_uploaded', 'total_done'
            ])
        activeList = []
        for deTor in torList.values():
            upspeed = 0
            downspeed = 0
            if (len(deTor[b'peers']) > 0):
                for p in deTor[b'peers']:
                    upspeed += p[b'up_speed']
                    downspeed += p[b'down_speed']
            at = ActiveTorrent(
                deTor[b'hash'].decode("utf-8"),
                self.scsetting.name,
                deTor[b'name'].decode("utf-8"),
                deTor[b'total_size'],
                deTor[b'progress'],
                upspeed,
                downspeed,
                deTor[b'num_seeds'],
                deTor[b'num_peers'],
                self.abbrevTracker(deTor[b'tracker_host'].decode("utf-8")),
                datetime.utcfromtimestamp(
                    deTor[b'time_added']).replace(tzinfo=pytz.utc),
                deTor[b'state'].decode("utf-8"),
                deTor[b'download_location'].decode("utf-8"),
                deTor[b'total_uploaded'],
                deTor[b'total_done'],
            )
            activeList.append(at)
        return activeList


class ActiveTorrent(object):
    def __init__(self, torrent_hash, scname, name, size, progress,
                 upload_speed, download_speed, seeder_num, leech_num, tracker,
                 added_date, status, save_path, total_uploaded,
                 total_downloaded):
        self.torrent_hash = torrent_hash
        self.scname = scname
        self.name = name
        self.size = size
        self.sizeStr = HumanBytes.format(size, True)
        self.progress = "{:.0f}%".format(progress)
        self.upload_speed = upload_speed
        self.uploadspeedStr = HumanBytes.format(
            upload_speed, True) if upload_speed > 0 else ''
        self.download_speed = download_speed
        self.downloadspeedStr = HumanBytes.format(
            download_speed, True) if download_speed > 0 else ''
        self.seeder_num = seeder_num
        self.leech_num = leech_num
        self.tracker = tracker
        self.added_date = added_date
        self.status = status
        self.save_path = save_path
        self.total_uploaded = total_uploaded
        self.total_downloaded = total_downloaded

class Activities:
    def __init__(self, scname, atlist):
        self.scname = scname
        self.atlist = atlist
        self.num = len(atlist)
        self.sumup = sum(ac.upload_speed for ac in atlist)
        self.sumdown = sum(ac.download_speed for ac in atlist)
        self.sumstr = '%s 活跃， 上传 %s/s  下载 %s/s' % (
            self.num, HumanBytes.format(
                self.sumup, True), HumanBytes.format(self.sumdown, True))

