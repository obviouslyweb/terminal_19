## Overview

**Project Title**: TERMINAL_19

**Project Description**: A music bot created using Discord.py that allows users to upload their own audio tracks to listen to in voice channels, with support for a variety of audio filetypes, playlist features, looping tracks, and (theoretically) support for an infinite amount of tracks to be played.

**Project Goals**: To understand how a pre-existing platform API (like Discord) functions and create a custom application that can interface with it to provide extended and customized functionality, as well as understand community-created libraries (Discord.py & ffmpeg) to achieve said functionality.

## Instructions for Build and Use

**IMPORTANT:** TERMINAL_19 is meant to be a private audio bot that you can load tracks into and play audio with in smaller, friends-focused Discord servers. Therefore, these steps encompass the process of creating your own version of the bot from scratch. **You must host the bot yourself.** There is no invite link to a version of the bot that is publicly hosted, as I don't want to be liable for whatever you do with this bot. Proceeding to use the code I've provided here for this application means that you agree to follow Discord's Terms of Service and that I am NOT LIABLE for anything that happens as a result of this application.

To create your own bot using TERMINAL_19 as a base, follow the given instructions:

1. Download [ffmpeg](https://ffmpeg.org/download.html) and add it to your PATH. You can download pre-compiled versions from other users or compile it yourself (although doing so is a complicated process).
2. Download and install [Python](https://www.python.org/downloads/), as well as add it to PATH. Versions 3.9 to 3.12 are confirmed to work well, but 3.13 and above may have slight compatibility issues with Discord.py, so you may encounter issues with that route.
3. Download the contents of this repository to your computer and store in a safe location (optimally somewhere easy to access).
4. Log into the [Discord Developer Portal](https://discord.com/developers/applications) using your Discord account. Create a new application and give it a name. On the *Bot* page, toggle "Server Members Intent" and "Message Content Intent"; these are required for the bot to be able to properly process user information and messages to read messages.
5. In the main `terminal_19` folder, create a new file called `.env`. This will contain important details that our bot needs to run. Type `DISCORD_TOKEN=` in the first and only line in the file. Back in the Discord Developer Portal *Bot* page, there should be a button named "Reset Token"; click it and obtain your bot's token, and paste it back in the `.env` file after `DISCORD_TOKEN=`. Then, save the file.
**WARNING: DO NOT SHARE YOUR BOT TOKEN WITH ANYONE!**  If it's stolen, others can log in as this bot with custom functionality NOT in your code.
6. Return to your application on the Discord Developer Portal and go to the OAuth2 tab. Scroll down to *OAuth2 URL Generator*. This is where you'll create the invite link that you will use to invite the bot into your server. Toggle "bot", "applications.commands", and then under Bot Permissions, "View Channels", "Send Messages", "Send Messages in Threads", "Manage Messages", "Read Message History", "Add Reactions", "Connect", "Speak", and "Use Voice Activity". Then, under Integration Type, choose "Guild Install". Copy the Generated URL and store it so you can use it to reinvite the bot going forward.
7. Open the link with your Discord account, and select the server(s) you want to add it to. Once added, it will appear offline; this is because we've yet to turn the bot on.

Instructions for turning on / disabling the bot:

1. Using Command Prompt, Terminal, or an equivalent program, navigate to the `terminal_19` folder using `cd`.
2. Type `python main.py` to turn the bot on. After a few seconds, the bot should load and display a message, "Logged in as (bot name)#1234 (ID: ####)". Once you see this message, the bot will start accepting commands.
3. In Discord, use !help on any channel the bot is in to see the bot's available commands.
4. To turn off the bot, use `CTRL + C` on the window you used to enable the bot. This will take it offline until you turn it back on.

Instructions for adding audio to the bot:

1. Find a compatible audio file ()

## Development Environment 

To recreate the development environment, you need the following software and/or libraries with the specified versions:

* [Visual Studio Code](https://code.visualstudio.com/)
* [Python 3.11.5](https://www.python.org/downloads/)
* [discord.py 2.3.2](https://discordpy.readthedocs.io/en/stable/)
* [ffmpeg](https://ffmpeg.org/)
* dotenv (`python-dotenv`)

## Useful Websites to Learn More

I found these websites useful in developing this software:

* [discord.py](https://discordpy.readthedocs.io/en/stable/)'s documentation on the Python libraries used to create this application
* 
* 

## Future Work

The following items I plan to fix, improve, and/or add to this project in the future:

* [ ] Additional playback features (show current timestamp of playing song in !queue, keep playlist mode, etc.)
* [ ] Integrate functionality with Discord slash commands (the ability to use /play instead of !play).
* [ ] Include integration with YouTube or Soundcloud APIs for streaming music from online sources

## Legal Disclaimer

This project is provided “as is” without warranty of any kind. By using this code, you agree that you are solely responsible for compliance with Discord’s Terms of Service and all applicable laws. I accept no liability for misuse or damages.