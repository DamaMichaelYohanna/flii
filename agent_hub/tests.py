from django.test import TestCase
from accounts.models import User
from agent_hub.agent import FliiAgent
from agent_hub.models import AgentAction

class AgentHubTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='agent_tester',
            email='agent_tester@example.com',
            password='Password123!'
        )

    def test_human_approval_state_machine(self):
        agent = FliiAgent(self.user)
        action = agent.request_user_approval(
            action_type="submit_application",
            title="Submit Test Application",
            description="Testing human approval workflow",
            payload={"test": True}
        )
        self.assertEqual(action.status, 'pending')
        
        # User approves
        action.approve(feedback="Looks verified, proceed.")
        self.assertEqual(action.status, 'approved')
        self.assertIsNotNone(action.resolved_at)

    def test_agent_message_processing(self):
        agent = FliiAgent(self.user)
        res = agent.process_message("Find fully funded MSc in Germany")
        self.assertEqual(res['tool_used'], 'search_opportunities')
        self.assertIn('found', res['response'].lower())
