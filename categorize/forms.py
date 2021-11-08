from django import forms
from seedclient.models import LocationCategory, CategorizeStep


class CategoryExcludeForm(forms.Form):
    INITIAL_CHOICES = []
    scRootDir = forms.CharField(max_length=255,
                                label='分类的根目录：',
                            
                                required=True)
    dirNotExclude = forms.MultipleChoiceField(
        choices=INITIAL_CHOICES,
        label='选择分类的目录：',
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        csList = CategorizeStep.objects.all()
        if len(csList) > 0:
            cs = csList[0]
            self.fields['scRootDir'].initial = cs.sclient.root_dir
            self.fields['scRootDir'].widget.attrs['style'] = 'width:400px;'
            # locChoices = [('', '无')]
            locChoices = []
            locList = LocationCategory.objects.filter(
                scname=cs.sclient.name).order_by('location')
            for locItem in locList:
                newItem = (locItem.scname + ': ' + locItem.location,
                           locItem.scname + ': ' + locItem.location)
                locChoices.append(newItem)
            self.fields['dirNotExclude'].choices = locChoices
