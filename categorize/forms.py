from django import forms
from seedclient.models import LocationCategory, CategorizeStep, Torrent


class CategoryExcludeForm(forms.Form):
    INITIAL_CHOICES = []
    scRootDir = forms.CharField(max_length=255,
                                label='1. （必选）分类的根目录',
                                required=True)
    dirNotExclude = forms.MultipleChoiceField(
        choices=INITIAL_CHOICES,
        label='2. （必选）选择哪些位置要进行分类，未勾选的不会进行改变',
        widget=forms.CheckboxSelectMultiple,
    )
    trackerSelect = forms.MultipleChoiceField(
        choices=INITIAL_CHOICES,
        label='3. （option）选择哪些站点的种子分到专门子目录，如果有同名的辅种种子，也将一并移动。剩余的移至猜测分类目录',
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        csList = CategorizeStep.objects.all()
        if len(csList) > 0:
            cs = csList[0]
            locChoices = []
            locList = LocationCategory.objects.filter(
                scname=cs.sclient.name).order_by('location')
            minDir = locList[0].location
            for locItem in locList:
                newItem = (locItem.scname + ': ' + locItem.location,
                           locItem.scname + ': ' + locItem.location)
                locChoices.append(newItem)
                if len(locItem.location) < len(minDir):
                    minDir = locItem.location
            self.fields['dirNotExclude'].choices = locChoices

            self.fields['scRootDir'].initial = minDir
            self.fields['scRootDir'].widget.attrs['style'] = 'width:400px;'

            trkChoices = []
            trackerDistinctList = Torrent.objects.filter(
                sclient=cs.sclient).values('tracker').distinct()
            for trkItem in trackerDistinctList:
                newTrk = (trkItem['tracker'], trkItem['tracker'])
                trkChoices.append(newTrk)
            self.fields['trackerSelect'].choices = trkChoices
            self.fields['trackerSelect'].required = False
