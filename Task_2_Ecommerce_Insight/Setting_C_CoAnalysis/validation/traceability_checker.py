import pandas as pd
from utils.logger import get_logger

logger = get_logger("validation.traceability")

def build_traceability_matrix(recommendations, insights):
    """
    Creates a mapping of recommendation_id -> insight_id -> evidence_summary.
    Verifies that each recommendation maps to an insight with quantitative evidence.
    """
    logger.info("Building recommendation-to-insight traceability matrix...")
    
    # Create insight lookup map
    insight_map = {ins['insight_id']: ins for ins in insights}
    
    trace_data = []
    
    for rec in recommendations:
        rec_id = rec['recommendation_id']
        linked_insights = rec.get('insight_ids', [])
        
        if not linked_insights:
            logger.warning(f"Recommendation '{rec_id}' has no linked insight IDs.")
            trace_data.append({
                'recommendation_id': rec_id,
                'insight_id': 'None',
                'evidence_summary': 'No linked insights',
                'has_quantitative_evidence': False
            })
            continue
            
        for ins_id in linked_insights:
            if ins_id not in insight_map:
                logger.warning(f"Recommendation '{rec_id}' links to non-existent insight ID '{ins_id}'.")
                trace_data.append({
                    'recommendation_id': rec_id,
                    'insight_id': ins_id,
                    'evidence_summary': 'Linked insight ID does not exist',
                    'has_quantitative_evidence': False
                })
                continue
                
            insight = insight_map[ins_id]
            quant_val = insight.get('quantitative_value')
            has_quant = pd.notna(quant_val) and quant_val != ''
            
            trace_data.append({
                'recommendation_id': rec_id,
                'insight_id': ins_id,
                'evidence_summary': insight['description'][:100],
                'has_quantitative_evidence': has_quant
            })
            
    traceability_df = pd.DataFrame(trace_data)
    logger.info("Traceability matrix construction complete.")
    return traceability_df

def classify_recommendations(traceability_matrix, recommendations):
    """
    Classifies recommendations into qualified and rejected based on quantitative evidence and priority.
    """
    logger.info("Classifying recommendations...")
    
    # Group traceability by recommendation_id to count valid quantitative evidence items
    grouped = traceability_matrix.groupby('recommendation_id').agg({
        'has_quantitative_evidence': 'any'
    }).to_dict()['has_quantitative_evidence']
    
    qualified = []
    rejected = []
    
    for rec in recommendations:
        rec_id = rec['recommendation_id']
        has_evidence = grouped.get(rec_id, False)
        
        # Check priority tier: high/medium
        priority = rec.get('priority_tier', 'low').lower()
        
        # To qualify, a recommendation must have quantitative evidence and not be low priority
        if has_evidence and priority in ['high', 'medium']:
            qualified.append(rec)
        else:
            reason = "Missing quantitative evidence" if not has_evidence else "Priority tier is low"
            rec_copy = rec.copy()
            rec_copy['rejection_reason'] = reason
            rejected.append(rec_copy)
            
    # Sort qualified recommendations: High priority first, then sort by impact_score
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    
    def sort_key(r):
        p_tier = r.get('priority_tier', 'medium').lower()
        impact = r.get('impact_score', 0)
        return (priority_order.get(p_tier, 1), -impact)
        
    qualified_sorted = sorted(qualified, key=sort_key)
    
    # Limit to top 3-5 priority recommendations as per design
    final_qualified = qualified_sorted[:5]
    for r in qualified_sorted[5:]:
        r_copy = r.copy()
        r_copy['rejection_reason'] = "Capped at top 5 recommendations"
        rejected.append(r_copy)
        
    logger.info(f"Classification complete: {len(final_qualified)} qualified, {len(rejected)} rejected.")
    return {
        'qualified': final_qualified,
        'rejected': rejected
    }
