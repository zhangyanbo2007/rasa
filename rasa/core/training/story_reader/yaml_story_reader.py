import logging
from pathlib import Path
from typing import Dict, Text, List, Any, Optional, Union

from ruamel.yaml.parser import ParserError

import rasa.utils.common as common_utils
import rasa.utils.io
from rasa.constants import DOCS_URL_STORIES, DOCS_URL_RULES
from rasa.core.constants import INTENT_MESSAGE_PREFIX
from rasa.core.actions.action import RULE_SNIPPET_ACTION_NAME
from rasa.core.events import UserUttered, SlotSet, Form
from rasa.core.training.story_reader.story_reader import StoryReader
from rasa.core.training.structures import StoryStep
from rasa.data import YAML_FILE_EXTENSIONS

logger = logging.getLogger(__name__)

KEY_STORIES = "stories"
KEY_STORY_NAME = "story"
KEY_RULES = "rules"
KEY_RULE_NAME = "rule"
KEY_STEPS = "steps"
KEY_ENTITIES = "entities"
KEY_USER_INTENT = "intent"
KEY_SLOT_NAME = "slot_was_set"
KEY_SLOT_VALUE = "value"
KEY_FORM = "active_loop"
KEY_ACTION = "action"
KEY_CHECKPOINT = "checkpoint"
KEY_CHECKPOINT_SLOTS = "slot_was_set"
KEY_METADATA = "metadata"
KEY_OR = "or"
KEY_RULE_CONDITION = "condition"
KEY_WAIT_FOR_USER_INPUT_AFTER_RULE = "wait_for_user_input"
KEY_RULE_FOR_CONVERSATION_START = "conversation_start"


