from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from ajax_datatable.views import AjaxDatatableView
from seedclient.models import Torrent, LocationCategory, SeedClientSetting, CategorizeStep
from .forms import CategoryExcludeForm
from seedclient import sclient as SeedClientUtil
from background_task import background


class categorizeTable(AjaxDatatableView):
    model = Torrent
    title = 'Torrent'
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
            'foreign_field': 'sclient__name',
            'visible': True,
            'title': '下载器',
            'searchable': False,
            'autofilter': True,
        },
        {
            'name': 'name',
            'title': '名称',
            'searchable': False,
        },
        {
            'name': 'sizeStr',
            'title': '大小',
            'sort_field': 'size',
            'searchable': False,
        },
        {
            'name': 'location',
            'title': '当前存储位置',
            'searchable': False,
        },
        {
            'name': 'guess_category',
            'foreign_field': 'guess_category__label',
            'searchable': False,
            'title': '分类'
        },
        {
            'name': 'moveto',
            'placeholder': True,
            'searchable': False,
            'title': '移动到',
        },
        {
            'name': 'exclude',
            'visible': True,
            'searchable': False,
            'title': '是否排除',
        },
        {
            'name': 'categorized',
            'visible': False,
            'searchable': False,
            'title': '未归类',
        },
    ]

    def customize_row(self, row, obj):
        if obj.location is not None:
            if obj.sclient.root_dir.endswith('/'):
                row['moveto'] = obj.sclient.root_dir + obj.guess_category.label
            else:
                row['moveto'] = obj.sclient.root_dir + '/' + obj.guess_category.label
            if obj.location_category.exclude:
                row['exclude'] = '排除'
            else:
                row['exclude'] = ''
        else:
            row['moveto'] = ''
        return

    def get_initial_queryset(self, request=None):
        csList = CategorizeStep.objects.all()
        if len(csList) > 0:
            cs = csList[0]
        queryset = self.model.objects.filter(sclient__name=cs.sclient.name,
                                             categorized=0,
                                             location_category__exclude=False)
        return queryset


def saveExcludeDirs(form_dir_exclude):
    locationList = LocationCategory.objects.all()
    for loc in locationList:
        searchItem = loc.scname + ': ' + loc.location
        if searchItem in form_dir_exclude:
            loc.exclude = False
        else:
            loc.exclude = True
        loc.save()


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
            cs.sclient.root_dir = form.cleaned_data['scRootDir']
            cs.sclient.save()
            saveExcludeDirs(form.cleaned_data['dirNotExclude'])
            return redirect('cat_step2')
    form = CategoryExcludeForm()
    # form.
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


@background(schedule=0)
def backgroundProceedCategorize():
    csList = CategorizeStep.objects.all()
    if len(csList) > 0:
        catconfig = csList[0]
        c = SeedClientUtil.getSeedClientObj(catconfig.sclient)
        c.moveTorrentData(catconfig)


@login_required
def categorizeProceed(request):
    csList = CategorizeStep.objects.all()
    if len(csList) <= 0:
        return redirect('cat_step0')
    backgroundProceedCategorize(schedule=0)
    return render(request, 'categorize/step3.html', {
        'cat_progress': 0,
        'refresh': True
    })


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
