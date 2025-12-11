import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from veille_scraping import call_api_articles
from conversation_agent import ConversationAgent


class DiscordBot(discord.Client):
    def __init__(self, conversation_agent):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.conversation_agent = conversation_agent
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # --- Commande /ask ---
        @self.tree.command(name="ask", description="Pose une question à Jarvis")
        @app_commands.describe(question="Il est un peu enervé, fais attention à ce que tu racontes...")
        async def ask(interaction: discord.Interaction, question: str):
            await interaction.response.defer()
            try:
                response = self.conversation_agent.ask_llm(user_interaction=question)
                full_response = f"**Question :** {question}\n\n{response}"
                if len(full_response) > 2000:
                    full_response = full_response[:1990] + "..."
                await interaction.followup.send(full_response)
            except Exception as e:
                await interaction.followup.send(f"Une erreur est survenue : {e}")

        # --- Commande /ask_veille ---
        @self.tree.command(name="ask_veille", description="Lance une veille d'information")
        @app_commands.describe(
            sujet_veille="Le sujet ou les mots-clés de la veille",
            langue="Langue des articles (Sélectionner dans la liste)",
            jour="Nombre de jours à remonter",
            nombre_article="Nombre d'articles à récupérer"
        )
        @app_commands.choices(langue=[
            app_commands.Choice(name="Français", value="fr"),
            app_commands.Choice(name="English", value="en")
        ])
        async def ask_veille(
                interaction: discord.Interaction,
                sujet_veille: str,
                langue: app_commands.Choice[str],
                jour: int,
                nombre_article: int
        ):
            if jour < 1 or nombre_article < 1:
                await interaction.response.send_message(
                    "❌ Le nombre de jours et d'articles doit être supérieur à 0.", ephemeral=True
                )
                return

            await interaction.response.defer()
            try:
                response = call_api_articles(
                    sujet=sujet_veille,
                    langue=langue.value,
                    jour=jour,
                    nb_articles=nombre_article
                )
                header = (
                    f"## Veille lancée\n"
                    f"Sujet : {sujet_veille}\n"
                    f"Langue : {langue.name}\n"
                    f"Jours : {jour} | Articles : {nombre_article}\n"
                    f"-----------------------------------\n"
                )
                full_response = header + str(response)
                if len(full_response) > 2000:
                    full_response = full_response[:1990] + "..."
                await interaction.followup.send(full_response)
            except Exception as e:
                await interaction.followup.send(f"❌ Une erreur est survenue lors de la veille : {e}")

        # --- Commande /subscribe_newsletter ---
        @self.tree.command(name="subscribe_newsletter", description="S'abonner à la newsletter en indiquant son email")
        @app_commands.describe(email="Votre adresse email pour recevoir la newsletter")
        async def subscribe_newsletter(interaction: discord.Interaction, email: str):
            await interaction.response.defer(ephemeral=True)
            try:
                fichier_email = (""
                                 "")
                emails_existants = set()
                if os.path.exists(fichier_email):
                    with open(fichier_email, "r", encoding="utf-8") as f:
                        emails_existants = set(l.strip() for l in f.readlines())
                if email in emails_existants:
                    await interaction.followup.send("⚠️ Cette adresse est déjà inscrite à la newsletter.")
                    return
                with open(fichier_email, "a", encoding="utf-8") as f:
                    f.write(email + "\n")
                await interaction.followup.send(f"✅ Adresse {email} ajoutée à la newsletter !")
            except Exception as e:
                await interaction.followup.send(f"❌ Une erreur est survenue : {e}")

        await self.tree.sync()
        print("Commandes synchronisées (ask, ask_veille, subscribe_newsletter).")

    async def on_ready(self):
        print(f'Connecté en tant que {self.user} !')


# -----------------------------
# Lancement du bot
# -----------------------------
if __name__ == "__main__":
    load_dotenv()
    discord_token = os.getenv('DISCORD_TOKEN')

    if not discord_token:
        print("Erreur : Token manquant dans le .env")
    else:
        agent = ConversationAgent()
        bot = DiscordBot(conversation_agent=agent)
        bot.run(discord_token)
