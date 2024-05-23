from django import forms
from dashboard.models import ChatConfiguration

class ChatConfigurationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ChatConfigurationForm, self).__init__(*args, **kwargs)
        readonly_fields = []
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            for field in readonly_fields:
                self.fields[field].widget.attrs['readonly'] = True
                self.fields[field].widget.attrs['disabled'] = True

    class Meta:
        model = ChatConfiguration
        fields = ['system_message', 'included_plugins',"use_document_retrieval", 'document_tags']
