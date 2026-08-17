from utils.logger import get_logger

logger = get_logger("reporting.insight_formatter")

def format_insight(insight_id, title, description, evidence_type, quant_val):
    """
    Constructs a structured insight dictionary.
    """
    return {
        'insight_id': insight_id,
        'title': title,
        'description': description,
        'evidence_type': evidence_type,
        'quantitative_value': quant_val
    }

def format_recommendation(rec_id, title, description, insight_ids, impact, feasibility, risk, priority):
    """
    Constructs a structured recommendation dictionary.
    """
    return {
        'recommendation_id': rec_id,
        'title': title,
        'description': description,
        'insight_ids': insight_ids,
        'impact_score': impact,       # 1-10 scale
        'difficulty_score': feasibility, # 1-10 scale (higher means easier/more feasible)
        'risk_score': risk,           # 1-10 scale (lower means safer)
        'priority_tier': priority     # 'High', 'Medium', 'Low'
    }
