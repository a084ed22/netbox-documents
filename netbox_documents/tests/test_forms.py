from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from dcim.models import Site
from netbox_documents.forms import DocumentForm
from netbox_documents.models import Document


class DocumentFormAssignmentTest(TestCase):
    def setUp(self):
        self.source_site = Site.objects.create(name='Source Site', slug='source-site')
        self.destination_site = Site.objects.create(name='Destination Site', slug='destination-site')
        self.site_type = ContentType.objects.get_for_model(Site)
        self.document = Document.objects.create(
            name='Site document',
            external_url='https://example.com/document.pdf',
            document_type='other',
            content_type=self.site_type,
            object_id=self.source_site.pk,
        )

    def _form_data(self, **overrides):
        data = {
            'name': self.document.name,
            'external_url': self.document.external_url,
            'document_type': self.document.document_type,
            'comments': '',
            'tags': [],
            'assigned_object': self.destination_site.pk,
        }
        data.update(overrides)
        return data

    def test_assignment_field_uses_document_content_type(self):
        form = DocumentForm(instance=self.document)

        self.assertIn('assigned_object', form.fields)
        self.assertIs(form.fields['assigned_object'].queryset.model, Site)
        self.assertEqual(form.initial['assigned_object'], self.source_site)

    def test_existing_document_can_be_reassigned(self):
        form = DocumentForm(data=self._form_data(), instance=self.document)

        self.assertTrue(form.is_valid(), form.errors)
        document = form.save()
        document.refresh_from_db()

        self.assertEqual(document.content_type, self.site_type)
        self.assertEqual(document.object_id, self.destination_site.pk)
        self.assertEqual(document.assigned_object, self.destination_site)

    def test_assigned_object_is_required(self):
        form = DocumentForm(
            data=self._form_data(assigned_object=''),
            instance=self.document,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('assigned_object', form.errors)