class YAMLStoryReader(StoryReader):
    """Class that reads Core training data and rule data in YAML format."""

    @classmethod
    def from_reader(cls, reader: "YAMLStoryReader") -> "YAMLStoryReader":
        """Create a reader from another reader.

        Args:
            reader: Another reader.

        Returns:
            A new reader instance.
        """
        return cls(
            reader.interpreter,
            reader.domain,
            reader.template_variables,
            reader.use_e2e,
            reader.source_name,
        )

    async def read_from_file(self, filename: Text) -> List[StoryStep]:
        """Read stories or rules from file.

        Args:
            filename: Path to the story/rule file.

        Returns:
            `StoryStep`s read from `filename`.
        """
        try:
            yaml_content = rasa.utils.io.read_yaml_file(filename)
        except (ValueError, ParserError) as e:
            common_utils.raise_warning(
                f"Failed to read YAML from '{filename}', it will be skipped. Error: {e}"
            )
            return []

        if not isinstance(yaml_content, dict):
            common_utils.raise_warning(
                f"Failed to read '{filename}'. It should be a YAML dictionary."
            )
            return []

        return self.read_from_parsed_yaml(yaml_content)

    def read_from_parsed_yaml(
        self, parsed_content: Dict[Text, Union[Dict, List]]
    ) -> List[StoryStep]:
        """Read stories from parsed YAML.

        Args:
            parsed_content: The parsed YAML as a dictionary.

        Returns:
            The parsed stories or rules.
        """
        from rasa.validator import Validator

        if not Validator.validate_training_data_format_version(
            parsed_content, self.source_name
        ):
            return []

        for key, parser_class in {
            KEY_STORIES: StoryParser,
            KEY_RULES: RuleParser,
        }.items():
            data = parsed_content.get(key, [])
            parser = parser_class.from_reader(self)
            parser.parse_data(data)
            self.story_steps.extend(parser.get_steps())

        return self.story_steps

    @staticmethod
    def is_yaml_story_file(file_path: Text) -> bool:
        """Check if file contains Core training data or rule data in YAML format.

        Args:
            file_path: Path of the file to check.

        Returns:
            `True` in case the file is a Core YAML training data or rule data file,
            `False` otherwise.
        """
        suffix = Path(file_path).suffix

        if suffix and suffix not in YAML_FILE_EXTENSIONS:
            return False

        try:
            content = rasa.utils.io.read_yaml_file(file_path)
            return any(key in content for key in [KEY_STORIES, KEY_RULES])
        except Exception as e:
            # Using broad `Exception` because yaml library is not exposing all Errors
            common_utils.raise_warning(
                f"Tried to check if '{file_path}' is a story or rule file, but failed "
                f"to read it. If this file contains story or rule data, you should "
                f"investigate this error, otherwise it is probably best to "
                f"move the file to a different location. Error: {e}"
            )
            return False

    def get_steps(self) -> List[StoryStep]:
        self._add_current_stories_to_result()
        return self.story_steps

    def parse_data(self, data: List[Dict[Text, Any]]) -> None:
        item_title = self._get_item_title()

        for item in data:
            if not isinstance(item, dict):
                common_utils.raise_warning(
                    f"Unexpected block found in '{self.source_name}':\n"
                    f"{item}\nItems under the "
                    f"'{self._get_plural_item_title()}' key must be YAML "
                    f"dictionaries. It will be skipped.",
                    docs=self._get_docs_link(),
                )
                continue

            if item_title in item.keys():
                self._parse_plain_item(item)

    def _parse_plain_item(self, item: Dict[Text, Any]) -> None:
        item_name = item.get(self._get_item_title(), "")

        if not item_name:
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}': \n"
                f"{item}\n"
                f"The {self._get_item_title()} has an empty name. "
                f"{self._get_plural_item_title().capitalize()} should "
                f"have a name defined under '{self._get_item_title()}' "
                f"key. It will be skipped.",
                docs=self._get_docs_link(),
            )

        steps: List[Union[Text, Dict[Text, Any]]] = item.get(KEY_STEPS, [])

        if not steps:
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}': "
                f"The {self._get_item_title()} has no steps. "
                f"It will be skipped.",
                docs=self._get_docs_link(),
            )
            return

        self._new_part(item_name, item)

        for step in steps:
            self._parse_step(step)

        self._close_part(item)

    def _new_part(self, item_name: Text, item: Dict[Text, Any]) -> None:
        raise NotImplementedError()

    def _close_part(self, item: Dict[Text, Any]) -> None:
        pass

    def _parse_step(self, step: Union[Text, Dict[Text, Any]]) -> None:
        if isinstance(step, str):
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}':\n"
                f"Found an unexpected step in the {self._get_item_title()} "
                f"description:\n{step}\nThe step is of type `str` "
                f"which is only allowed for the rule snippet action "
                f"'{RULE_SNIPPET_ACTION_NAME}'. It will be skipped.",
                docs=self._get_docs_link(),
            )
        elif KEY_USER_INTENT in step.keys():
            self._parse_user_utterance(step)
        elif KEY_OR in step.keys():
            self._parse_or_statement(step)
        elif KEY_ACTION in step.keys():
            self._parse_action(step)
        elif KEY_CHECKPOINT in step.keys():
            self._parse_checkpoint(step)
        # This has to be after the checkpoint test as there can be a slot key within
        # a checkpoint.
        elif KEY_SLOT_NAME in step.keys():
            self._parse_slot(step)
        elif KEY_FORM in step.keys():
            self._parse_form(step[KEY_FORM])
        elif KEY_METADATA in step.keys():
            pass
        else:
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}':\n"
                f"Found an unexpected step in the {self._get_item_title()} "
                f"description:\n{step}\nIt will be skipped.",
                docs=self._get_docs_link(),
            )

    def _get_item_title(self) -> Text:
        raise NotImplementedError()

    def _get_plural_item_title(self) -> Text:
        raise NotImplementedError()

    def _get_docs_link(self) -> Text:
        raise NotImplementedError()

    def _parse_user_utterance(self, step: Dict[Text, Any]) -> None:
        utterance = self._parse_raw_user_utterance(step)
        if utterance:
            self._validate_that_utterance_is_in_domain(utterance)
            self.current_step_builder.add_user_messages([utterance])

    def _validate_that_utterance_is_in_domain(self, utterance: UserUttered) -> None:
        intent_name = utterance.intent.get("name")

        if not self.domain:
            logger.debug(
                "Skipped validating if intent is in domain as domain " "is `None`."
            )
            return

        if intent_name not in self.domain.intents:
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}': \n"
                f"Found intent '{intent_name}' in stories which is not part of the "
                f"domain.",
                docs=DOCS_URL_STORIES,
            )

    def _parse_or_statement(self, step: Dict[Text, Any]) -> None:
        utterances = []

        for utterance in step.get(KEY_OR):
            if KEY_USER_INTENT in utterance.keys():
                utterance = self._parse_raw_user_utterance(utterance)
                if utterance:
                    utterances.append(utterance)
            else:
                common_utils.raise_warning(
                    f"Issue found in '{self.source_name}': \n"
                    f"`OR` statement can only have '{KEY_USER_INTENT}' "
                    f"as a sub-element. This step will be skipped:\n"
                    f"'{utterance}'\n",
                    docs=self._get_docs_link(),
                )
                return

        self.current_step_builder.add_user_messages(utterances)

    def _parse_raw_user_utterance(self, step: Dict[Text, Any]) -> Optional[UserUttered]:
        user_utterance = step.get(KEY_USER_INTENT, "").strip()

        if not user_utterance:
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}':\n"
                f"User utterance cannot be empty. "
                f"This {self._get_item_title()} step will be skipped:\n"
                f"{step}",
                docs=self._get_docs_link(),
            )

        raw_entities = step.get(KEY_ENTITIES, [])
        final_entities = self._parse_raw_entities(raw_entities)

        if user_utterance.startswith(INTENT_MESSAGE_PREFIX):
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}':\n"
                f"User intent '{user_utterance}' starts with "
                f"'{INTENT_MESSAGE_PREFIX}'. This is not required.",
                docs=self._get_docs_link(),
            )
            # Remove leading slash
            user_utterance = user_utterance[1:]

        intent = {"name": user_utterance, "confidence": 1.0}

        return UserUttered(user_utterance, intent, final_entities)

    @staticmethod
    def _parse_raw_entities(
        raw_entities: Union[List[Dict[Text, Text]], List[Text]]
    ) -> List[Dict[Text, Text]]:
        final_entities = []
        for entity in raw_entities:
            if isinstance(entity, dict):
                for key, value in entity.items():
                    final_entities.append({"entity": key, "value": value})
            else:
                final_entities.append({"entity": entity, "value": ""})

        return final_entities

    def _parse_slot(self, step: Dict[Text, Any]) -> None:

        slot_name = step.get(KEY_SLOT_NAME, "")

        if not slot_name or KEY_SLOT_VALUE not in step:
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}': \n"
                f"Slots should have a name and a value. "
                f"This {self._get_item_title()} step will be skipped:\n"
                f"{step}",
                docs=self._get_docs_link(),
            )
            return

        slot_value = step.get(KEY_SLOT_VALUE, "")

        self._add_event(SlotSet.type_name, {slot_name: slot_value})

    def _parse_action(self, step: Dict[Text, Any]) -> None:

        action_name = step.get(KEY_ACTION, "")
        if not action_name:
            common_utils.raise_warning(
                f"Issue found in '{self.source_name}': \n"
                f"Action name cannot be empty. "
                f"This {self._get_item_title()} step will be skipped:\n"
                f"{step}",
                docs=self._get_docs_link(),
            )
            return

        self._add_event(action_name, {})

    def _parse_form(self, form_name: Optional[Text]) -> None:
        self._add_event(Form.type_name, {"name": form_name})

    def _parse_checkpoint(self, step: Dict[Text, Any]) -> None:

        checkpoint_name = step.get(KEY_CHECKPOINT, "")
        slots = step.get(KEY_CHECKPOINT_SLOTS, [])

        slots_dict = {}

        for slot in slots:
            if not isinstance(slot, dict):
                common_utils.raise_warning(
                    f"Issue found in '{self.source_name}':\n"
                    f"Checkpoint '{checkpoint_name}' has an invalid slot: "
                    f"{slots}\nItems under the '{KEY_CHECKPOINT_SLOTS}' key must be "
                    f"YAML dictionaries. The checkpoint will be skipped.",
                    docs=self._get_docs_link(),
                )
                return

            for key, value in slot.items():
                slots_dict[key] = value

        self._add_checkpoint(checkpoint_name, slots_dict)


