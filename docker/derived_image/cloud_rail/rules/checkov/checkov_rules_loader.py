from typing import List

from persistency.rule_metadata_store import RuleMetadataStore
from rules.base_rule import BaseRule
from rules.checkov.base_checkov_rule import BaseCheckovRule


class CheckovRulesLoader:
    @staticmethod
    def load_rules() -> List[BaseRule]:
        checkov_rule_ids = RuleMetadataStore.list_checkov_rule_ids()
        return [BaseCheckovRule(checkov_rule_id) for checkov_rule_id in checkov_rule_ids]
