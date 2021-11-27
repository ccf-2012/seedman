from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from ajax_datatable.views import AjaxDatatableView
from seedclient.models import Torrent, LocationCategory, SeedClientSetting, CategorizeStep, MoveList
from seedclient.torguess import GuessCategoryUtils
from .forms import CategoryExcludeForm
from .tasks import backgroundProceedCategorize
from activities.tasks import checkTaskExists
import os


class categorizeTable(AjaxDatatableView):
    model = MoveList
    title = 'MoveList'
    length_menu = [[
        30,
        50,
        100,
    ], [
        30,
        50,
        100,
    ]]
    # length_menu = [[-1], ['']]
    column_defs = [
        {
            'name': 'sclient',
            'foreign_field': 'torrent__sclient__name',
            'visible': True,
            'title': '下载器',
            'searchable': False,
            'autofilter': True,
        },
        {
            'name': 'name',
            'foreign_field': 'torrent__name',
            'title': '名称',
            'searchable': False,
        },
        {
            'name': 'sizeStr',
            'foreign_field': 'torrent__size',
            'title': '大小',
            # 'sort_field': 'torrent__size',
            'searchable': False,
        },
        {
            'name': 'tracker',
            'foreign_field': 'torrent__tracker',
            'visible': True,
            'title': '站点',
            'searchable': False,
            # 'choices': True,
            # 'autofilter': True,
            # 'lookup_field': '__iexact',
        },
        {
            'name': 'location',
            'foreign_field': 'torrent__location',
            'title': '当前存储位置',
            'searchable': False,
        },
        {
            'name': 'guess_category',
            'foreign_field': 'torrent__guess_category__label',
            'searchable': False,
            'title': '分类'
        },
        {
            'name': 'moveto_location',
            'searchable': False,
            'title': '移动到',
        },
    ]

    # def customize_row(self, row, obj):
    #     if obj.location is not None:
    #         if obj.sclient.root_dir.endswith('/'):
    #             row['moveto'] = obj.sclient.root_dir + obj.guess_category.label
    #         else:
    #             row['moveto'] = obj.sclient.root_dir + '/' + obj.guess_category.label
    #     else:
    #         row['moveto'] = ''
    #     return

    # def get_initial_queryset(self, request=None):
    #     csList = CategorizeStep.objects.all()
    #     if len(csList) > 0:
    #         cs = csList[0]
    #     queryset = self.model.objects.filter(sclient__name=cs.sclient.name,
    #                                          location_category__exclude=False)
    #     return queryset


def saveExcludeDirs(form_dir_exclude):
    locationList = LocationCategory.objects.all()
    for loc in locationList:
        searchItem = loc.scname + ': ' + loc.location
        if searchItem in form_dir_exclude:
            loc.exclude = False
        else:
            loc.exclude = True
        loc.save()


def generateTargetDir(rootDir, catDir):
    targetDir = os.path.join(rootDir, catDir)
    if not targetDir.endswith('/'):
        targetDir += '/'
    return targetDir

def getAllReseedTorrent(sc, torName, torSize):
    torList = Torrent.objects.filter(
        sclient=sc, name=torName, size=torSize, location_category__exclude=False)
    return torList


def generateMoveList(cateStep):
    MoveList.objects.all().delete()
    moveByTrackerList = cateStep.trackList.split(',')
    for tor in Torrent.objects.filter(sclient=cateStep.sclient,
                                      location_category__exclude=False,
                                      tracker__in=moveByTrackerList):
        reseedTorList = getAllReseedTorrent(cateStep.sclient, tor.name, tor.size)
        for reseedTor in reseedTorList:
            if not MoveList.objects.filter(torrent=reseedTor).exists():
                ml = MoveList()
                ml.torrent = reseedTor
                ml.moveto_location = generateTargetDir(cateStep.root_dir, tor.tracker)
                ml.save()

    for tor in Torrent.objects.filter(sclient=cateStep.sclient,
                                      location_category__exclude=False):
        if not MoveList.objects.filter(torrent=tor).exists():
            ml = MoveList()
            ml.torrent = tor
            catDir, groupDir = GuessCategoryUtils.guessByName(tor.name)
            ml.moveto_location = generateTargetDir(cateStep.root_dir, catDir)
            ml.save()


@login_required
def categorizeStep0(request):
    CategorizeStep.objects.all().delete()
    sclientList = SeedClientSetting.objects.all()
    return render(request, 'categorize/step0.html',
                  {'sclient_list': sclientList})


@login_required
def categorizeStep0Select(request, pk):
    sclient = get_object_or_404(SeedClientSetting, pk=pk)
    cs = CategorizeStep()
    cs.sclient = sclient
    cs.save()

    return redirect('cat_step1')


@login_required
def categorizeStep1(request):
    csList = CategorizeStep.objects.all()
    if len(csList) <= 0:
        return redirect('cat_step0')
    cs = csList[0]
    if request.method == "POST":
        form = CategoryExcludeForm(request.POST)
        if form.is_valid():
            cs.root_dir = form.cleaned_data['scRootDir']
            cs.save()
            saveExcludeDirs(form.cleaned_data['dirNotExclude'])
            cs.trackList = ','.join(form.cleaned_data['trackerSelect'])
            cs.save()
            generateMoveList(cs)
            return redirect('cat_step2')
    form = CategoryExcludeForm()

    return render(request, 'categorize/step1.html', {
        'form': form,
        'scname': cs.sclient.name
    })


@login_required
def categorizeStep2(request):
    csList = CategorizeStep.objects.all()
    if len(csList) <= 0:
        return redirect('cat_step0')
    cs = csList[0]
    dir_noex = ''
    for locItem in LocationCategory.objects.filter(scname=cs.sclient.name):
        if not locItem.exclude:
            dir_noex += locItem.location + '; '

    return render(request, 'categorize/step2.html', {
        'scname': cs.sclient.name,
        'dir_notexclude': dir_noex
    })

@login_required
def categorizeProceed(request):
    csList = CategorizeStep.objects.all()
    if len(csList) <= 0:
        return redirect('cat_step0')

    vname = "proceed_categorize"
    if not checkTaskExists(vname):
        backgroundProceedCategorize(schedule=0, verbose_name=vname)
    return render(request, 'categorize/step3.html', {
        'cat_progress': 0,
        'refresh': True
    })

@login_required
def refreshProgress(request):
    csList = CategorizeStep.objects.all()
    if len(csList) <= 0:
        return render(request, 'categorize/progress.html', {
            'progress_text': '这是个意外',
            'cat_progress': 100,
        })
    if csList[0].totalTorrentNum <= 0:
        return render(request, 'categorize/progress.html', {
            'progress_text': '稍等一下，马上开始',
            'cat_progress': 0,
        })
    cs = csList[0]
    progress = cs.currentProceedingNum / cs.totalTorrentNum * 100
    progress_text = ' {} / {} '.format(cs.currentProceedingNum,
                                       cs.totalTorrentNum)

    return render(request, 'categorize/progress.html', {
        'progress_text': progress_text,
        'cat_progress': progress,
    })
