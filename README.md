# fantasy-notifier
Bot that will notify you when a player in free agency for your Yahoo fantasy hockey league is doing exceptionally well. Support for other sports is pending.

Steps to use:

1. Install the required packages.

```
pip3 install -r requirements.txt
```

2. Create a .env file based off of .env.example.

3. Set up an app for the Yahoo Fantasy API: https://developer.yahoo.com/fantasysports/guide/
- Add the consumer key and consumer secret to your .env file.

4. Add the name of your Yahoo Fantasy league that you want notifications for to the .env file as well under `NAME_OF_LEAGUE_OF_INTEREST`.

5. If you don't already have one, you'll want to set up an AWS account.

6. Set up a DynamoDB table on your AWS account called `SentNotifications` with a partition key (primary key) named `player_id_and_date`. If you want different names for the table or partition key, make sure to change those in your .env file.

7. Create a Twilio account, project, and phone number. 
- Add the account SID, auth token, and phone number all to the .env file.

8. Finally, add the phone number you want text messages sent to as `USER_PHONE_NUMBER` and set a minimum point total that you would want notifications for under `EXCEPTIONAL_FANTASY_POINTS`, all in the .env file. For example, if you want a notification whenever a free agent player hits 10 fantasy points, then set that to 10.

9. [Set up a cron job](https://phoenixnap.com/kb/set-up-cron-job-linux) that runs run.py as frequently as you'd like to poll for if a player has hit the `EXCEPTIONAL_FANTASY_POINTS`. If you don't want to have to leave your computer running, you can also [set something up in the cloud](https://betterprogramming.pub/cron-job-patterns-in-aws-126fbf54a276).
