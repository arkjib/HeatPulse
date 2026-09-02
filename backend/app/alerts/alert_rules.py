from app.schemas.alerts import AlertRuleDefinition, ActionRecommendation

# Heuristic Rules mapping risk category + persistence to actions
RULES = [
    AlertRuleDefinition(
        rule_id="RULE_LOW_RISK",
        condition_description="Risk is LOW. Routine monitoring.",
        severity="LOW",
        recommended_actions=[
            ActionRecommendation(action_id="MONITOR", description="Routine monitoring")
        ],
        explanation="Routine background monitoring. No immediate action required."
    ),
    AlertRuleDefinition(
        rule_id="RULE_MODERATE_RISK",
        condition_description="Risk is MODERATE.",
        severity="MODERATE",
        recommended_actions=[
            ActionRecommendation(action_id="PREPARE_MSG", description="Prepare public messaging"),
            ActionRecommendation(action_id="INC_MONITOR", description="Increase monitoring")
        ],
        explanation="Risk is elevated. Prepare standard messaging."
    ),
    AlertRuleDefinition(
        rule_id="RULE_HIGH_RISK",
        condition_description="Risk is HIGH.",
        severity="HIGH",
        recommended_actions=[
            ActionRecommendation(action_id="ISSUE_ADVISORY", description="Issue heat advisory"),
            ActionRecommendation(action_id="INC_WATER", description="Increase water availability"),
            ActionRecommendation(action_id="REVIEW_WORK", description="Review outdoor-work scheduling")
        ],
        explanation="High hazard and/or exposure detected. Intervention advised."
    ),
    AlertRuleDefinition(
        rule_id="RULE_VERY_HIGH_RISK",
        condition_description="Risk is VERY_HIGH.",
        severity="VERY_HIGH",
        recommended_actions=[
            ActionRecommendation(action_id="ACTIVATE_HAP", description="Activate enhanced Heat Action Plan measures"),
            ActionRecommendation(action_id="OPEN_COOLING", description="Open/prepare cooling centres"),
            ActionRecommendation(action_id="ADVISE_WORK_MOD", description="Strongly advise outdoor-work modification")
        ],
        explanation="Severe localized risk. Enhanced HAP measures required."
    ),
    AlertRuleDefinition(
        rule_id="RULE_EXTREME_RISK",
        condition_description="Risk is EXTREME.",
        severity="EXTREME",
        recommended_actions=[
            ActionRecommendation(action_id="ACTIVATE_MAX_HAP", description="Activate highest-level Heat Action Plan"),
            ActionRecommendation(action_id="EMERGENCY_COOLING", description="Deploy emergency cooling resources"),
            ActionRecommendation(action_id="RESTRICT_WORK", description="Restrict/modify hazardous outdoor work where authorized")
        ],
        explanation="Extreme localized risk threshold crossed."
    )
]

def get_rule_for_category(category: str) -> AlertRuleDefinition:
    for rule in RULES:
        if rule.severity in category:
            return rule
    # Fallback
    return RULES[0]
