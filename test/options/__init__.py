from abc import ABC, abstractmethod

from nativeconfig.exceptions import InitializationError, DeserializationError, ValidationError

from test import DummyMemoryConfig


class TestOptionMixin(ABC):
    OPTION_TYPE = None

    def test_name_cannot_be_none(self):
        with self.assertRaises(InitializationError):
            class MyConfig(DummyMemoryConfig):
                option = self.OPTION_TYPE(None)

    def test_name_cannot_be_empty(self):
        with self.assertRaises(InitializationError):
            class MyConfig(DummyMemoryConfig):
                option = self.OPTION_TYPE('')

    def test_env_name_cannot_be_empty(self):
        with self.assertRaises(InitializationError):
            class MyConfig(DummyMemoryConfig):
                option = self.OPTION_TYPE('Foo', env_name='')

    def test_choices_cannot_be_empty(self):
        with self.assertRaises(InitializationError):
            class MyConfig(DummyMemoryConfig):
                option = self.OPTION_TYPE('Foo', choices=[])

    def test_doc_passed_from_constructor(self):
        doc_string = 'Test option'

        class OptionsWithDoc(DummyMemoryConfig):
            test_array = self.OPTION_TYPE('Foo', doc=doc_string)

        c = OptionsWithDoc.get_instance()
        self.assertEqual(c.option_for_name('Foo').__doc__, doc_string)

    def test_doc_inherited_from_parent_if_not_passed(self):
        class OptionsWithDoc(DummyMemoryConfig):
            test_array = self.OPTION_TYPE('Foo')

        c = OptionsWithDoc.get_instance()
        self.assertEqual(c.option_for_name('Foo').__doc__, self.OPTION_TYPE.__doc__)

    @abstractmethod
    def test_default_value_must_be_one_of_choices_if_any(self):
        pass

    @abstractmethod
    def test_all_choices_must_be_valid(self):
        pass

    @abstractmethod
    def test_default_must_be_valid(self):
        pass

    @abstractmethod
    def test_value_must_be_one_of_choices_if_any(self):
        pass

    @abstractmethod
    def test_serialize_json(self):
        pass

    @abstractmethod
    def test_deserialize_json(self):
        pass

    @abstractmethod
    def test_value_can_be_overridden_by_env(self):
        pass

    @abstractmethod
    def test_value_can_be_overridden_by_one_shot_value(self):
        pass

    @abstractmethod
    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        pass

    @abstractmethod
    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        pass

    @abstractmethod
    def test_setting_value_resets_one_shot_value(self):
        pass

    @abstractmethod
    def test_setting_invalid_value_raises_exception(self):
        pass

    @abstractmethod
    def test_setting_none_deletes_value(self):
        pass

    @abstractmethod
    def test_deleting_value(self):
        pass

    @abstractmethod
    def test_env_is_first_json_deserialized_then_deserialized(self):
        pass

    @abstractmethod
    def test_env_value_must_be_valid_json(self):
        pass