class StoryParser(YAMLStoryReader):
    """Encapsulate story-specific parser behavior."""

    def _new_part(self, item_name: Text, item: Dict[Text, Any]) -> None:
        self._new_story_part(item_name, self.source_name)

    def _get_item_title(self) -> Text:
        return KEY_STORY_NAME

    def _get_plural_item_title(self) -> Text:
        return KEY_STORIES

    def _get_docs_link(self) -> Text:
        return DOCS_URL_STORIES


class RuleParser(YAMLStoryReader):
    """Encapsulate rule-specific parser behavior."""

    def _new_part(self, item_name: Text, item: Dict[Text, Any]) -> None:
        self._new_rule_part(item_name, self.source_name)
        conditions = item.get(KEY_RULE_CONDITION, [])
        self._parse_rule_conditions(conditions)
        if not item.get(KEY_RULE_FOR_CONVERSATION_START):
            self._parse_rule_snippet_action()

    def _parse_rule_conditions(
        self, conditions: List[Union[Text, Dict[Text, Any]]]
    ) -> None:
        for condition in conditions:
            self._parse_step(condition)

    def _close_part(self, item: Dict[Text, Any]) -> None:
        if item.get(KEY_WAIT_FOR_USER_INPUT_AFTER_RULE) is False:
            self._parse_rule_snippet_action()

    def _get_item_title(self) -> Text:
        return KEY_RULE_NAME

    def _get_plural_item_title(self) -> Text:
        return KEY_RULES

    def _get_docs_link(self) -> Text:
        return DOCS_URL_RULES

    def _parse_rule_snippet_action(self) -> None:
        self._add_event(RULE_SNIPPET_ACTION_NAME, {})
