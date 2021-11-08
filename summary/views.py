from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from seedclient.humanbytes import HumanBytes
from seedclient.models import GuessCategory, LocationCategory, SeedClientSetting, Torrent, TrackerCategory
from ajax_datatable.views import AjaxDatatableView

from seedclient.views import initAllCategories


class summaryCatTable(AjaxDatatableView):
    model = GuessCategory
    title = '乱猜分类'
    # initial_order = [["cat_id", "asc"], ]
    column_defs = [
        {
            'name': 'cat_id',
            'visible': False,
        },
        {
            'name': 'label',
            'visible': True,
            'title': '分类',
            'searchable': False,
        },
        {
            'name': 'sizeStr',
            'visible': True,
            'title': '大小',
            'sort_field': 'size',
            'searchable': False,
        },
        {
            'name': 'count',
            'visible': True,
            'title': '数量',
            'searchable': False,
        },
    ]


@login_required
def summaryCatIndex(request):
    guessCatList = GuessCategory.objects.all()
    return render(
        request, 'summary/catlist.html', {
            'cat_data': guessCatList,
            'num_category': OverviewSumary.getNumCategory(),
            'num_torrent': OverviewSumary.getNumTorrents(),
            'size_torrent': OverviewSumary.getSizeTorrents(),
        })


class summaryTrackerTable(AjaxDatatableView):
    model = TrackerCategory
    title = '站点分类'
    initial_order = [
        ["sizeStr", "desc"],
    ]
    length_menu = [[-1], ['']]
    column_defs = [
        {
            'name': 'cat_id',
            'visible': False,
        },
        {
            'name': 'tracker',
            'visible': True,
            'title': '站点',
            'searchable': False,
        },
        {
            'name': 'size',
            'visible': False,
        },
        {
            'name': 'sizeStr',
            'visible': True,
            'title': '大小',
            'sort_field': 'size',
            'searchable': False,
        },
        {
            'name': 'count',
            'visible': True,
            'title': '数量',
            'searchable': False,
        },
    ]


@login_required
def summaryTrackerIndex(request):
    trackerList = TrackerCategory.objects.all()
    return render(request, 'summary/trackerlist.html',
                  {'cat_data': trackerList})


class summaryDirTable(AjaxDatatableView):
    model = LocationCategory
    title = '存储位置分类'
    length_menu = [[-1], ['']]
    initial_order = [
        ["scname", "asc"],
    ]
    column_defs = [
        {
            'name': 'scname',
            'visible': True,
            'title': '下载器',
            'searchable': False,
        },
        {
            'name': 'location',
            'visible': True,
            'title': '存储位置',
            'searchable': False,
        },
        # {'name': 'size', 'visible': False, },
        {
            'name': 'sizeStr',
            'visible': True,
            'title': '大小',
            'sort_field': 'size',
            'searchable': False,
        },
        {
            'name': 'count',
            'visible': True,
            'title': '数量',
            'searchable': False,
        },
    ]


@login_required
def summaryDirIndex(request):
    sclientList = SeedClientSetting.objects.all()
    return render(
        request, 'summary/dirlist.html', {
            'sc_data': sclientList,
            'num_sclient': OverviewSumary.getNumSeedClient(),
            'num_torrent': OverviewSumary.getNumTorrents(),
            'size_torrent': OverviewSumary.getSizeTorrents(),
        })


class OverviewSumary:
    def getNumCategory():
        return GuessCategory.objects.count()

    def getNumLocation():
        return LocationCategory.objects.count()

    def getNumTracker():
        return TrackerCategory.objects.count()

    def getNumSeedClient():
        return SeedClientSetting.objects.count()

    def getNumTorrents():
        catList = GuessCategory.objects.all()
        sumNum = 0
        for cat in catList:
            sumNum += cat.count
        return sumNum

    def getSizeTorrents():
        catList = GuessCategory.objects.all()
        sumSize = 0
        for cat in catList:
            sumSize += cat.size
        return HumanBytes.format(sumSize)
