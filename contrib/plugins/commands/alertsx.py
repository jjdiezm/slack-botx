from app.tasks.base_tasks import Command
from app.common.slack_models import CommandModelIn, CommandModelOut 
from fastapi.encoders import jsonable_encoder
import app.common.util
import argparse
import json

class Task(Command):
    async def execute(self):
        command_in : CommandModelIn = self.event_in
        self.logger.info(f"AlertsX.execute[{command_in}]")
        
        #get alerts status
        gql_query = await app.common.util.format_graphql_query( "alertsx_status", {'criteria_group':"easework-admin"})
        response_json = await self.http_gql_client.query(  gql_query )
        self.logger.info(f"gql_response [{response_json}]")

        #create the response message
        count_ok:int = 0
        count_err:int = 0
        suppliers_alerts = []
        for edges in response_json['data']['alertsX']['alerts']['edges']:
            for node_edges in edges['node']['alertData']['events']['edges']:
                event_data = node_edges['node']['eventData']
                if event_data['status'] == "OK":
                    count_ok += 1
                else:
                    count_err += 1
                    suppliers_alerts.append(event_data['groupBy']) 
        blocks = await app.common.util.get_message_blocks_payload( ["alertsx_status"], {'count_ok': count_ok, 'count_err': count_err} )
        self.logger.info(f"blocks:[{command_in.response_url}][{blocks}]")
        out =  CommandModelOut( response_type='in_channel', replace_original=True )
        self.logger.info(f"out:[{out.dict()}]")
        #response to slack
        #https://api.slack.com/reference/messaging/payload
        response = app.common.util.send_slack_post_model(url = command_in.response_url, data_model = out)
        self.logger.info(f"AlertsX execution OK [{response}]")

    async def needs_help(self)->bool:
        parser = argparse.ArgumentParser()
        parser.add_argument("status")
        parser.add_argument("help")
        args = parser.parse_args( self.event_in.text )
        if (args.help):
            return True
        if not (args.status):
            return True
        return False

    
