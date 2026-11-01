import unittest
from unittest.mock import Mock, patch
import requests
import agent
from planner import choose_topic, build_tasks
from simulator import simulate

class ReliabilityTests(unittest.TestCase):
    def test_transient_read_retries_but_write_does_not(self):
        with patch.dict('os.environ', {'SUPABASE_URL':'https://example.invalid','DB_SERVICE_KEY':'sb_secret_test'}):
            db=agent.Database()
        response=Mock();response.content=b'[]';response.json.return_value=[]
        with patch.object(agent.requests,'request',side_effect=[requests.Timeout(),response]) as call,patch.object(agent.time,'sleep'):
            self.assertEqual(db.request('GET','/agent_runs'),[])
            self.assertEqual(call.call_count,2)
        with patch.object(agent.requests,'request',side_effect=requests.Timeout()) as call:
            with self.assertRaises(requests.Timeout):db.request('POST','/agent_runs',payload={})
            self.assertEqual(call.call_count,1)

    def test_oldest_topic_breaks_equal_counts(self):
        self.assertEqual(choose_topic([{'topic':'a'},{'topic':'b'}],('a','b')), 'b')

    def test_simulation_is_never_real_evidence(self):
        r=simulate(visitors=100, conversion_rate=.1, price_vnd=20000, unit_cost_vnd=5000)
        self.assertEqual(r['scenarios'][1]['hypothetical_margin_vnd'],150000)
        self.assertEqual((r['actual_spend_vnd'],r['actual_revenue_vnd']), (0,0))
        self.assertEqual(r['evidence_status'],'unvalidated')

    def test_invalid_simulation_assumptions(self):
        for kwargs in ({'visitors':-1},{'visitors':True},{'conversion_rate':2},
                       {'price_vnd':float('nan')},{'unit_cost_vnd':-1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):simulate(**kwargs)

    def test_plan_blocks_external_actions(self):
        tasks=build_tasks({}, {})
        self.assertEqual(tasks[-1]['status'],'blocked')
        self.assertEqual(tasks[-1]['kind'],'owner_review')

    def test_history_failure_releases_claim(self):
        db=Mock();db.count_today.return_value=0
        db.claim_event.return_value={'id':'event', 'attempts':1}
        def request(method,path,**kwargs):
            if method=='GET':raise requests.Timeout('secret must not be saved')
            return []
        db.request.side_effect=request
        with patch.object(agent,'Database',return_value=db),patch.dict('os.environ',{'MANUAL_TOPIC':'','ISSUE_NUMBER':''}):
            with self.assertRaises(requests.Timeout):agent.main()
        release=db.request.call_args.kwargs
        self.assertEqual(release['payload']['status'],'pending')
        self.assertEqual(release['payload']['last_error'],'Timeout')
        self.assertEqual(release['params']['attempts'],'eq.1')

    def test_atomic_completion_receives_plan_and_simulation(self):
        db=Mock();db.count_today.return_value=0;db.claim_event.return_value=None
        db.request.return_value=[];db.insert.return_value={'id':'run'}
        proposal={'title':'example'}
        with patch.object(agent,'Database',return_value=db),patch.object(agent,'research',return_value=[]),patch.object(agent,'make_proposal',return_value=proposal),patch.dict('os.environ',{'MANUAL_TOPIC':'test','ISSUE_NUMBER':''}):agent.main()
        self.assertEqual(db.request.call_args.args,('POST','/rpc/complete_agent_run'))
        payload=db.request.call_args.kwargs['payload']
        self.assertEqual(payload['p_simulation']['mode'],'simulation_only')
        self.assertEqual(len(payload['p_tasks']),3)
        db.insert.assert_called_once()

    def test_invalid_output_not_silently_relabelled_free(self):
        proposal={k: ('text' if v['type']=='string' else [] if v['type']=='array' else True if v['type']=='boolean' else 50) for k,v in agent.SCHEMA['properties'].items()}
        with self.assertRaisesRegex(ValueError,'Paid proposal'):agent.validate_proposal(proposal)
        proposal['estimated_cost_vnd']=0
        self.assertEqual(agent.validate_proposal(proposal),proposal)
        proposal['confidence_percent']='high'
        with self.assertRaises(ValueError):agent.validate_proposal(proposal)

if __name__=='__main__':unittest.main()
