import json
import os
import tempfile

from copy import copy
from django.apps import apps as django_apps
from django.core.serializers.base import DeserializationError
from django.test import TestCase, tag
from edc_base.utils import get_utcnow
from edc_device.constants import NODE_SERVER
from edc_sync import datetime_to_date_parser
from edc_sync_files.transaction import TransactionImporter, TransactionExporter
from faker import Faker

from ..models import OutgoingTransaction, IncomingTransaction
from ..site_sync_models import site_sync_models
from ..sync_model import SyncModel
from ..transaction import TransactionDeserializer, TransactionDeserializerError
from .models import TestModel, TestModelWithFkProtected, TestModelWithM2m, M2m, TestModelDates


fake = Faker()


def my_test_parser(json_text):
    model = 'edc_sync.testmodeldates'
    field = 'f2'
    return datetime_to_date_parser(json_text, model=model, field=field)


class TestDeserializer1(TestCase):

    databases = '__all__'

    def setUp(self):
        site_sync_models.registry = {}
        site_sync_models.loaded = False
        sync_models = [
            'edc_sync.testmodel',
            'edc_sync.testmodelwithfkprotected',
            'edc_sync.testmodelwithm2m',
            'edc_sync.testmodelhook', ]
        site_sync_models.register(sync_models)

        self.export_path = os.path.join(tempfile.gettempdir(), 'export')
        if not os.path.exists(self.export_path):
            os.mkdir(self.export_path)
        self.import_path = self.export_path
        IncomingTransaction.objects.all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModel.objects.all().delete()
        TestModel.objects.using('client').all().delete()
        TestModel.history.all().delete()
        TestModel.history.using('client').all().delete()
        TestModel.objects.using('client').create(f1='model1')
        TestModel.objects.using('client').create(f1='model2')

        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        self.batch = tx_importer.import_batch(filename=batch.filename)

    def test_deserilize(self):
        tx_deserializer = TransactionDeserializer(override_role=NODE_SERVER)
        tx_deserializer.deserialize_transactions(
            transactions=self.batch.saved_transactions)

    def test_deserilized_object(self):
        tx_deserializer = TransactionDeserializer(override_role=NODE_SERVER)
        tx_deserializer.deserialize_transactions(
            transactions=self.batch.saved_transactions)

    def test_saved(self):
        """Assert transaction object is saved to default db.
        """
        tx_deserializer = TransactionDeserializer(
            override_role=NODE_SERVER,
            using='default')
        tx_deserializer.deserialize_transactions(
            transactions=self.batch.saved_transactions)
        try:
            TestModel.objects.using('default').get(f1='model1')
        except TestModel.DoesNotExist:
            self.fail('TestModel.DoesNotExist unexpectedly raised')


