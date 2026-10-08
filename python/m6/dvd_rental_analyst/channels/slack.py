# python/m6/dvd_rental_analyst/channels/slack.py
"""Lets people @mention the agent in Slack.

The bare call is enough for a first deploy. The options below are all optional.

With this file present, `mda deploy` prints an authorization link near the end.
Approving it lets LangSmith create the Slack app, install it, and point its
Events endpoint at the deployment. The bot token is stored as a workspace
connection (`mda connections list`), so it stays out of .env.

Press Enter at that prompt to skip it; the deploy finishes with Slack events
disabled and you can authorize on a later deploy.
"""

from managed_deepagents import channels

channel = channels.slack()

# Available options (managed-deepagents 0.8.3), all optional:
#
#   channels.slack(
#       name="dvd-rental-analyst",        # display name in Slack, 1-35 characters
#       description="Answers DVD rental business questions",  # up to 139 characters
#       icon="icon.png",                  # 512x512 PNG under channels/, max 1 MB (generated if omitted)
#       background_color="#1F2937",       # app background, #RRGGBB
#       trigger_on_all_messages=False,    # True: every channel message starts a run, not just @mentions
#       allow_bot_triggers=False,         # True: let other bots trigger the agent
#   )
