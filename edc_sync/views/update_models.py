from datetime import datetime

import requests
from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import messages


class UpdateModels:

    def __init__(self, request):
        self.request = request

    @property
    def nav_plan_cls(self):
        return django_apps.get_model('potlako_subject.navigationsummaryandplan')

    @property
    def evaluation_timeline_cls(self):
        return django_apps.get_model('potlako_subject.evaluationtimeline')

    def update_models(self):
        """
        Sets up and configure an environment for pulling data from the database using
        the potlako rest api. The url of the rest api is defined in the .ini file. Use
        url to query for data from a remote server then pass the data to the update nav
        plans func
        :return: None
        """
        headers = {
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
        }
        nav_plans_url = settings.NAV_PLAN_API
        evaluation_timeline_url = settings.EVALUATION_TIMELINE

        nav_plans_reponce = requests.request("GET", nav_plans_url, headers=headers,
                                             verify=False)
        evaluation_timelines_response = requests.request("GET",
                                                         evaluation_timeline_url,
                                                         headers=headers,
                                                         verify=False)
        nav_plans = nav_plans_reponce.json()
        evaluation_timelines = evaluation_timelines_response.json()
        self.update_nav_plans(nav_plans, evaluation_timelines, self.request)

    def update_nav_plans(self, nav_plans, evaluation_timelines, request):
        """
        Takes evaluation plans and navigation plans then resaves the projects or create
        the objects if they do not exist. returns a message objects of either error or
        success regarding on weathere the update or create was succesful.
        :param nav_plans: navigation plass from the server, passed in as a list
        :param evaluation_timelines: list from server of evaluation timlines
        :param request: request dict from the current request for setting up messages
        :return: a message object to update the django messages for feedback
        """
        update_nav_message = True
        update_eva_message = True

        evaluation_timelines_batch = [{
            'id': row['id'],
            'navigation_plan_id': row['navigation_plan_id'],
            'key_step': row['key_step'],
            'target_date': row['target_date'] and datetime.strptime(row['target_date'],
                                                                    '%Y-%m-%d').date(),
            'adjusted_target_date': row['adjusted_target_date'] and datetime.strptime(
                row['adjusted_target_date'],
                '%Y-%m-%d').date(),
            'key_step_status': row['key_step_status'],
            'completion_date': row['completion_date'] and datetime.strptime(
                row['completion_date'],
                '%Y-%m-%d').date(),
            'review_required': row['review_required'], } for row in
            evaluation_timelines]

        for nav_plan in nav_plans:
            try:
                self.nav_plan_cls.objects.update_or_create(id=nav_plan.get('id'),
                                                           defaults=nav_plan)
            except Exception as e:
                update_nav_message = False
                messages.error(request,
                               f'Failed to update Navigation Plans, got error {e}')

        update_nav_message and messages.success(request, 'Updated Navigation Plans')
        for evaluation_timeline in evaluation_timelines_batch:
            try:
                self.evaluation_timeline_cls.objects.update_or_create(
                    id=evaluation_timeline.get('id'),
                    defaults=evaluation_timeline)
            except Exception as e:
                update_eva_message = False
                messages.error(request,
                               f'Failed to update Evaluation Timeline, got error {e}')

        update_eva_message and messages.success(request, 'Updated Evaluation Timelines')
        return messages
