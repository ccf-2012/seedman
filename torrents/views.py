import re
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
# from django.views import generic
from django.conf import settings
from django.views.generic.list import ListView
from seedclient.humanbytes import HumanBytes
from seedclient.models import Torrent, GuessCategory, TrackerCategory
from django.db.models import Q
from ajax_datatable.views import AjaxDatatableView


class TableView(AjaxDatatableView):
    # https://github.com/morlandi/django-ajax-datatable
    model = Torrent
    title = 'Torrent'
    initial_order = [
        ["addedDate", "desc"],
    ]
    length_menu = [[
        30,
        50,
        100,
    ], [
        30,
        50,
        100,
    ]]
    search_values_separator = '+'
    # latest_by = 'addedDate'
    # show_date_filters = True
    # show_column_filters = False
    table_row_id_fieldname = 'torrent_id'

    # size_choices = (('<1GB', '1GB'), ('<10GB', '10GB'), ('<50GB', '50GB'))
    # site_choices = []
    # for site in TrackerCategory.objects.all():
    #     site_choices += tuple((site.tracker, site.tracker))
    # cat_choices = []
    # for cat in GuessCategory.objects.all():
    #     if cat.count > 0:
    #         a = (cat.label, cat.label)
    #         cat_choices.append(a)

    column_defs = [
        # AjaxDatatableView.render_row_tools_column_def(),
        {
            'name': 'torrent_id',
            'visible': False,
        },
        {
            'name': 'name',
            'visible': True,
            'title': '标题',
            'searchable': True,
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
            'name': 'guess_category',
            'foreign_field': 'guess_category__label',
            'choices': True,
            'autofilter': True,
            'visible': True,
            'title': '分类'
        },
        {
            'name': 'addedDate',
            'visible': True,
            'title': '加入时间',
            'searchable': False,
        },
        {
            'name': 'tracker',
            'visible': True,
            'title': '站点',
            'choices': True,
            'autofilter': True,
        },
        {
            'name': 'sclient',
            'foreign_field': 'sclient__name',
            'visible': True,
            'title': '下载器',
            'choices': True,
            'autofilter': True,
        },
        {
            'name': 'location',
            'visible': True,
            'title': '存储位置',
            'choices': True,
            'autofilter': True,
        },
        {
            'name': 'trackerlink',
            'placeholder': True,
            'visible': True,
            'title': '原站查找',
            'searchable': False,
            'orderable' : False,
        },
        {
            'name': 'groupname',
            'title': '组',
            'choices': True,
            'autofilter': True,
        },
        {
            'name': 'hash',
            'visible': False,
            'title': 'hash',
            'searchable': False,
            'orderable' : False,
        },
        {
            'name': 'status',
            'visible': True,
            'title': '状态',
            'choices': True,
            'autofilter': True,
        },
    ]

    # column_defs = [
    #     # AjaxDatatableView.render_row_tools_column_def(),
    #     {'name': 'torrent_id', 'visible': False, },
    #     {'name': 'name', "width": "55%", 'visible': True, 'title': '标题',  'searchable': True, },
    #     # {'name': 'size', 'visible': False, },
    #     {'name': 'sizeStr', "width": "5%",'visible': True, 'title': '大小', 'searchable': False, },
    #     {'name': 'guess_category', "width": "7%",'foreign_field': 'guess_category__label', 'choices':True, 'autofilter':True, 'visible': True, 'title': '分类'},
    #     {'name': 'addedDate', "width": "6%",'visible': True, 'title': '加入时间',  'searchable': False,  },
    #     {'name': 'tracker', "width": "5%", 'visible': True, 'title': '站点', 'choices':True, 'autofilter':True,},
    #     {'name': 'sclient', "width": "5%",'foreign_field': 'sclient__name', 'visible': True, 'title': '下载器', 'choices':True, 'autofilter':True,},
    #     {'name': 'location', "width": "8%",'visible': True, 'title': '存储位置', 'choices':True, 'autofilter':True,},
    #     {'name': 'trackerlink',  'placeholder': True, 'visible': True, 'title': '原站查找', 'searchable': False, },
    # ]

    def customize_row(self, row, obj):
        if obj.tracker is not None:
            row['trackerlink'] = '<a href=\"%s\" target=\"_blank\">%s</a>' % (
                self._get_search_link(obj), obj.tracker)
        else:
            row['trackerlink'] = ''
        return

    SEARCH_URL_PREFIX = {
        'pterclub': 'https://pterclub.com/torrents.php?search=',
        'pthome': 'https://pthome.net/torrents.php?search=',
        'm-team': 'https://kp.m-team.cc/torrents.php?search=',
        'chdbits': 'https://chdbits.co/torrents.php?search=',
        'ourbits': 'https://ourbits.club/torrents.php?search=',
        'hdsky': 'https://hdsky.me/torrents.php?search=',
        'totheglory': 'https://totheglory.im/browse.php?search_field=',
        'keepfrds': 'https://pt.keepfrds.com/torrents.php?search=',
        'springsunday': 'https://springsunday.net/torrents.php?search=',
        'open': 'https://open.cd/torrents.php?search=',
        'discfan': 'https://discfan.net/torrents.php?search=',
        'btschool': 'https://pt.btschool.club/torrents.php?search=',
        'hddolby': 'https://www.hddolby.com/torrents.php?search=',
        'hdchina': 'https://hdchina.org/torrents.php?search=',
        'hdatmos': 'https://hdatmos.club/torrents.php?search=',
        'dmhy': 'https://u2.dmhy.org/torrents.php?search=',
        'tjupt': 'https://www.tjupt.org/torrents.php?search=',
        'beitai': 'https://www.beitai.pt/torrents.php?search=',
        'hares': 'https://club.hares.top/torrents.php?search=',
        'ptsbao': 'https://ptsbao.club/torrents.php?search=',
        'soulvoice': 'https://pt.soulvoice.club/torrents.php?search=',
        'hdhome': 'https://hdhome.org/torrents.php?search=',
        'lemonhd': 'https://lemonhd.org/torrents.php?search=',
        'hdtime': 'https://hdtime.org/torrents.php?search=',
        'iptorrents': 'https://iptorrents.com/t?q=',
        'torrentleech':
        'https://www.torrentleech.org/torrents/browse/index/query/',
        'blutopia': 'https://blutopia.xyz/torrents?name=',
    }

    def _get_search_link(self, obj):
        if obj.tracker in self.SEARCH_URL_PREFIX:
            sstr = obj.name
            if obj.guess_category not in ['Audio', 'Music', 'eBook']:
                match = re.search(r'^[\s\[ ]*(.*)[\. ]\d', obj.name, re.I)
                if match:
                    sstr = match.group(1).replace('.', ' ')
                if obj.tracker in ['keepfrds', 'ourbits']:
                    sstr = re.sub('[\u4e00-\u9fa5]', '', sstr)
                # elif obj.tracker in ['springsunday']:
                #     sstr = re.sub('[\u4e00-\u9fa5]', '', sstr)
            dilimers = {'[':' ', ']':' ', '.':' ', 'Complete': ' '}
            for original, replacement in dilimers.items():
                sstr = sstr.replace(original, replacement)           
            return self.SEARCH_URL_PREFIX[obj.tracker] + sstr
        else:
            return ''


def torrentIndex(request):
    return render(request, 'torrent/tablelist.html', {})


@method_decorator(login_required, name='dispatch')
class TorrentListView(ListView):
    model = Torrent
    template_name = 'torrent/list.html'
    context_object_name = 'torlist'
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        queryset_list = Torrent.objects.all().order_by("-pk")
        query = self.request.GET.get("q")
        if query:
            queryset_list = queryset_list.filter(
                Q(name__icontains=query)).distinct()

        return queryset_list


@login_required
def torrentListView(request):
    query = request.GET.get('q')
    if query:
        qset = (Q(name__icontains=query))
        results = Torrent.objects.filter(qset).distinct()
    else:
        results = Torrent.objects.all().order_by('-pk')

    paginator = Paginator(results, settings.PAGINATE_BY)
    pageNumber = request.GET.get('page')
    pageItems = paginator.get_page(pageNumber)

    return render(request,
                  template_name='torrent/list.html',
                  context={'page_obj': pageItems})
