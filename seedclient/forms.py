from django import forms
from .models import SeedClientSetting


class SeedClientForm(forms.ModelForm):

    # password = forms.CharField(
    #     required=True,
    #     label='新密码',
    #     widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    #     error_messages={'required': '请输入新密码。'})

    # password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField(label='用户名', required=False)
    password = forms.CharField(label='密码', required=False)
    # root_dir = forms.CharField(label='存储根目录', required=False)
    class Meta:
        model = SeedClientSetting
        fields = ['clienttype', 'name', 'host', 'port', 'username', 'password']