class TestDeserializer2(TestCase):

    databases = '__all__'

    def setUp(self):
        site_sync_models.registry = {}
        site_sync_models.loaded = False
        sync_models = [
            'edc_sync.testmodel',
            'edc_sync.testmodelwithfkprotected',
            'edc_sync.testmodelwithm2m']
        site_sync_models.register(sync_models, wrapper_cls=SyncModel)

        self.export_path = os.path.join(tempfile.gettempdir(), 'export')
        if not os.path.exists(self.export_path):
            os.mkdir(self.export_path)
        self.import_path = self.export_path
        M2m.objects.all().delete()
        M2m.objects.using('client').all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        IncomingTransaction.objects.all().delete()
        TestModel.objects.all().delete()
        TestModel.objects.using('client').all().delete()
        TestModel.history.all().delete()
        TestModel.history.using('client').all().delete()

    def test_saved_on_self(self):
        """Asserts can save on self if allow_self=True.
        """
        TestModel.objects.create(f1='model1')
        tx_exporter = TransactionExporter(export_path=self.export_path)
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        tx_deserializer = TransactionDeserializer(
            override_role=NODE_SERVER, allow_self=True)
        tx_deserializer.deserialize_transactions(
            transactions=batch.saved_transactions)
        try:
            TestModel.objects.get(f1='model1')
        except TestModel.DoesNotExist:
            self.fail('TestModel unexpectedly does not exist')

    def test_created_from_client(self):
        """Asserts "default" instance is created when "client" instance
        is created.
        """
        TestModel.objects.using('client').create(f1='model1')
        tx_exporter = TransactionExporter(
            export_path=self.export_path, using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        tx_deserializer = TransactionDeserializer(
            override_role=NODE_SERVER, allow_self=True)
        tx_deserializer.deserialize_transactions(
            transactions=batch.saved_transactions)
        try:
            TestModel.objects.get(f1='model1')
        except TestModel.DoesNotExist:
            self.fail('TestModel unexpectedly does not exists')

    def test_flagged_as_deserialized(self):
        """Asserts "default" instance is created when "client" instance
        is created.
        """
        TestModel.objects.using('client').create(f1='model1')
        tx_exporter = TransactionExporter(
            export_path=self.export_path, using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        tx_deserializer = TransactionDeserializer(
            override_role=NODE_SERVER, allow_self=True)
        tx_deserializer.deserialize_transactions(
            transactions=batch.saved_transactions)
        for transaction in batch.saved_transactions:
            self.assertTrue(transaction.is_consumed)

    def test_deleted_from_client(self):
        """Asserts "default" instance is deleted when "client" instance
        is deleted.
        """
        test_model = TestModel.objects.using('client').create(f1='model1')
        tx_exporter = TransactionExporter(
            export_path=self.export_path, using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        tx_deserializer = TransactionDeserializer(
            override_role=NODE_SERVER, allow_self=True)
        tx_deserializer.deserialize_transactions(
            transactions=batch.saved_transactions, deserialize_only=True)
        test_model.delete()
        tx_exporter = TransactionExporter(
            export_path=self.export_path, using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        tx_deserializer = TransactionDeserializer(
            override_role=NODE_SERVER, allow_self=True)
        tx_deserializer.deserialize_transactions(
            transactions=batch.saved_transactions)
        try:
            TestModel.objects.get(f1='model1')
        except TestModel.DoesNotExist:
            pass
        else:
            self.fail('TestModel unexpectedly exists')

    def test_dont_allow_saved_on_self(self):
        """Asserts cannot save on self by default.
        """
        TestModel.objects.create(f1='model1')
        tx_exporter = TransactionExporter(export_path=self.export_path)
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        tx_importer.import_batch(filename=batch.filename)
        self.assertRaises(
            TransactionDeserializerError,
            TransactionDeserializer)

    def test_allow_saved_on_self(self):
        """Asserts can save on self by default.
        """
        TestModel.objects.create(f1='model1')
        tx_exporter = TransactionExporter(export_path=self.export_path)
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        tx_importer.import_batch(filename=batch.filename)
        self.assertRaises(TransactionDeserializerError,
                          TransactionDeserializer, allow_self=True)

    def test_allow_saved_on_any_device(self):
        """Asserts can save on self by default.
        """
        TestModel.objects.create(f1='model1')
        tx_exporter = TransactionExporter(export_path=self.export_path)
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        tx_importer.import_batch(filename=batch.filename)
        self.assertRaises(TransactionDeserializerError,
                          TransactionDeserializer, allow_self=True)

    def test_deserialized_with_fk(self):
        """Asserts correctly deserialized model with FK.
        """
        test_model = TestModel.objects.using('client').create(f1='model1')
        TestModelWithFkProtected.objects.using(
            'client').create(f1='f1', test_model=test_model)
        tx_exporter = TransactionExporter(
            export_path=self.export_path, using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        tx_deserializer = TransactionDeserializer(
            allow_self=True, override_role=NODE_SERVER)
        tx_deserializer.deserialize_transactions(
            transactions=batch.saved_transactions)
        test_model = TestModel.objects.get(f1='model1')
        try:
            obj = TestModelWithFkProtected.objects.get(f1='f1')
        except TestModelWithFkProtected.DoesNotExist:
            self.fail('TestModel unexpectedly does not exists')
        self.assertEqual(test_model, obj.test_model)

    def test_deserialized_with_history(self):
        """Asserts correctly deserialized model with history.
        """
        TestModel.objects.using('client').create(f1='model1')
        tx_exporter = TransactionExporter(
            export_path=self.export_path, using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        tx_deserializer = TransactionDeserializer(
            allow_self=True, override_role=NODE_SERVER)
        tx_deserializer.deserialize_transactions(
            transactions=batch.saved_transactions)
        try:
            TestModel.history.get(f1='model1')
        except TestModel.DoesNotExist:
            self.fail('TestModel history unexpectedly does not exists')

    def test_deserialize_with_m2m(self):
        """Asserts deserializes model with M2M as long as
        M2M instance exists on destination.
        """
        obj = TestModelWithM2m.objects.using('client').create(f1='model1')
        m2m = M2m.objects.using('client').create(name='erik', short_name='bob')
        obj.m2m.add(m2m)

        tx_exporter = TransactionExporter(
            export_path=self.export_path, using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)

        M2m.objects.create(name='erik', short_name='bob')

        tx_deserializer = TransactionDeserializer(
            allow_self=True, override_role=NODE_SERVER)
        tx_deserializer.deserialize_transactions(
            transactions=batch.saved_transactions, deserialize_only=False)
        obj = TestModelWithM2m.objects.get(f1='model1')

        obj.m2m.get(short_name='bob')

    def test_deserialize_with_m2m_missing(self):
        """Asserts deserialization error if m2m instance does not
        exist on destination.
        """
        obj = TestModelWithM2m.objects.using('client').create(f1='model1')
        m2m = M2m.objects.using('client').create(name='erik')
        obj.m2m.add(m2m)
        tx_exporter = TransactionExporter(
            export_path=self.export_path, using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        batch = tx_importer.import_batch(filename=batch.filename)
        tx_deserializer = TransactionDeserializer(
            allow_self=True, override_role=NODE_SERVER)
        self.assertRaises(
            DeserializationError,
            tx_deserializer.deserialize_transactions,
            transactions=batch.saved_transactions)


class TestDeserializer3(TestCase):

    databases = '__all__'

    def setUp(self):
        site_sync_models.registry = {}
        site_sync_models.loaded = False
        sync_models = ['edc_sync.testmodeldates']
        site_sync_models.register(sync_models, wrapper_cls=SyncModel)

        self.export_path = os.path.join(tempfile.gettempdir(), 'export')
        if not os.path.exists(self.export_path):
            os.mkdir(self.export_path)
        self.import_path = self.export_path
        IncomingTransaction.objects.all().delete()
        OutgoingTransaction.objects.using('client').all().delete()
        TestModelDates.objects.all().delete()
        TestModelDates.objects.using('client').all().delete()
        self.date = get_utcnow()
        TestModelDates.objects.using('client').create(f2=self.date.date())

        tx_exporter = TransactionExporter(
            export_path=self.export_path,
            using='client')
        batch = tx_exporter.export_batch()
        tx_importer = TransactionImporter(import_path=self.import_path)
        self.batch = tx_importer.import_batch(filename=batch.filename)

        datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        self.obj = IncomingTransaction.objects.all()[0]
        bad_date = self.date.strftime(datetime_format)
        json_text = self.obj.aes_decrypt(self.obj.tx)
        json_obj = json.loads(json_text)
        json_obj[0]['fields']['f2'] = bad_date
        json_text = json.dumps(json_obj)
        self.obj.tx = self.obj.aes_encrypt(json_text)
        self.obj.save()
        self.obj = IncomingTransaction.objects.get(id=self.obj.id)
        self.app_config = copy(django_apps.get_app_config('edc_sync'))

    def tearDown(self):
        django_apps.app_configs['edc_sync'] = self.app_config

    def test_raises_for_invalid_date(self):
        tx_deserializer = TransactionDeserializer(
            allow_self=True, override_role=NODE_SERVER)
        self.assertRaises(
            DeserializationError,
            tx_deserializer.deserialize_transactions,
            transactions=IncomingTransaction.objects.all())

    def test_custom_parser_declared_in_apps_fixes_date(self):
        app_config = django_apps.get_app_config('edc_sync')
        app_config.custom_json_parsers = [my_test_parser]
        django_apps.app_configs['edc_sync'] = app_config
        tx_deserializer = TransactionDeserializer(
            allow_self=True, override_role=NODE_SERVER)
        try:
            tx_deserializer.deserialize_transactions(
                transactions=[self.obj])
        except DeserializationError:
            self.fail('DeserializationError unexpectedly raised')
