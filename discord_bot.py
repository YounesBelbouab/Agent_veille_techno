import os
import discord
import json
import re
import datetime
import asyncio

from aiohttp import web
from discord import app_commands
from dotenv import load_dotenv
from bigquery_utils import insert_config_to_bigquery

from bigquery_utils import insert_config_to_bigquery
from agents.veille_scraping import call_api_articles
from agents.conversation_agent import ConversationAgent
from exec.batch_runner import run_batch
from exec.batch_runner import run_batch

MODEL_ID = "llama-3.3-70b-versatile"
TARGET_CHANNEL_ID = 1448667313921331252


class DiscordBot(discord.Client):
    def __init__(self, conversation_agent):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.conversation_agent = conversation_agent
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Connecte : {self.user}')

    async def send_long_message(self, interaction: discord.Interaction, content: str, use_followup=False):
        chunks = [content[i:i + 1990] for i in range(0, len(content), 1990)]
        if target_channel is None:
            print(f"Erreur : Impossible de trouver le salon {TARGET_CHANNEL_ID}")
            return

        for i, chunk in enumerate(chunks):
            if i == 0 and use_followup:
                await interaction.followup.send(chunk)
            elif use_followup:
                await interaction.channel.send(chunk)
            else:
                await interaction.channel.send(chunk)
        try:
            try:
                user_obj = await self.fetch_user(int(user_id))
                user_name = user_obj.name
            except:
                user_name = user_id

            date_str = datetime.datetime.now().strftime("%d/%m/%Y")

            thread = await target_channel.create_thread(
                name=f"Veille de {user_name} du {date_str}",
                type=discord.ChannelType.public_thread,
                auto_archive_duration=60
            )

            full_message = f"Hey <@{user_id}> voici ta veille du {date_str} ! \n\n{veille_user}"

            if len(full_message) <= 2000:
                await thread.send(full_message)
            else:
                chunks = [full_message[i:i+1900] for i in range(0, len(full_message), 1900)]
                for chunk in chunks:
                    await thread.send(chunk)

            print(f"Veille envoyée avec succès dans le thread '{thread.name}'")

        except Exception as e:
            print(f"Erreur critique lors de l'envoi de la veille : {e}")

    def validate_veille_params(self, jour: int, nombre_article: int):
        if jour > 30: return "Erreur Temporelle : Max 30 jours."
        if jour < 1: return "Erreur : Jours minimum 1."
        if nombre_article > 50: return "Surcharge : Max 50 articles."
        if nombre_article < 1: return "Erreur : Articles minimum 1."
        return None

    async def handle_ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        try:
            response = self.conversation_agent.ask_llm(user_interaction=question, model=MODEL_ID)
            full_response = f"**Question :** {question}\n\n{response}"
            await self.send_long_message(interaction, full_response, use_followup=True)
        except Exception as e:
            await interaction.followup.send(f"Erreur : {e}")

    async def handle_ask_veille(self, interaction: discord.Interaction, sujet: str, langue: str, jour: int,
                                nombre: int):
        error_msg = self.validate_veille_params(jour, nombre)
        if error_msg:
            await interaction.response.send_message(error_msg, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            await interaction.followup.send(f"Recherche : {sujet}...")

            articles_raw = call_api_articles(sujet=sujet, langue=langue, jour=jour, nb_articles=nombre)

            if isinstance(articles_raw, str):
                try:
                    articles_raw = json.loads(articles_raw)
                except json.JSONDecodeError:
                    await interaction.followup.send(f"Erreur format donnees : {articles_raw[:1000]}")
                    return

            if not isinstance(articles_raw, list) or not articles_raw:
                await interaction.followup.send("Aucun article trouve ou format invalide.")
                return

            for article in articles_raw:
                if not isinstance(article, dict): continue

                titre = article.get('title', 'Sans titre')
                url = article.get('url', 'N/A')
                contenu = article.get('content', article.get('summary', 'Pas de contenu'))

                prompt_agent = (
                    f"Tache : Analyse cet article et genere un rapport de veille complet.\n"
                    f"IMPORTANT : Redige la section RESUME explicitement.\n"
                    f"--- ARTICLE ---\n"
                    f"Titre : {titre}\nURL : {url}\nContenu : {contenu[:15000]}"
                )

                response = self.conversation_agent.ask_llm(user_interaction=prompt_agent, model=MODEL_ID)
                await self.send_long_message(interaction, response, use_followup=False)

            await interaction.channel.send("Veille terminee.")

        except Exception as e:
            await interaction.followup.send(f"Erreur critique : {str(e)}")

    async def handle_config_veille(self, interaction: discord.Interaction, email: str, sujet: str, langue: str,
                                   periode: int, nb_articles: int):
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            await interaction.response.send_message("Email invalide.", ephemeral=True)
            return

        if periode < 1 or nb_articles < 1:
            await interaction.response.send_message("Les valeurs doivent etre positives.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            user_data = {
                "id_discord": str(interaction.user.id),
                "email": email,
                "sujet": sujet,
                "langue": langue,
                "periode": periode,
                "nb_articles": nb_articles,
            }
            insert_config_to_bigquery(user_data)
            await interaction.followup.send(f"Config sauvegardee pour **{sujet}** ({langue}) -> `{email}`")
        except Exception as e:
            await interaction.followup.send(f"Erreur sauvegarde : {str(e)}")

    async def handle_automation(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send("Demarrage du Batch Automation...")
        try:
            await asyncio.to_thread(run_batch, self)
            await interaction.followup.send("Batch Automation termine.")
        except Exception as e:
            await interaction.followup.send(f"Erreur batch : {e}")
        @self.tree.command(name="run_veille_automation", description="Lancer manuellement le batch de veille")
        async def run_veille_automation(interaction: discord.Interaction):
            # 1. On dit à Discord de patienter (car le batch peut prendre 5 min)
            await interaction.response.defer()
            await interaction.followup.send("🚀 Démarrage du Batch Automation en cours...")

            try:
                await run_batch(bot_client=self)

                await interaction.followup.send("✅ Batch Automation terminé avec succès.")

            except Exception as e:
                # On envoie l'erreur s'il y en a une
                await interaction.followup.send(f"❌ Erreur critique batch : {e}")


    async def send_veille_discord(self, user_id, veille_user):
        target_channel = self.get_channel(TARGET_CHANNEL_ID)
        if not target_channel:
            print(f"Erreur channel {TARGET_CHANNEL_ID} introuvable")
            return

        try:
            date_str = datetime.datetime.now().strftime("%d/%m/%Y")
            thread = await target_channel.create_thread(
                name=f"Veille de {user_id} du {date_str}",
                type=discord.ChannelType.public_thread,
                auto_archive_duration=60
            )
            await thread.send(f"Hey <@{user_id}> voici ta veille du {date_str} ! \n\n{veille_user}")
            print(f"Veille envoyee pour {user_id}")
        except Exception as e:
            print(f"Erreur envoi thread : {e}")

    async def setup_hook(self):

        @self.tree.command(name="ask", description="Pose une question à Jarvis")
        async def ask(interaction: discord.Interaction, question: str):
            await self.handle_ask(interaction, question)

        @self.tree.command(name="ask_veille", description="Lance une veille d'information")
        @app_commands.choices(langue=[
            app_commands.Choice(name="Français", value="fr"),
            app_commands.Choice(name="English", value="en")
        ])
        async def ask_veille(interaction: discord.Interaction, sujet_veille: str, langue: app_commands.Choice[str],
                             jour: int, nombre_article: int):
            await self.handle_ask_veille(interaction, sujet_veille, langue.value, jour, nombre_article)

        @self.tree.command(name="config_veille", description="Configure tes préférences de veille auto")
        @app_commands.choices(langue=[
            app_commands.Choice(name="Français", value="fr"),
            app_commands.Choice(name="English", value="en")
        ])
        async def config_veille(interaction: discord.Interaction, email: str, sujet: str,
                                langue: app_commands.Choice[str], periode: int, nb_articles: int):
            await self.handle_config_veille(interaction, email, sujet, langue.value, periode, nb_articles)

        @self.tree.command(name="run_veille_automation", description="Lancer manuellement le batch de veille")
        async def run_veille_automation(interaction: discord.Interaction):
            await self.handle_automation(interaction)

        await self.tree.sync()
        print("Commandes synchronisees.")
        self.loop.create_task(self.start_web_server())

    async def trigger_cron_handler(self, request):
            print("Cron activé! Lancement du batch...")
            asyncio.create_task(run_batch(bot_client=self))
            return web.Response(text="Batch démarré avec succès !")

    async def start_web_server(self):
        app = web.Application()
        app.router.add_get('/trigger_veille', self.trigger_cron_handler)

        runner = web.AppRunner(app)
        await runner.setup()

        port = int(os.environ.get("PORT", 8080))

        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"Serveur Web de veille démarré sur le port {port}")

    async def on_ready(self):
        print(f'Connecte : {self.user}')


if __name__ == "__main__":
    load_dotenv()
    discord_token = os.getenv('DISCORD_TOKEN')

    if not discord_token:
        print("Erreur : DISCORD_TOKEN manquant")
    else:
        agent = ConversationAgent()
        bot = DiscordBot(conversation_agent=agent)
        bot.run(discord_token)