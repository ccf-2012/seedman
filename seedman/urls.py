"""seedman URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import include, path
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from accounts.forms import UserLoginForm, PasswordChangeCustomForm
from seedclient.views import SeedClientAddView, SeedClientUpdateView, SeedClientDeleteView
from seedclient import views as scview
from torrents import views as torview
from summary import views as sumview
from categorize import views as catview
from activities import views as actview


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', SeedClientListView.as_view(), name='home'),
    path('', sumview.summaryCatIndex, name='home'),
]


urlpatterns += [
    path('seedclient/index', scview.sclientListView, name='sc_list'),
    path('seedclient/updatelist', scview.refreshSeedClientList, name='sc_update_list'),
    path('seedclient/connect', scview.sclientConnectionTest, name='sc_connect_test'),
    # path('seedclient/create', SeedClientAddView.as_view(), name='sc_create'),
    path('seedclient/create', scview.seedClientAddFunc, name='sc_create'),
    # path('seedclient/update/<int:pk>', SeedClientUpdateView.as_view(), name='sc_update'),
    path('seedclient/update/<int:pk>', scview.seedClientUpdateFunc, name='sc_update'),
    path('seedclient/delete/<int:pk>', SeedClientDeleteView.as_view(), name='sc_delete'),
    path('seedclient/load', scview.loadSclientTorrents, name='sc_loadtorrents'),
]


urlpatterns += [
    path('summary/catindex', sumview.summaryCatIndex, name='sum_cat_index'),
    path('summary/cattable', sumview.summaryCatTable.as_view(), name='sum_cat_table'),
    path('summary/trackerindex', sumview.summaryTrackerIndex, name='sum_tracker_index'),
    path('summary/trackerlist', sumview.summaryTrackerTable.as_view(), name='sum_tracker_table'),
    path('summary/dirindex', sumview.summaryDirIndex, name='sum_dir_index'),
    path('summary/dirlist', sumview.summaryDirTable.as_view(), name='sum_dir_table'),
]

urlpatterns += [
    path('categorize/index', catview.categorizeStep2, name='cat_step2'),
    path('categorize/cattable', catview.categorizeTable.as_view(), name='cat_table'),
    path('categorize/step0', catview.categorizeStep0, name='cat_step0'),
    path('categorize/step0/<int:pk>', catview.categorizeStep0Select, name='cat_step0select'),
    path('categorize/step1', catview.categorizeStep1, name='cat_step1'),
    path('categorize/proceed', catview.categorizeProceed, name='cat_proceed'),
    path('categorize/progress', catview.refreshProgress, name='cat_update_progress'),
]

urlpatterns += [
    # path('torrent/', torview.TorrentListView.as_view(), name='tor_list'),
    path('torrent/list', torview.TorrentListView.as_view(), name='tor_list'),
    # path('torrent/list/', torview.torrentListView, name='tor_list'),
    # path('torrent/index2/', torview.ZeroConfigurationDatatableView.as_view(), name='tor_index2'),
    path('torrent/index/', torview.torrentIndex, name='tor_index'),
    path('ajax_datatable/torrent', torview.TableView.as_view(), name='tor_table'),
]

urlpatterns += [
    path('activities/list', actview.activeList, name='active_list'),
    path('activities/listupdate/<int:pk>', actview.ajaxRefreshActiveList, name='activetor_update_list'),
    path('activities/listselect/<int:pk>', actview.activeListSelect, name='active_list_select'),
    path('activities/starttask', actview.startSpeedingTorrentTask, name='active_speed_taks'),
    # path('activities/actortableindex', actview.actorTableIndex, name='actor_table_index'),
    # path('activities/actortableajax', actview.actorTableAjax, name='actor_table_ajax'),
]

urlpatterns += [
    path('accounts/login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

urlpatterns += [
    url(r'^reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='auth/password_reset.html',
            email_template_name='auth/password_reset_email.html',
            subject_template_name='auth/password_reset_subject.txt'
        ),
        name='password_reset'),
    url(r'^reset/done/$',
        auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'),
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'),
        name='password_reset_confirm'),
    url(r'^reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'),
        name='password_reset_complete'),

    url(r'^settings/password/$', auth_views.PasswordChangeView.as_view(template_name='auth/password_change.html', form_class=PasswordChangeCustomForm),
        name='password_change'),
    url(r'^settings/password/done/$', auth_views.PasswordChangeDoneView.as_view(template_name='auth/password_change_done.html'),
        name='password_change_done'),
]

