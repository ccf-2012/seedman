import datetime
from django.db import models
from django import forms
from .humanbytes import HumanBytes

CLIENT_TYPES = [
    ('qb', 'qbittorrent'),
    ('tr', 'transmission'),
    ('de', 'deluge'),
]

ONLINE_STATUS = [
    (0, 'unknown'),
    (1, 'failed'),
    (2, 'loading'),
    (3, 'online'),
    (4, 'loaded'),
    (5, 'connecting'),
]


class SeedClientSetting(models.Model):
    seedclient_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="名称")
    clienttype = models.CharField(max_length=2,
                                  choices=CLIENT_TYPES,
                                  default='qb',
                                  verbose_name="类型")
    host = models.CharField(max_length=128, verbose_name="主机地址")
    port = models.IntegerField(default=8080, verbose_name="端口")
    username = models.CharField(max_length=64, verbose_name="用户名")
    password = models.CharField(max_length=64, verbose_name="密码")
    online = models.IntegerField(default=0,
                                 choices=ONLINE_STATUS,
                                 verbose_name="连接状态")
    num_total = models.BigIntegerField(default=0, verbose_name="种子数")
    size_total = models.BigIntegerField(default=0, verbose_name="种子总大小")
    num_active = models.BigIntegerField(default=0, verbose_name="活跃种子数")
    num_downloading = models.BigIntegerField(default=0, verbose_name="正在下载")
    root_dir = models.CharField(max_length=255, default='', verbose_name="存储根目录")

    class Meta:
        db_table = 'seed_client'

    def __str__(self):
        return self.name


class GuessCategory(models.Model):
    cat_id = models.BigAutoField(primary_key=True)
    label = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    count = models.IntegerField(default=0)
    location = models.CharField(max_length=255)

    def _get_size_str(self):
        return HumanBytes.format(self.size)

    sizeStr = property(_get_size_str)

    class Meta:
        db_table = 'guess_category'


class LocationCategory(models.Model):
    cat_id = models.BigAutoField(primary_key=True)
    location = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    count = models.IntegerField(default=0)
    scname = models.CharField(max_length=255)
    exclude = models.BooleanField(default=False)

    def _get_size_str(self):
        return HumanBytes.format(self.size)

    sizeStr = property(_get_size_str)

    class Meta:
        db_table = 'location_category'


class TrackerCategory(models.Model):
    cat_id = models.BigAutoField(primary_key=True)
    tracker = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    count = models.IntegerField(default=0)

    def _get_size_str(self):
        return HumanBytes.format(self.size)

    sizeStr = property(_get_size_str)

    class Meta:
        db_table = 'tracker_category'


class Torrent(models.Model):
    torrent_id = models.BigAutoField(primary_key=True)
    sclient = models.ForeignKey(SeedClientSetting, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    location = models.CharField(max_length=255)
    hash = models.CharField(max_length=255, default='')
    tracker = models.CharField(max_length=128)
    addedDate = models.DateTimeField(default=0, blank=True)
    origin_category = models.CharField(max_length=128)
    status = models.CharField(max_length=32)
    categorized = models.IntegerField(default=0)

    guess_category = models.ForeignKey(GuessCategory,
                                       on_delete=models.SET_NULL,
                                       blank=True,
                                       null=True)
    location_category = models.ForeignKey(LocationCategory,
                                          on_delete=models.SET_NULL,
                                          blank=True,
                                          null=True)
    tracker_category = models.ForeignKey(TrackerCategory,
                                         on_delete=models.SET_NULL,
                                         blank=True,
                                         null=True)

    def _get_size_str(self):
        return HumanBytes.format(self.size)

    sizeStr = property(_get_size_str)

    class Meta:
        db_table = 'torrent'

    def __str__(self):
        return self.name


class CategorizeStep(models.Model):
    catstep_id = models.BigAutoField(primary_key=True)
    sclient = models.ForeignKey(SeedClientSetting, null=True, blank=True, on_delete=models.SET_NULL)
    location_category = models.ForeignKey(LocationCategory,
                                          on_delete=models.SET_NULL,
                                          blank=True,
                                          null=True)
    totalTorrentNum = models.IntegerField(default=0)
    currentProceedingNum  = models.IntegerField(default=0)
    totalMovedNum = models.IntegerField(default=0)