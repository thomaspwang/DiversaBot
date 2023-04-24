# DiversaBot
Management bot for DiversaTech

Features currently supported
- Parses messages in #diversaspotting and stores them in a Google Sheet. Requires the spotter to mention all the people (could be multiple) they spotted, along with an image file.
- typing "diversabot leaderboard" prompts the bot to display the top 10 spotters
- typing "diversabot miss <@user>" will prompt the bot to display a random image of the specified user
- typing "diversabot stats" prompts the bot to display which position you're currently in as well as nearby members by rank. Moreover, it will also display how many times you've been spotted, and which member has spotted you the most
- replying "diversabot flag" to a diversaspot will flag the spot hearby negating it in any points calculation
- typing "diversabot help" will display all commands
- typing "diversabot rules" will display the diversapotting official rules and regulation


Features to Implement
- "diversabot leaderboard" displaying project team rankings

TO-DOs
- make the code not so shit
- migrate from sheets to mongodb since slack deletes messages
