"""Bounded, explainable memory; no embedding service or external requests."""
import re
import unicodedata
from difflib import SequenceMatcher


def normalize(text):
    text=unicodedata.normalize('NFKD',str(text).casefold()).replace('đ','d')
    text=''.join(c for c in text if not unicodedata.combining(c))
    return ' '.join(re.findall(r'\w+',text))


def similarity(a,b):
    a,b=normalize(a),normalize(b)
    if not a or not b:return 0.0
    return SequenceMatcher(None,a,b,autojunk=False).ratio()


def recall(proposal, history):
    """Match problem + customer even when an idea has a different title."""
    best={'duplicate':False,'similarity':0.0,'matched_id':None,'prior_decision':None}
    for row in history[:200]:
        old=row.get('proposal') or {}
        title=similarity(proposal.get('title',''),old.get('title',''))
        problem=similarity(proposal.get('problem_hypothesis',''),old.get('problem_hypothesis',''))
        customer=similarity(proposal.get('target_customer',''),old.get('target_customer',''))
        score=max(title,min(problem,customer))
        duplicate=title>=.9 or (problem>=.88 and customer>=.85)
        if (duplicate,score)>(best['duplicate'],best['similarity']):
            best={'duplicate':duplicate,
                  'similarity':round(score,3),'matched_id':row.get('id'),
                  'prior_decision':row.get('approval_status')}
    return best


def memory_context(history):
    return [{'title':r.get('proposal',{}).get('title','')[:200],
             'problem':r.get('proposal',{}).get('problem_hypothesis','')[:300],
             'customer':r.get('proposal',{}).get('target_customer','')[:150],
             'decision':r.get('approval_status','pending')}
            for r in history[:40] if isinstance(r.get('proposal'),dict)]
