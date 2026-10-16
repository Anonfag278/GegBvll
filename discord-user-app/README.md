# Discord user-installed message app

Python 3.10+ and one dependency: discord.py. Uses an application **bot token**, with slash commands installed to your account. No user tokens, self-botting, server bot invitations, web server, or public endpoint needed. Keep the Python process running to receive commands over Discord's Gateway.

## Upload to GitHub

1. Extract the GitHub export ZIP and open the `discord-user-app` folder.
2. On GitHub, create a new repository, for example `discord-user-app`. Choose Public or Private. Leave the options to add a README, license, and .gitignore unchecked: this package already includes a README and .gitignore. No license is selected for you.
3. On the empty repository page, select **uploading an existing file**. Upload `app.py`, `requirements.txt`, `README.md`, `.gitignore`, and the `tests` folder from inside the extracted folder. Commit the files. Upload the contents, rather than the enclosing folder or the ZIP itself, so `app.py` appears at the repository root.
4. Share the repository link for the source code. Share the Discord installation link for friends who just want to use the running app.

The export excludes virtual environments, Python caches, and credentials. GitHub's browser uploader does not apply `.gitignore`, so upload only the exported source files. Never upload a bot token or paste it into README, issues, or commits. If one was published, reset it in the Discord Developer Portal; deleting a file does not remove its Git history.

Uploading code to GitHub does not keep the app running. Continue running it on your computer or a host. Friends using your app do not need to run the source themselves.

## Developer Portal

1. Open https://discord.com/developers/applications and create an application.
2. On **Bot**, create/reset and copy the bot token. Keep it private. Leave all privileged Gateway intents off.
3. On **Installation**, enable **User Install**. You can disable **Guild Install** for this app.
4. Select **Discord Provided Link**. Under **Default Install Settings → User Install**, select only **applications.commands** and save.
5. Copy the install link and open it. Choose **Add to My Apps**, then authorize with your Discord account. No server invitation or `bot` scope is needed.
6. Leave **General Information → Interactions Endpoint URL** empty: this program receives interactions through the Gateway.
7. Share the **Installation → Install Link** with friends. They choose **Add to My Apps**. Anyone who installs the app can use its commands; no owner ID is required. Keep the bot token private: friends only need the install link, not the code or token. Keep **Requires OAuth2 Code Grant** off for this simple installation flow.

## Run (Windows PowerShell)

Open a terminal in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$secret = Read-Host 'Paste the application bot token' -AsSecureString
$env:DISCORD_BOT_TOKEN = [System.Net.NetworkCredential]::new('', $secret).Password
.\.venv\Scripts\python.exe app.py
```

Enter the token only at the hidden prompt, not in the commands. This works in Windows PowerShell 5.1 and PowerShell 7.

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
read -rs -p 'Bot token: ' DISCORD_BOT_TOKEN; echo
export DISCORD_BOT_TOKEN
.venv/bin/python app.py
```

Wait for `Slash commands synced` and `Connected as ...`. Commands register globally on startup; Discord may take time to display them. Run one instance of the program. Environment variables must be set again in a new terminal; `.env` files are not loaded. Stop the program with Ctrl+C.

## Commands

- `/repeat message:Hello! count:3` sends three public app messages in the channel where invoked. Text length: 1–2000 characters; count: 1–5. Mentions display without pinging users, roles, or everyone.
- `/stop` requests that your active run stop, including a run in another channel. Each user can have one active run and can stop only their own run. It cannot undo delivered messages. A send already in progress, including a discord.py rate-limit wait, may still complete before the loop stops.

Both commands are enabled in server channels, DMs with the app, DMs with other users, and group DMs, wherever Discord permits user-installed commands.

The initial status and final sent count are private to you. Repeated messages are sent as the app, attributed to the interaction, rather than as your normal account. Short runs may finish before you can invoke `/stop`.

## Limits and troubleshooting

User-installed apps without a server installation are limited to **five follow-up messages per interaction**. This app reserves all five for your text and edits its initial private response for status. It does not chain interactions to bypass this cap.

Sends are sequential with no artificial delay. discord.py handles Discord's rate limits and waits as required; there is no guaranteed messages-per-second rate. A Discord API error stops the run. No custom retry loop is used because an ambiguous failure could otherwise duplicate a delivered message. Use only in channels where repeated messages are welcome.

Server/channel permissions, including **Use Application Commands** and **Use External Apps**, and Discord's own restrictions still apply. If public external-app responses are disabled, Discord can make responses private or reject them; this app cannot override that. Check the selected channel, installation context, and server permissions if commands are missing or messages aren't public. Do not invite a server bot just to run this app.

Official references:

- [Discord user-install setup](https://github.com/discord/discord-api-docs/blob/main/developers/tutorials/developing-a-user-installable-app.mdx)
- [Interaction follow-up limits](https://github.com/discord/discord-api-docs/blob/main/developers/interactions/receiving-and-responding.mdx)
- [discord.py interactions and command API](https://discordpy.readthedocs.io/en/stable/interactions/api.html)

Live verification requires your own app credentials and a permitted Discord channel. Offline tests: `python -m unittest discover -s tests -v`.
