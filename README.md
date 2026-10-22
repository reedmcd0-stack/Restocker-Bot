# Restocker bot
Restocker Bot

A Discord bot for publishing restock announcements and managing a service stock panel.

Features

- "/publish" — Publish a restock announcement for a selected service and quantity.
- "/generator" — Publish the interactive stock panel.
- "/stock" — View current stock counts.
- "/remove-restock" — Remove entries from a service's stock.
- Interactive service buttons and automatic panel refresh.
- Role-based access control and a 60-second cooldown.
- Stock management using local text files.

Supported Services

Paramount+, Disney+, Crunchyroll, Steam, Netflix, Supercell, Eldorado, Epic Games, PlayStation, Roblox, Deezer, Hotmail, Spotify, Prime Video, CapCut, ExpressVPN, HIDIVE, DAZN, TunnelBear and Hulu.

Requirements

- Python 3.10 or newer
- "discord.py" with support for the UI components used by the project
- A Discord application and bot token

Installation

Clone the repository:

git clone https://github.com/reedmcd0-stack/Restocker-Bot.git
cd Restocker-Bot

Install the dependencies once "requirements.txt" is available:

pip install -r requirements.txt

Configuration

Set the bot token as an environment variable:

DISCORD_TOKEN=your_discord_bot_token

Configure "DISCORD_TOKEN" in your hosting platform's environment variables. Never publish your bot token or commit it to GitHub.

Review the role IDs, banner URLs and permissions in the command modules before deployment.

Stock Management

Stock files are stored in:

generator_data/
├── panel.json
└── stock/

Each service uses a numbered ".txt" file. Each non-empty line represents one test record.

Important: Use only fictional test records or data you are authorized to manage. Never upload real passwords or private account credentials.

Hosting

The bot can run on a Python-compatible hosting platform that supports persistent processes.

Configure the environment variables and startup command required by your project. If your hosting platform uses temporary storage, stock files may be lost after a restart or redeployment.

Security

- Keep your Discord bot token private.
- Grant the bot only the permissions it needs.
- Restrict administrative commands to authorized members.
- Back up stock data if persistent storage is required.
- Review and test changes before deploying.

License

No license has been specified yet.

Adding a New Service

Adding a new service is simple. You only need to add "Example", to the service list in all four files:

- "generator.py"
- "restock.py"
- "publish.py"
- "remove-restock.py"

Example

Add the service name to the existing list:

"Example",

Replace ""Example"" with the name of your service.

Important:

- Use the exact same service name in all four files.
- Keep the same spelling and capitalization.
- Follow the existing list format and keep the commas correct.
- Restart the bot after making your changes.

That's it! The new service will be included wherever the service list is used by the bot.