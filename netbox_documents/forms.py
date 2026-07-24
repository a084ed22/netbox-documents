from django import forms
from django.contrib.contenttypes.models import ContentType
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from utilities.forms.fields import (
    CommentField,
    ContentTypeChoiceField,
    DynamicModelChoiceField,
    TagFilterField,
)
from .models import Document, DocTypeChoices, get_allowed_doc_types


class DocumentForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = Document
        fields = (
            'name', 'document', 'external_url', 'document_type',
            'comments', 'tags',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The content type is fixed by the object from which the document was
        # created, but the assigned object can be changed to another instance
        # of that model. This restores the reassignment functionality exposed
        # by the model-specific forms prior to v0.8.
        content_type_id = None
        if self.instance and self.instance.content_type_id:
            content_type_id = self.instance.content_type_id
            model = self.instance.content_type.model_class()
            if model is not None:
                self.fields['assigned_object'] = DynamicModelChoiceField(
                    queryset=model._default_manager.all(),
                    label=model._meta.verbose_name.title(),
                    selector=True,
                    help_text='The object to which this document is assigned.',
                )
                self.initial['assigned_object'] = self.instance.assigned_object

        allowed_values = get_allowed_doc_types(content_type_id)

        if allowed_values is not None:
            all_choices = list(DocTypeChoices())
            filtered = [c for c in all_choices if c[0] in allowed_values]

            # Preserve the current value when editing an existing document
            if self.instance and self.instance.pk:
                current = self.instance.document_type
                if current and current not in allowed_values:
                    current_label = dict(all_choices).get(current, current)
                    filtered.append((current, current_label))

            self.fields['document_type'].choices = filtered

    def clean(self):
        super().clean()

        # assigned_object is a form-only GenericForeignKey helper. Persist its
        # primary key in the Document's object_id field while retaining the
        # existing content type.
        assigned_object = self.cleaned_data.get('assigned_object')
        if assigned_object is not None:
            self.instance.object_id = assigned_object.pk


class DocumentFilterForm(NetBoxModelFilterSetForm):
    model = Document

    name = forms.CharField(required=False)

    document_type = forms.MultipleChoiceField(
        choices=DocTypeChoices,
        required=False,
    )

    content_type = ContentTypeChoiceField(
        queryset=ContentType.objects.all(),
        required=False,
        label='Object Type',
    )

    tag = TagFilterField(model)
