from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.generic.edit import UpdateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from .models import SeedClientSetting, SpeedPoint, Torrent, GuessCategory, LocationCategory, TrackerCategory, SpeedingTorrent
from .forms import SeedClientForm

from .torguess import GuessCategoryUtils
from seedclient import sclient as SeedClientUtil
from background_task import background
from activities.tasks import GetSpeedingTorrentRoutine, checkTaskExists
from background_task.models import Task


def initAllCategories():
    GuessCategory.objects.all().delete()
    LocationCategory.objects.all().delete()
    TrackerCategory.objects.all().delete()

    tcat = GuessCategoryUtils()
    for cat in tcat.CATEGORIES.keys():
        gc = GuessCategory()
        gc.label = tcat.CATEGORIES[cat][0]
        gc.count = 0
        gc.size = 0
        gc.save()

def initSpeedingTables():
    SpeedingTorrent.objects.all().delete()
    SpeedPoint.objects.all().delete()


def killAllBackgroupTasks():
    Task.objects.all().delete()

def removeEmptyCategories():
    GuessCategory.objects.filter(count=0).delete()


def fixSclientPath(sclient):
    if not sclient.root_dir.endswith('/'):
        sclient.root_dir = sclient.root_dir + '/'
        sclient.save()


@background(schedule=0)
def backgroundLoadSeedClientToDatabase():
    Torrent.objects.all().delete()
    initAllCategories()

    sclientList = SeedClientSetting.objects.all().order_by("pk")
    for sc in sclientList:
        fixSclientPath(sc)
        c = SeedClientUtil.getSeedClientObj(sc)
        c.loadTorrents()
    removeEmptyCategories()


def isSomethingLoading():
    loadingCount = SeedClientSetting.objects.filter(online=2).count()
    return (loadingCount > 0)


@login_required
def sclientListView(request):
    pageItems = SeedClientSetting.objects.all()

    return render(request, 'seedclient/list.html', {
        'sclient_list': pageItems,
        'refresh': isSomethingLoading()
    })


def testSeedClientConnection(scsetting):
    sc = SeedClientUtil.getSeedClientObj(scsetting)
    r = sc.connect()
    return not (r is None)


@login_required
def sclientConnectionTest(request):
    check_id = int(request.GET.get('id'))
    sc = get_object_or_404(SeedClientSetting, seedclient_id=check_id)
    if testSeedClientConnection(sc):
        sc.online = 3
    else:
        sc.online = 1
    sc.save()
    pageItems = SeedClientSetting.objects.all()
    return render(request, 'seedclient/sclist.html', {
        'sclient_list': pageItems,
        'refresh': isSomethingLoading()
    })


@login_required
def loadSclientTorrents(request):
    killAllBackgroupTasks()
    vname = "task_loadtorrent"
    backgroundLoadSeedClientToDatabase(schedule=0, verbose_name=vname)
    # loadSeedClientToDatabase.now()

    vname = "task_speeding_torrent"
    initSpeedingTables()
    GetSpeedingTorrentRoutine(repeat=300, verbose_name=vname)
    sclientList = SeedClientSetting.objects.all()
    for sc in sclientList:
        sc.online = 0  # waiting
        sc.save()
    return render(request, 'seedclient/list.html', {
        'sclient_list': sclientList,
        'refresh': True
    })


def refreshSeedClientList(request):
    sclist = SeedClientSetting.objects.all()
    return render(request, 'seedclient/sclist.html', {'sclient_list': sclist})


@method_decorator(login_required, name='dispatch')
class SeedClientAddView(CreateView):
    model = SeedClientSetting
    template_name = 'seedclient/create.html'
    form_class = SeedClientForm
    success_url = reverse_lazy('sc_list')


def validatePostedData(request):
    newsc = request.POST.copy()
    if not newsc["root_dir"].endswith('/'):
        newsc["root_dir"] = newsc["root_dir"] + '/'
    request.POST = newsc
    return


def validateFormData(form):
    if not form.cleaned_data['root_dir'].endswith('/'):
        form.cleaned_data['root_dir'] = form.cleaned_data['root_dir'] + '/'
    return


def seedClientAddFunc(request):
    if request.method == "POST":
        form = SeedClientForm(request.POST)
        if form.is_valid():
            validatePostedData(request)
            form2 = SeedClientForm(request.POST)
            form2.save()
            return redirect('sc_list')
    form = SeedClientForm()
    return render(request, 'seedclient/create.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class SeedClientUpdateView(UpdateView):
    model = SeedClientSetting
    template_name = 'seedclient/update.html'
    form_class = SeedClientForm
    success_url = reverse_lazy('sc_list')


def seedClientUpdateFunc(request, pk, template_name='seedclient/update.html'):
    sclient = get_object_or_404(SeedClientSetting, pk=pk)
    form = SeedClientForm(request.POST or None, instance=sclient)
    if form.is_valid():
        validatePostedData(request)

        form2 = SeedClientForm(request.POST, instance=sclient)
        form2.save()
        return redirect('sc_list')
    return render(request, template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class SeedClientDeleteView(DeleteView):
    model = SeedClientSetting
    template_name = 'seedclient/delete.html'
    success_url = reverse_lazy('sc_list')
